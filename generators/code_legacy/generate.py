#!/usr/bin/env python
"""Legacy half of Corvane's monorepo: the CLARA sources (COBOL, copybooks, JCL, BMS, DDL, docs).

Writes FINAL-state files (variant a/b content) under build/code_src/legacy/<repo path>, the
CM-09 versions of changed files under build/code_src/legacy_c/<repo path>, the history metadata
build/code_src/legacy/history.yaml (read by generators/code_repo/assemble.py), the facts manifest
manifests/code_legacy.facts.yaml and check trees build/code_check_legacy/variant_{a,b,c}.

    .venv/bin/python -I generators/code_legacy/generate.py [--no-check-trees]

Exit status is non-zero if any self-check fails (SQL tables / CALLs / COPYs vs programs.yaml,
line widths, history replay, needles at their locators, forbidden strings, denylist words).
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import argparse
import hashlib
import os
import re
import shutil

import yaml

from generators.common import util
from world.worldlib import load_world

from generators.code_legacy import archive, assets, cobol, commits, docs
from generators.code_legacy.srcmodel import hunks

OUT = ROOT / "build" / "code_src" / "legacy"
OUT_C = ROOT / "build" / "code_src" / "legacy_c"
CHECK = ROOT / "build" / "code_check_legacy"
MANIFEST = "code_legacy"
LEG = "legacy/clara"
ANCHOR_DATE = "2026-11-06"


# ---------------------------------------------------------------------------------------------
# file registry
# ---------------------------------------------------------------------------------------------
class F:
    def __init__(self, path, src, variants=("a", "b", "c"), created_by="CM-01", renamed_from=None,
                 facts=(), file_id=None, kind="other"):
        self.path = path
        self.src = src
        self.variants = list(variants)
        self.created_by = created_by
        self.renamed_from = renamed_from          # (commit, old_path)
        self.facts = list(facts)
        self.file_id = file_id or f"CODE:a:{path}"
        self.kind = kind


def build_ctx(W, cs):
    ctx = {"job_step": {}, "commit_date": {c["id"]: c["date"] for c in cs},
           "created_by": {"CLRRS210": "XC-04", "CLRFR060": "CM-05", "CLRFR120": "CM-05", "CLRFR090": "XC-07"},
           "create_ref": {"CLRRS210": "CHUB-241", "CLRFR060": "CHUB-206", "CLRFR120": "CHUB-206",
                          "CLRFR090": "CHUB-208"},
           "late": {}, "maint_extra": {}}
    for j in W.jcl_jobs.values():
        for st in j["steps"]:
            ctx["job_step"][st["program"]] = st["step"]
    for pid in ("CLRFR010", "CLRFR100", "CLRFR110", "CLRFR140"):
        ctx["late"][pid] = {"tables": {"CLR.T_FRAUD_NOTIFICATION": "CM-05"}, "cpys": {"FRDNOT01": "CM-05"}}
        ctx["maint_extra"][pid] = [("2026-03-27", "KBARR01", "CHUB-206",
                                    "READS CLR.T_FRAUD_NOTIFICATION (NISA CIRCULAR 2026/04)", "CM-05", None)]
    me = ctx["maint_extra"]
    me["CLRFR020"] = [("2025-03-01", "PASHW01", "", "RENAMED FROM FNETCAL1 (FRAUDNET RENAMED SENTINEL)", "XC-01", None),
                      ("2025-03-03", "PASHW01", "CHUB-119", "SCORE HOST SWITCHED TO SENTINEL.CORVANE.INTERNAL "
                                                            "(INC-2025-0233)", "CM-02", None)]
    me["CLRFR030"] = [("2025-03-01", "PASHW01", "", "RENAMED FROM FNETREF1 (FRAUDNET RENAMED SENTINEL)", "XC-01", None)]
    me["CLRRS170"] = [("2025-04-30", "KBARR01", "CHUB-142", "RM-REC-VERSION SET TO 02 (INC-2025-0412)", "CM-03", None)]
    me.setdefault("CLRFR140", []).append(("2026-03-31", "PASHW01", "CHUB-207",
                                          "DISABLED - BR-FRD-019 WITHDRAWN; JOB CLRNFR99 OFF THE SCHEDULE", "XC-06", None))
    me["CLRRS210"] = [("2026-08-28", "KBARR01", "CHUB-241", "RETIRED - PARALLEL RUN ENDED 2026-08-28", "XC-09", None)]
    me["CLRFR040"] = [("2026-11-12", "KBARR01", "CHUB-298", "THRESHOLDS FROM CLR.T_PARAM VIA CLRCM040; HARD-CODED "
                                                            "070 REMOVED", "CM-09", None)]
    return ctx


def build_files(W, cs):
    ctx = build_ctx(W, cs)
    files: list[F] = []
    prog_stats = {}
    for pid in W.programs:
        g = cobol.ProgramGen(W, pid, ctx)
        src = g.build()
        rn = None
        rf = W.programs[pid].get("renamed_from")
        if rf and rf["date"] >= "2025-02-21":
            rn = ("XC-01", f"{LEG}/cobol/{rf['old_id']}.cbl")
        files.append(F(f"{LEG}/cobol/{pid}.cbl", src, created_by=ctx["created_by"].get(pid, "CM-01"),
                       renamed_from=rn, facts=g.facts, kind="cobol"))
        prog_stats[pid] = {"target": g.target, "n_fill": g.n_fill}
    for name in W.copybooks:
        s, fx = assets.copybook(W, name)
        files.append(F(f"{LEG}/copybooks/{name}.cpy", s, created_by="CM-05" if name == "FRDNOT01" else "CM-01",
                       facts=fx, kind="copybook"))
    for job in W.jcl_jobs:
        fid = f"CODE:a:{LEG}/jcl/{job}.jcl"
        s, fx = assets.jcl(W, job, fid)
        files.append(F(f"{LEG}/jcl/{job}.jcl", s, created_by=assets.JCL_CREATED.get(job, "CM-01"), facts=fx, kind="jcl"))
    for ms in sorted({m["mapset"] for m in W.bms_maps.values()}):
        s, fx = assets.mapset(W, ms)
        files.append(F(f"{LEG}/bms/{ms}.bms", s, facts=fx, kind="bms"))
    for t in W.tables:
        if not t.startswith("CLR."):
            continue
        short = t.split(".")[1]
        fid = f"CODE:a:{LEG}/ddl/{short}.sql"
        s, fx = assets.ddl(W, t, fid)
        files.append(F(f"{LEG}/ddl/{short}.sql", s, created_by=assets.DDL_CREATED.get(t, "CM-01"), facts=fx, kind="ddl"))
    s, fx = assets.param_seed(W, f"CODE:a:{LEG}/ddl/T_PARAM_seed.sql")
    files.append(F(f"{LEG}/ddl/T_PARAM_seed.sql", s, facts=fx, kind="ddl"))
    s, fx = docs.readme(W)
    files.append(F(f"{LEG}/README.md", s, facts=fx, kind="doc"))
    for fname, fn in (("program-inventory.md", docs.program_inventory), ("batch-jobs.md", docs.batch_jobs),
                      ("db2-objects.md", docs.db2_objects)):
        p = f"{LEG}/docs/{fname}"
        s, fx = fn(W, f"CODE:a:{p}")
        files.append(F(p, s, created_by="XC-11", facts=fx, kind="doc"))
    s, fx = docs.coding_standards(W)
    files.append(F(f"{LEG}/docs/coding-standards.md", s, created_by="XC-11", facts=fx, kind="doc"))
    # ---- variant b only
    for name, retired, title, kind in archive.ARCHIVE:
        s, fx = archive.archived_program(name, retired, title, kind)
        files.append(F(f"{LEG}/cobol-archive/{name}.cbl", s, variants=["b"], facts=fx, kind="archive",
                       file_id=f"CODE:b:{LEG}/cobol-archive/{name}.cbl"))
    files.append(F(f"{LEG}/cobol-archive/README.md", archive.archive_readme(), variants=["b"], kind="archive"))
    files.append(F(f"{LEG}/testdata/README.md", archive.testdata_readme(), variants=["b"], kind="testdata"))
    for t in W.tables:
        if t.startswith("CLR.") and t != "CLR.T_PARAM":
            files.append(F(f"{LEG}/testdata/db2/{t.split('.')[1]}.csv", archive.fixture_csv(W, t), variants=["b"],
                           kind="testdata"))
    for n in ("RSVMOVE", "SENTREQ1", "SENTRSP1"):
        files.append(F(f"{LEG}/testdata/interfaces/{n}_sample.txt", archive.interface_sample(n), variants=["b"],
                       kind="testdata"))
    exp_pids = ["CLRRS110", "CLRRS130", "CLRRS150", "CLRRS170", "CLRST040", "CLRRC050", "CLRGL090", "CLRFR040",
                "CLRFR060", "CLRTR020"]
    for pid in exp_pids:
        files.append(F(f"{LEG}/testdata/expected/{pid}_report.txt", archive.expected_report(W, pid), variants=["b"],
                       kind="testdata"))
        files.append(F(f"{LEG}/testdata/jcl/T{pid[3:]}.jcl", archive.test_jcl(W, pid), variants=["b"], kind="testdata"))
    return files, prog_stats


# ---------------------------------------------------------------------------------------------
# rendering, history
# ---------------------------------------------------------------------------------------------

def states(order):
    """commit id -> frozenset of commits applied up to and including it."""
    out, acc = {}, []
    for c in order:
        acc.append(c)
        out[c] = frozenset(acc)
    return out


def history_entry(f: F, order, st, cinfo):
    tags = f.src.commits()
    created_ix = order.index(f.created_by)
    for t in tags:
        if order.index(t) <= created_ix:
            raise RuntimeError(f"{f.path}: tag {t} not after creation {f.created_by}")
    mods = []
    seq = sorted(set(tags) | ({f.renamed_from[0]} if f.renamed_from else set()), key=order.index)
    prev = st[f.created_by]
    for cid in seq:
        cur = st[cid]
        before, _ = f.src.render(prev)
        after, _ = f.src.render(cur)
        mv = [v for v in f.variants if v in cinfo[cid]["variants"]]
        for b, a in hunks(before, after):
            mods.append({"commit": cid, "variants": mv, "before": b, "after": a})
        prev = cur
    e = {"path": f.path, "variants": f.variants, "created_by": f.created_by}
    if f.renamed_from:
        e["renamed_from"] = {"commit": f.renamed_from[0], "path": f.renamed_from[1]}
    e["modifications"] = mods
    return e


def verify_replay(f: F, entry, order, st, a_final, c_final):
    """Undo modifications from the final content and compare with every rendered state."""
    for variant, final in (("a", a_final), ("c", c_final)):
        if variant == "a" and "a" not in f.variants and "b" not in f.variants:
            continue
        if variant == "c" and "c" not in f.variants:
            continue
        content = final
        applied = [m for m in entry["modifications"] if variant in m["variants"] or
                   (variant == "a" and "b" in m["variants"])]
        commits_in = sorted({m["commit"] for m in applied}, key=order.index, reverse=True)
        for cid in commits_in:
            for m in [m for m in applied if m["commit"] == cid]:
                if content.count(m["after"]) != 1:
                    raise RuntimeError(f"{f.path}: 'after' of {cid} occurs {content.count(m['after'])}x")
                content = content.replace(m["after"], m["before"])
            # state just before cid
            ix = order.index(cid)
            prev_state = st[order[ix - 1]] if ix > 0 else frozenset()
            keep = prev_state | ({"CM-09"} if False else set())
            if variant == "a":
                keep = frozenset(k for k in keep if k != "CM-09")
            exp, _ = f.src.render(keep)
            if exp != content:
                raise RuntimeError(f"{f.path}: replay mismatch before {cid} (variant {variant})")
        exp0, _ = f.src.render(st[f.created_by])
        if content != exp0:
            raise RuntimeError(f"{f.path}: replay mismatch at creation (variant {variant})")


HIST_HEADER = """\
# history.yaml - commit history of the legacy/ files (written by generators/code_legacy/generate.py)
#
# FORMAT (for generators/code_repo/assemble.py)
#   This file is metadata: never copy it into a repo. Content roots:
#     source_root   build/code_src/legacy     final content of every file for variants a and b
#     override_root build/code_src/legacy_c   final content for variant c of files CM-09 changes
#   commits: every commit that touches legacy/ files, oldest first.
#     id, date, author (person id), author_name, author_email, message, variants, tickets
#     world: true  -> a corpus_plan commit (CM-xx); create it with exactly this message/author/date.
#     world: false -> a legacy-only source sync (XC-xx) implied by the world model (tickets, renames,
#                     parameter rows, new programs). Create it as its own commit at its date (merge it
#                     with your own commit list by date). If you cannot, fold its changes into the commit
#                     named in fold_into (the next variant-a world commit on or after its date, else the
#                     last one before it).
#   files: one entry per file
#     path        repo path (also the path under source_root / override_root)
#     variants    which repos contain the file; [b] = variant-b-only file (canaries live there)
#     created_by  commit that adds the file
#     renamed_from (optional) {commit, path}: the file was added at created_by under `path` and
#                 git-mv'ed to `path` (the entry's path) by `commit` (apply that commit's
#                 modifications after the move)
#     modifications  [{commit, variants, before, after}] oldest first. `before`/`after` are exact
#                 whole-line snippets (each ends with a newline); `after` occurs exactly once in the
#                 file version produced by `commit`, `before` exactly once in the version before it.
#   To materialise the version of a file at commit K for variant V: start from the final content
#   (override_root for V = c when the file exists there, otherwise source_root), then for each
#   commit after K, newest first, whose modification lists V: replace `after` with `before`.
#   Equivalently, build forward: content at created_by = final content with every modification
#   undone; then apply each commit's after-for-before replacements in order.
#   CM-09 modifications list only variant c; variants a and b never see them.
#   Every replay above is verified by the generator before this file is written.
"""


class _Dumper(yaml.SafeDumper):
    pass


def _str_rep(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str_rep)
_Dumper.ignore_aliases = lambda self, data: True


# ---------------------------------------------------------------------------------------------
# self-checks
# ---------------------------------------------------------------------------------------------
SQL_W = [re.compile(r"\bINSERT\s+INTO\s+(CLR\.\w+)"), re.compile(r"\bUPDATE\s+(CLR\.\w+)"),
         re.compile(r"\bDELETE\s+FROM\s+(CLR\.\w+)")]
SQL_R = [re.compile(r"\bFROM\s+(CLR\.\w+)"), re.compile(r"\bJOIN\s+(CLR\.\w+)")]


def code_lines(text):
    out = []
    for ln in text.splitlines():
        body = ln[6:72] if len(ln) > 6 else ""
        if body[:1] in ("*", "/"):
            continue
        out.append(body[1:])
    return out


def analyse_cobol(text):
    lines = code_lines(text)
    joined = "\n".join(lines)
    reads, writes = set(), set()
    for blk in re.findall(r"EXEC\s+SQL(.*?)END-EXEC", joined, flags=re.S):
        b = " ".join(blk.split())
        for rx in SQL_W:
            writes.update(rx.findall(b))
        b2 = re.sub(r"\bDELETE\s+FROM\s+CLR\.\w+", " ", b)
        for rx in SQL_R:
            reads.update(rx.findall(b2))
    calls = set(re.findall(r"\bCALL\s+'([A-Z0-9]+)'", joined))
    copies = set(re.findall(r"^\s*COPY\s+([A-Z0-9]+)\s*\.", joined, flags=re.M))
    links = re.findall(r"EXEC\s+CICS\s+(?:LINK|XCTL)", joined)
    return reads, writes, calls, copies, links


FORBIDDEN = ["CICSPRD1", "CICSPRD2", "CLRPLAN1", "LEGACY_SKADE_REF", "MAXDEPTH", "02:15", "CLR-2025-02",
             "@corvane/", "@kbarraclough", "'3.1'", "RSV_BI_INDEX_PCT', '", "45 seconds", "05:40", "recon.daily_diff",
             "CLM-SE-2026-004417", "2027-01-23", "cdw-ro-02", "200Gi", "notification.fraud-notice",
             "Context Studio", "knowledge graph", "LLM", "RAG ", "Endevor", "Control-M"]
FORBIDDEN_RE = [re.compile(r"\bDB2P\b"), re.compile(r"\bAUC\b"), re.compile(r"velocity", re.I)]


def check_all(W, files, renders, errors, prog_stats):
    order_ok = True
    # 1) programs vs programs.yaml
    for f in files:
        if f.kind != "cobol":
            continue
        pid = pathlib.Path(f.path).stem
        p = W.programs[pid]
        for variant in ("a", "c"):
            text = renders[f.path][variant]
            reads, writes, calls, copies, links = analyse_cobol(text)
            exp_calls = set(p["calls_programs"]) | ({"CLRCM040"} if variant == "c" and pid == "CLRFR040" else set())
            exp_cpy = set(p["copybooks"]) | ({"PARMREC1"} if variant == "c" and pid == "CLRFR040" else set())
            if reads != set(p["reads_tables"]):
                errors.append(f"{pid}/{variant}: reads {sorted(reads)} != {sorted(p['reads_tables'])}")
            if writes != set(p["writes_tables"]):
                errors.append(f"{pid}/{variant}: writes {sorted(writes)} != {sorted(p['writes_tables'])}")
            if calls != exp_calls:
                errors.append(f"{pid}/{variant}: calls {sorted(calls)} != {sorted(exp_calls)}")
            if copies != exp_cpy:
                errors.append(f"{pid}/{variant}: copies {sorted(copies)} != {sorted(exp_cpy)}")
            if links:
                errors.append(f"{pid}/{variant}: EXEC CICS LINK/XCTL found")
        n = len(renders[f.path]["a"].splitlines())
        if not 150 <= n <= 900:
            errors.append(f"{pid}: {n} lines (want 150-900)")
        prog_stats[pid]["lines"] = n
    # 2) fixed-format widths and sequence numbers
    for f in files:
        if f.kind in ("cobol", "copybook", "archive") and f.path.endswith((".cbl", ".cpy")):
            for v in ("a", "c"):
                for i, ln in enumerate(renders[f.path][v].splitlines(), 1):
                    if len(ln) > 80 or (len(ln) > 72 and not ln[72:].strip().isalnum()):
                        errors.append(f"{f.path}:{i}: line too long")
                    if not ln[:6].isdigit():
                        errors.append(f"{f.path}:{i}: no sequence number")
        if f.kind == "jcl":
            for i, ln in enumerate(renders[f.path]["a"].splitlines(), 1):
                if len(ln) > 72:
                    errors.append(f"{f.path}:{i}: JCL line > 72")
        if f.kind == "bms":
            for i, ln in enumerate(renders[f.path]["a"].splitlines(), 1):
                if len(ln) > 72:
                    errors.append(f"{f.path}:{i}: BMS line > 72")
    # 3) forbidden strings / denylist
    deny = []
    for e in W.denylist if isinstance(W.denylist, list) else W.denylist.get("entries", []):
        nm = e["name"] if isinstance(e, dict) else e
        if nm in ("Corvane", "Brackenfield Loss Adjusting", "Programme Skerry") or "/" in nm:
            continue
        deny.append(re.compile(r"(?<![A-Za-z0-9])" + re.escape(nm) + r"(?![A-Za-z0-9])", re.I))
    for f in files:
        for v in ("a", "c"):
            text = renders[f.path][v]
            for s in FORBIDDEN:
                if s in text:
                    errors.append(f"{f.path}/{v}: forbidden string {s!r}")
            for rx in FORBIDDEN_RE:
                if rx.search(text) and not (rx.pattern == "velocity" and f.path.endswith("CLRFR990.cbl")):
                    errors.append(f"{f.path}/{v}: forbidden pattern {rx.pattern!r}")
            for rx in deny:
                m = rx.search(text)
                if m:
                    errors.append(f"{f.path}/{v}: denylisted name {m.group(0)!r}")
    # 4) exclusivity guards on what the generator states
    for pid in W.programs:
        fid = f"CODE:a:{LEG}/cobol/{pid}.cbl"
        for fld in ("description", "reads_tables", "writes_tables", "calls_programs", "copybooks", "cics_transaction",
                    "bms_map", "jcl_job", "since", "renamed_from", "notes", "status", "owner_person"):
            if not W.may_state(fid, f"PROGRAM:{pid}", fld):
                errors.append(f"{pid}: may_state false for {fld}")
    for cp in W.copybooks:
        if not W.may_state(f"CODE:a:{LEG}/copybooks/{cp}.cpy", f"COPYBOOK:{cp}", "fields"):
            errors.append(f"{cp}: may_state false for fields")
    for m in W.bms_maps:
        if not W.may_state(f"CODE:a:{LEG}/bms/x.bms", f"BMS:{m}", "fields"):
            errors.append(f"{m}: may_state false for fields")
    for t in W.tables:
        if t.startswith("CLR."):
            fid = f"CODE:a:{LEG}/ddl/{t.split('.')[1]}.sql"
            for fld in ("columns", "description", "primary_key", "foreign_keys"):
                if not W.may_state(fid, f"TABLE:{t}", fld):
                    errors.append(f"{t}: may_state false for {fld}")
    for iid, fld in (("CLX-IF-042", "format"), ("CLX-IF-042", "programs"), ("CLX-IF-011", "format"),
                     ("CLX-IF-031", "format"), ("JCL:CLRNRSV3", "datasets"), ("JCL:CLRNRSV3", "restart")):
        ref = iid if ":" in iid else f"INTERFACE:{iid}"
        if not W.may_state(f"CODE:a:{LEG}/cobol/CLRRS170.cbl", ref, fld):
            errors.append(f"{ref}: may_state false for {fld}")


# ---------------------------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------------------------

def fid_prefix(path):
    stem = pathlib.Path(path).stem
    parent = pathlib.Path(path).parent.name
    base = stem if parent in ("cobol", "copybooks", "jcl", "bms", "ddl", "cobol-archive") else f"{parent}-{stem}"
    return "CL-" + re.sub(r"[^A-Za-z0-9_.-]", "-", base)


def auto_facts(W, f: F, marks_a):
    """Generic code facts derived from marks (writes, calls, copybook PICs, JCL steps, DDL keys...)."""
    out = []
    path = f.path
    if f.kind == "cobol":
        pid = pathlib.Path(path).stem
        p = W.programs[pid]
        seen = set()
        for m, lines in sorted(marks_a.items(), key=lambda kv: kv[1][0]):
            if m.startswith("W:"):
                _, op, t = m.split(":", 2)
                if (op, t) in seen:
                    continue
                seen.add((op, t))
                needle = {"INSERT": f"INSERT INTO {t}", "UPDATE": f"UPDATE {t}", "DELETE": f"DELETE FROM {t}"}[op]
                out.append(cobol.Fact(f"w-{op}-{t}", (m, m), needle,
                                      f"{pid} executes {needle} (EXEC SQL {op}).",
                                      world_ref=f"PROGRAM:{pid}#writes_tables:{t}"))
            elif m.startswith("R:"):
                t = m[2:]
                if ("R", t) in seen:
                    continue
                seen.add(("R", t))
                kw = "JOIN" if f"JOIN {t}" in f.src.render(frozenset())[0] and f"FROM {t}" not in \
                    f.src.render(frozenset())[0] else "FROM"
                out.append(cobol.Fact(f"r-{t}", (m, m), f"{kw} {t}", f"{pid} reads {t} (EXEC SQL SELECT/cursor).",
                                      world_ref=f"PROGRAM:{pid}#reads_tables:{t}"))
            elif m.startswith("CALL:"):
                callee = m[5:]
                if ("C", callee) in seen or callee not in p["calls_programs"]:
                    continue
                seen.add(("C", callee))
                out.append(cobol.Fact(f"call-{callee}", (m, m), f"CALL '{callee}'", f"{pid} calls {callee}.",
                                      world_ref=f"PROGRAM:{pid}#calls_programs:{callee}"))
            elif m.startswith("COPY:") and m.count(":") == 1:
                cp = m[5:]
                out.append(cobol.Fact(f"copy-{cp}", (m, m), f"COPY {cp}.", f"{pid} includes copybook {cp}.",
                                      world_ref=f"PROGRAM:{pid}#copybooks:{cp}"))
    elif f.kind == "copybook":
        cp = pathlib.Path(path).stem
        c = W.copybooks[cp]
        if cp in ("RSVREC", "RSVMVT01", "RSVMOVE", "PARMREC1", "FRDREF01", "FRDSCR01", "CLRCOMM1", "CLRERR01",
                  "MQMDCLR1", "SENTRSP1", "SENTREQ1", "CLRCLM01", "FRDNOT01", "IFLOG01", "CLRDATE1"):
            for fld in c["fields"]:
                if fld["pic"] and f"CPY:{fld['name']}" in marks_a and fld["name"] != "FILLER":
                    out.append(cobol.Fact(f"pic-{fld['name']}", (f"CPY:{fld['name']}", f"CPY:{fld['name']}"),
                                          f"{fld['name']}", f"Copybook {cp} field {fld['name']} is PIC {fld['pic']}.",
                                          world_ref=f"COPYBOOK:{cp}#fields:{fld['name']}",
                                          extra={"needle_full": f"{fld['name']} PIC {fld['pic']}"}))
    elif f.kind == "jcl":
        job = pathlib.Path(path).stem
        j = W.jcl_jobs[job]
        for st in j["steps"]:
            m = f"RUN:{st['program']}"
            if m in marks_a:
                out.append(cobol.Fact(f"step-{st['step']}", (f"STEP:{st['step']}", m), f"RUN PROGRAM({st['program']})",
                                      f"Job {job} {st['step']} runs program {st['program']}.",
                                      world_ref=f"JCL:{job}#steps"))
        if "SCHED" in marks_a:
            sched = j["schedule"]
            out.append(cobol.Fact("sched", ("SCHED", "SCHED"), f"SCHEDULE  : {sched.upper()}",
                                  f"Job {job} is scheduled {sched}.", world_ref=f"JCL:{job}#schedule"))
        if "RESTART" in marks_a:
            out.append(cobol.Fact("restart", ("RESTART", "RESTART"), "RESTART   :",
                                  f"Job {job} restart instructions: {j['restart']}", world_ref=f"JCL:{job}#restart"))
        if "NFR99-SCHED" in marks_a:
            out.append(cobol.Fact("nfr99", ("NFR99-SCHED", "NFR99-SCHED"), "REMOVED FROM SCHEDULE 2026-04-01",
                                  "Job CLRNFR99 (auto-decline sweep CLRFR140) was removed from the schedule on 2026-04-01 "
                                  "(was daily 00:45).", world_ref="JCL:CLRNFR99#schedule", kind="temporal"))
        if "DRSV9-RET" in marks_a:
            out.append(cobol.Fact("drsv9", ("DRSV9-RET", "DRSV9-RET"), "RETIRED 2026-08-28",
                                  "Job CLRDRSV9 (reserve parallel-run reconciliation) is retired since 2026-08-28.",
                                  world_ref="JCL:CLRDRSV9#status", kind="temporal"))
    elif f.kind == "bms":
        for m in marks_a:
            if m.startswith("MAP:"):
                mp = W.bms_maps[m[4:]]
                out.append(cobol.Fact(f"map-{mp['map']}", (m, f"TXN:{mp['map']}"), f"* MAP {mp['map']} -",
                                      f"BMS map {mp['map']} ({mp['title']}) in mapset {mp['mapset']} is used by "
                                      f"transaction {mp['transaction']}, program {mp['program']}.",
                                      world_ref=f"BMS:{mp['map']}"))
    elif f.kind == "ddl" and path.endswith(".sql") and "seed" not in path:
        t = "CLR." + pathlib.Path(path).stem
        tb = W.tables[t]
        out.append(cobol.Fact("pk", ("DDL-PK", "DDL-PK"), f"PRIMARY KEY ({', '.join(tb['primary_key'])})",
                              f"{t} has primary key ({', '.join(tb['primary_key'])}).", world_ref=f"TABLE:{t}#primary_key"))
        for fk in tb.get("foreign_keys", []):
            m = f"FK:{fk['column']}"
            if m in marks_a:
                out.append(cobol.Fact(f"fk-{fk['column']}", (m, m), f"FOREIGN KEY ({fk['column']})",
                                      f"{t}.{fk['column']} references {fk['references']}.",
                                      world_ref=f"TABLE:{t}#foreign_keys"))
        if "DDL-CREATED" in marks_a:
            out.append(cobol.Fact("created", ("DDL-CREATED", "DDL-CREATED"), f"Created {tb['created']}",
                                  f"{t} was created on {tb['created']} (CHUB-206).", world_ref=f"TABLE:{t}#created",
                                  kind="temporal"))
        if t in ("CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT", "CLR.T_FRAUD_REFERRAL", "CLR.T_PARAM"):
            for c in tb["columns"]:
                m = f"CMT:{c['name']}"
                if m in marks_a:
                    out.append(cobol.Fact(f"col-{c['name']}", (m, m), f"COMMENT ON COLUMN {t}.{c['name']}",
                                          f"{t}.{c['name']}: {c['description']}", world_ref=f"TABLE:{t}#columns:{c['name']}"))
    return out


def resolve_fact(f: F, fact, marks, text_lines):
    m0, m1 = fact.marks
    if fact.extra.get("span") == "calls":
        ls = sum((marks.get(f"CALL:{c}", []) for c in ("CLRRS015", "CLRCM030", "CLRCM040", "CLRCM020")), [])
        start, end = min(ls), max(ls)
    else:
        if m0 not in marks or m1 not in marks:
            raise RuntimeError(f"{f.path}: mark {m0}/{m1} missing for {fact.fid_suffix}")
        start = min(marks[m0])
        end = max(marks[m1]) if m1 != m0 else min(marks[m1])
        if end < start:
            start, end = min(marks[m1]), max(marks[m0])
    return start, end


def norm(s):
    return " ".join(s.lower().split())


# ---------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-check-trees", action="store_true")
    args = ap.parse_args()
    W = load_world()
    cs = commits.all_commits(W)
    cinfo = {c["id"]: c for c in cs}
    order = [c["id"] for c in cs]
    st = states(order)
    a_state = frozenset(c for c in order if c not in commits.C_ONLY)
    all_state = st[order[-1]]
    files, prog_stats = build_files(W, cs)
    paths = [f.path for f in files]
    assert len(paths) == len(set(paths)), "duplicate paths"

    renders = {}
    for f in files:
        a_txt, _ = f.src.render(a_state)
        c_txt, _ = f.src.render(all_state)
        renders[f.path] = {"a": a_txt, "c": c_txt}

    errors: list[str] = []
    check_all(W, files, renders, errors, prog_stats)

    # ---- write outputs (only our own trees)
    for d in (OUT, OUT_C):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    changed_c = []
    for f in files:
        p = OUT / f.path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(renders[f.path]["a"], encoding="ascii" if f.path.endswith((".cbl", ".cpy", ".jcl", ".bms")) else "utf-8")
        if renders[f.path]["c"] != renders[f.path]["a"]:
            q = OUT_C / f.path
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_text(renders[f.path]["c"], encoding="ascii")
            changed_c.append(f.path)
    if changed_c != [f"{LEG}/cobol/CLRFR040.cbl"]:
        errors.append(f"variant c changes unexpected files: {changed_c}")

    # ---- history
    hist_files = []
    for f in files:
        e = history_entry(f, order, st, cinfo)
        try:
            verify_replay(f, e, order, st, renders[f.path]["a"], renders[f.path]["c"])
        except RuntimeError as exc:
            errors.append(str(exc))
        hist_files.append(e)
    hist = {"format_version": 1, "source_root": "build/code_src/legacy", "override_root": "build/code_src/legacy_c",
            "commits": [{k: c[k] for k in ("id", "world", "date", "author", "author_name", "author_email", "message",
                                           "variants", "tickets", "fold_into")} for c in cs],
            "files": hist_files}
    with open(OUT / "history.yaml", "w", encoding="utf-8") as fh:
        fh.write(HIST_HEADER)
        yaml.dump(hist, fh, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=200)

    # ---- manifest
    entries = []
    placements = {p["placement_id"]: p for p in W.placements}
    for f in files:
        marks_a = f.src.mark_lines(a_state)
        marks_c = f.src.mark_lines(all_state)
        facts = list(f.facts) + auto_facts(W, f, marks_a)
        lines_a = renders[f.path]["a"].splitlines()
        lines_c = renders[f.path]["c"].splitlines()
        n = 0
        pre = fid_prefix(f.path)
        for fact in facts:
            variant = fact.variant
            marks = marks_c if variant == "c" else marks_a
            lines = lines_c if variant == "c" else lines_a
            try:
                start, end = resolve_fact(f, fact, marks, lines)
            except (RuntimeError, ValueError) as exc:
                errors.append(f"fact {fact.fid_suffix}: {exc}")
                continue
            needle = fact.extra.get("needle_full", fact.needle)
            seg = norm("\n".join(lines[start - 1:end]))
            if norm(needle) not in seg:
                if norm(fact.needle) in seg:
                    needle = fact.needle
                else:
                    errors.append(f"{f.path}: needle {needle!r} not in lines {start}-{end} ({variant})")
                    continue
            n += 1
            e = {"fact_id": f"{pre}-F{n:03d}", "world_ref": fact.world_ref, "kind": fact.kind,
                 "statement": fact.statement, "file": f"build/code_repo/variant_{variant}/{f.path}",
                 "locator": {"kind": "code_lines", "variant": variant, "path": f.path, "start": start, "end": end},
                 "needle": needle}
            if fact.placement:
                pl = placements[fact.placement]
                e["world_ref"] = pl["world_ref"]
                e["kind"] = pl["kind"]
                e["exclusive"] = bool(pl.get("exclusive"))
                e["also_in"] = list(pl.get("also_in", []))
                e["placement"] = fact.placement
                e["placement_key"] = pl["key"]
                if pl.get("contradictions"):
                    e["contradictions"] = list(pl["contradictions"])
            else:
                e["exclusive"] = False
                e["also_in"] = []
            if fact.kind == "resync_change" and not fact.placement:
                e["notes"] = "variant c only (follow-up commit CM-09, 2026-11-12)"
            if f.renamed_from:
                e.setdefault("notes", f"file was {f.renamed_from[1]} until commit {f.renamed_from[0]}")
            entries.append(e)
    # every legacy CODE placement planted exactly once
    got = {e.get("placement") for e in entries}
    want = {p["placement_id"] for p in W.placements
            if str(p["target_file"]).startswith("CODE:") and str(p["target_file"]).split(":", 2)[2].startswith("legacy/")}
    for pl in sorted(want - got):
        errors.append(f"placement {pl} not planted")
    for pl in sorted(got - want - {None}):
        errors.append(f"unexpected placement {pl}")
    util.write_manifest(MANIFEST, entries)

    # ---- check trees: build/code_check_legacy/variant_{a,b,c}
    if not args.no_check_trees:
        if CHECK.exists():
            shutil.rmtree(CHECK)
        for v in ("a", "b", "c"):
            root = CHECK / f"variant_{v}"
            for f in files:
                if v not in f.variants:
                    continue
                dst = root / f.path
                dst.parent.mkdir(parents=True, exist_ok=True)
                txt = renders[f.path]["c" if v == "c" else "a"]
                dst.write_text(txt, encoding="utf-8")

    # ---- summary
    total = 0
    counts = {"a": 0, "b_only": 0}
    for f in files:
        p = OUT / f.path
        size = p.stat().st_size
        total += size
        if "a" in f.variants:
            counts["a"] += 1
        else:
            counts["b_only"] += 1
        print(f"{f.path} {size} {len(renders[f.path]['a'].splitlines())}")
    hs = (OUT / "history.yaml").stat().st_size
    print(f"history.yaml {hs}")
    print(f"TOTAL files: variant-a legacy {counts['a']}, variant-b-only {counts['b_only']}, "
          f"bytes {total} (+history {hs}); facts {len(entries)}")
    if total > 12 * 1024 * 1024:
        errors.append(f"legacy part {total} bytes > 12 MB")
    if not 240 <= counts["a"] <= 262:
        errors.append(f"variant-a legacy file count {counts['a']} outside 240-262")
    if not 100 <= counts["b_only"] <= 130:
        errors.append(f"variant-b-only count {counts['b_only']} outside 100-130")
    stats_path = ROOT / "build" / "cache" / "code_legacy_stats.yaml"
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(yaml.safe_dump(prog_stats, sort_keys=True))
    if errors:
        print(f"SELF-CHECK FAILED ({len(errors)} problems):")
        for e in errors[:200]:
            print("  -", e)
        return 1
    print("SELF-CHECK OK: SQL tables, CALLs and COPYs match programs.yaml; history replays; needles resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
