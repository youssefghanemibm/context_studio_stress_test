#!/usr/bin/env python
"""Assemble Corvane's monorepo into three real git repositories (branch main).

    .venv/bin/python -I generators/code_repo/assemble.py [--regen] [--skip-gen] [--fold-extra]

Inputs (written by the two generator halves):
    build/code_src/legacy/            CLARA sources, final state of variant a (+ b-only files)
    build/code_src/legacy/history.yaml
    build/code_src/legacy_c/          CM-09 overrides for legacy files
    build/code_src/modern/            Claims Hub half, final state of variant a (+ b-only files)
    build/code_src/modern/history.yaml
    build/code_src/modern_c/          CM-09 overrides and new files for the modern half

history.yaml (both halves): ``commits`` (extra commits the half defines: id, date, author,
message, variants) and ``files`` (per path: variants, created_by, optional renamed_from /
renamed_by, removed_by, modifications [{commit, before, after}], c_override).  A file's content
before a commit is its final content with the 'after' snippets of that commit and every later
commit replaced by their 'before' snippets.  World commits CM-01..CM-09 come from
world/data/corpus_plan.yaml.

Outputs: build/code_repo/variant_a, variant_b, variant_c (deleted and recreated on every run)
and build/code_repo/SUMMARY.md.

Variant a = CM-01..CM-08 + filler commits, head 2026-11-06.  Variant b = a + one commit adding
every b-only file.  Variant c = a + CM-09 (2026-11-12).  Dates, identities and environment are
fixed, so commit SHAs are identical across runs.  Git hooks configured on the machine (for
example a pre-commit secret scanner) run normally; this script never bypasses them.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse  # noqa: E402
import datetime as dt  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402

import yaml  # noqa: E402

from generators.common import util  # noqa: E402
from world.worldlib import load_world  # noqa: E402

W = load_world()
SRC = ROOT / "build" / "code_src"
OUT = ROOT / "build" / "code_repo"
PY = str(ROOT / ".venv" / "bin" / "python")
HALVES = ("legacy", "modern")
HEAD_A = "2026-11-06"
CM09 = "CM-09"
B_DEFAULT = ("B-01", "2026-11-06", "P053", "Add legacy bridge, reconciliation tooling, fixtures and archived CLARA sources")

# Budgets.  The world plan says variant a is about 350 files; the modern half's mandated content
# (13 services, 30 ADRs, 13 Terraform modules, 10 namespaces x 3 manifests) needs ~165 files, so the
# hard limit for a is wider than the 330-370 target (see build/notes/code_modern.md).
BUDGET = {"a_files": (300, 440), "a_target": (330, 370), "a_mb": 30, "b_files": (600, 700), "b_mb": 45,
          "file_mb": 48}


# ---------------------------------------------------------------------------------------------
# Commits
# ---------------------------------------------------------------------------------------------

@dataclass
class Commit:
    id: str
    date: str
    author: str
    message: str
    variants: list
    when: dt.datetime = None
    origin: str = "world"
    fold_into: str | None = None


def _uk_offset(d: dt.date) -> str:
    def last_sunday(year, month):
        x = dt.date(year, month + 1, 1) - dt.timedelta(days=1) if month < 12 else dt.date(year, 12, 31)
        return x - dt.timedelta(days=(x.weekday() + 1) % 7)
    start, end = last_sunday(d.year, 3), last_sunday(d.year, 10)
    return "+0100" if start <= d < end else "+0000"


def load_commits(histories: dict, fold_extra: bool) -> dict[str, Commit]:
    commits: dict[str, Commit] = {}
    for c in W.commits.values():
        variants = ["c"] if c["variant"] == "c" else ["a", "b", "c"]
        commits[c["id"]] = Commit(c["id"], str(c["date"]), c["author"], c["message"], variants)
    for half, h in histories.items():
        for c in (h or {}).get("commits", []) or []:
            cid = c.get("id")
            if not cid or cid in commits:
                continue
            variants = c.get("variants") or ["a", "b", "c"]
            if isinstance(variants, str):
                variants = list(variants)
            commits[cid] = Commit(cid, str(c["date"])[:10], c["author"], c["message"], list(variants),
                                  origin=half, fold_into=c.get("fold_into"))
    if not any(c.variants == ["b"] for c in commits.values()):
        cid, date, author, msg = B_DEFAULT
        commits[cid] = Commit(cid, date, author, msg, ["b"], origin="assembler")
    # time of day: fixed per commit id; variant-b commit is the last thing on its day
    for c in commits.values():
        r = util.rng(f"code_repo:time:{c.id}")
        d = dt.date.fromisoformat(c.date)
        if c.variants == ["b"]:
            h, m = 17, 20
        else:
            h, m = r.randint(8, 16), r.randint(0, 59)
        c.when = dt.datetime(d.year, d.month, d.day, h, m, r.randint(0, 59))
    if fold_extra:
        for c in list(commits.values()):
            if c.origin != "world" and c.fold_into:
                pass  # resolved in the replay (file events are re-targeted to fold_into)
    return commits


def git_date(c: Commit) -> str:
    return c.when.strftime("%Y-%m-%dT%H:%M:%S") + _uk_offset(c.when.date())


# ---------------------------------------------------------------------------------------------
# File records
# ---------------------------------------------------------------------------------------------

@dataclass
class FileRec:
    half: str
    path: str
    final: bytes | None                # variant-a final content (None for c-only files)
    variants: list
    created_by: str
    removed_by: str | None = None
    renamed_from: str | None = None
    renamed_by: str | None = None
    mods: list = field(default_factory=list)
    c_content: bytes | None = None     # content after CM-09 (variant c)


def _norm_variants(v) -> list:
    if v is None:
        return ["a", "b", "c"]
    if isinstance(v, str):
        return [x for x in v if x in "abc"] if len(v) <= 3 else [v]
    return [str(x) for x in v]


def _iter_hist_files(h):
    files = (h or {}).get("files") or {}
    if isinstance(files, dict):
        for path, e in files.items():
            yield path, (e or {})
    else:
        for e in files:
            yield e.get("path"), e


def _mod_list(e):
    out = []
    for m in e.get("modifications") or e.get("mods") or []:
        cid = m.get("commit") or m.get("commit_id") or m.get("id")
        before = m.get("before", m.get("old", ""))
        after = m.get("after", m.get("new", ""))
        mv = m.get("variants")
        out.append({"commit": cid, "before": before, "after": after,
                    "variants": _norm_variants(mv) if mv is not None else None})
    return out


def _mod_in(m: dict, variant: str) -> bool:
    """Does modification ``m`` belong to the history of ``variant``? (a and b share history)"""
    mv = m.get("variants")
    if mv is None:
        return m["commit"] != CM09 or variant == "c"
    if variant in ("a", "b"):
        return "a" in mv or "b" in mv
    return "c" in mv


def load_half(half: str) -> tuple[dict, list[FileRec]]:
    base = SRC / half
    if not base.exists():
        return {}, []
    hist_path = base / "history.yaml"
    h = yaml.safe_load(hist_path.read_text(encoding="utf-8")) if hist_path.exists() else {}
    h = h or {}
    # paths in the src tree may be repo-relative (legacy/clara/...) or relative to legacy/
    prefix = ""
    if half == "legacy" and not (base / "legacy").exists() and (base / "clara").exists():
        prefix = "legacy/"
    entries = {}
    for path, e in _iter_hist_files(h):
        if not path:
            continue
        p = path if (not prefix or path.startswith("legacy/")) else prefix + path
        entries[p] = e
    recs = []
    on_disk = {}
    for f in sorted(base.rglob("*")):
        if not f.is_file() or f.name == "history.yaml" and f.parent == base:
            continue
        rel = f.relative_to(base).as_posix()
        if rel.startswith(".") and rel.split("/")[0] in (".DS_Store",):
            continue
        on_disk[prefix + rel] = f
    c_dir = SRC / f"{half}_c"
    c_files = {}
    if c_dir.exists():
        for f in sorted(c_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(c_dir).as_posix()
                if prefix and not rel.startswith("legacy/"):
                    rel = prefix + rel
                c_files[rel] = f
    default_created = "CM-01" if half == "legacy" else "F-01"
    paths = sorted(set(on_disk) | set(entries) | set(c_files))
    for p in paths:
        e = entries.get(p, {})
        final = on_disk[p].read_bytes() if p in on_disk else None
        if final is None and e.get("content") is not None:
            final = str(e["content"]).encode("utf-8")
        variants = _norm_variants(e.get("variants"))
        ren_from, ren_by = e.get("renamed_from"), e.get("renamed_by")
        if isinstance(ren_from, dict):          # legacy format: {commit, path}
            ren_by = ren_from.get("commit") or ren_by
            ren_from = ren_from.get("path")
        rec = FileRec(half=half, path=p, final=final, variants=variants,
                      created_by=e.get("created_by") or (CM09 if variants == ["c"] else default_created),
                      removed_by=e.get("removed_by") or e.get("deleted_by"),
                      renamed_from=ren_from, renamed_by=ren_by,
                      mods=_mod_list(e))
        if rec.renamed_from and not rec.renamed_by:
            rec.renamed_by = "CM-04"
        if p in c_files:
            rec.c_content = c_files[p].read_bytes()
            if final is None and "c" not in rec.variants:
                rec.variants = ["c"]
        if final is None and rec.c_content is None:
            print(f"WARN {half}: {p} has no content (skipped)")
            continue
        recs.append(rec)
    return h, recs


# ---------------------------------------------------------------------------------------------
# Content as of a commit
# ---------------------------------------------------------------------------------------------

class Timeline:
    def __init__(self, commits: dict[str, Commit], fold_extra: bool):
        self.commits = commits
        self.fold_extra = fold_extra
        order = sorted(commits.values(), key=lambda c: (c.when, c.id))
        self.pos = {c.id: i for i, c in enumerate(order)}
        self.order = order

    def eff(self, cid: str | None) -> str | None:
        """Commit a file event lands in (folding extra commits when requested)."""
        if cid is None:
            return None
        c = self.commits.get(cid)
        if c is None:
            return None
        if self.fold_extra and c.origin != "world" and c.origin != "modern" and c.variants != ["b"]:
            target = c.fold_into
            if not target:
                # no later world commit: fold into the last variant-a commit
                a = [x for x in self.order if "a" in x.variants and x.variants != ["b"]]
                target = a[-1].id
            return target
        return cid

    def p(self, cid: str | None) -> float:
        cid = self.eff(cid)
        if cid is None:
            return float("inf")
        return self.pos.get(cid, float("inf"))


def content_at(rec: FileRec, upto: int, variant: str, tl: Timeline) -> bytes | None:
    """Content after the commit at position ``upto`` in the global order, for ``variant``."""
    cm09 = tl.p(CM09)
    if variant == "c" and upto >= cm09 and rec.c_content is not None:
        return rec.c_content
    if rec.final is None:
        return None
    try:
        text = rec.final.decode("utf-8")
    except UnicodeDecodeError:
        return rec.final
    groups: dict[str, list] = {}
    for m in rec.mods:
        if m["commit"] != CM09 and _mod_in(m, "a" if variant == "c" else variant):
            groups.setdefault(m["commit"], []).append(m)
    # newest commit first; within a commit apply every hunk at once (positions found first)
    for cid in sorted(groups, key=lambda c: (tl.p(c), tl.pos.get(c, 0)), reverse=True):
        if tl.p(cid) <= upto:
            continue
        text = _apply(text, [(m["after"], m["before"]) for m in groups[cid]], rec.path, cid)
    if variant == "c" and upto >= cm09 and rec.c_content is None:
        c_mods = [(m["before"], m["after"]) for m in rec.mods if m["commit"] == CM09]
        if c_mods:
            text = _apply(text, c_mods, rec.path, CM09)
    return text.encode("utf-8")


def _apply(text: str, pairs: list[tuple[str, str]], path: str, cid: str) -> str:
    """Replace each ``old`` by ``new`` (all located in the same text before replacing)."""
    spots = []
    for old, new in pairs:
        if old == "":
            raise ValueError(f"{path}: empty snippet in {cid}")
        i = text.find(old)
        if i < 0:
            raise ValueError(f"{path}: snippet of {cid} not found: {old[:60]!r}")
        spots.append((i, old, new))
    spots.sort(key=lambda s: s[0], reverse=True)
    last = len(text) + 1
    for i, old, new in spots:
        if i + len(old) > last:
            raise ValueError(f"{path}: overlapping snippets in {cid}")
        text = text[:i] + new + text[i + len(old):]
        last = i
    return text


def path_at(rec: FileRec, upto: int, tl: Timeline) -> str:
    if rec.renamed_from and upto < tl.p(rec.renamed_by):
        return rec.renamed_from
    return rec.path


def exists_at(rec: FileRec, upto: int, variant: str, tl: Timeline) -> bool:
    if variant not in rec.variants and not (variant == "c" and rec.c_content is not None and upto >= tl.p(CM09)):
        return False
    created = rec.created_by
    if rec.variants == ["b"]:
        created = next((c.id for c in tl.order if c.variants == ["b"]), created)
    if rec.variants == ["c"]:
        created = CM09
    if tl.p(created) > upto:
        return False
    if rec.removed_by and tl.p(rec.removed_by) <= upto:
        return False
    return True


# ---------------------------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------------------------

def git(repo: pathlib.Path, *args, env=None, check=True, capture=True):
    base_env = dict(os.environ)
    base_env.update({"GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C", "TZ": "UTC"})
    if env:
        base_env.update(env)
    res = subprocess.run(["git", "-C", str(repo), "-c", "core.autocrlf=false", "-c", "core.safecrlf=false",
                          "-c", "init.defaultBranch=main", *args],
                         env=base_env, capture_output=capture, text=True, timeout=600)
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed ({res.returncode}): {res.stderr.strip()}\n{res.stdout.strip()}")
    return res


def commit(repo: pathlib.Path, c: Commit):
    name = W.name_of(c.author, dt.date.fromisoformat(c.date))
    email = W.people[c.author]["email"]
    date = git_date(c)
    env = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": date,
           "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email, "GIT_COMMITTER_DATE": date}
    git(repo, "add", "-A")
    git(repo, "-c", f"user.name={name}", "-c", f"user.email={email}", "commit", "--allow-empty", "-q",
        "-m", c.message, env=env)


def sync_tree(repo: pathlib.Path, current: dict[str, bytes], target: dict[str, bytes], renames: list[tuple[str, str]]):
    for old, new in renames:
        if old in current and new not in current:
            (repo / new).parent.mkdir(parents=True, exist_ok=True)
            git(repo, "mv", old, new)
            current[new] = current.pop(old)
    for p in sorted(set(current) - set(target)):
        f = repo / p
        if f.exists():
            f.unlink()
        d = f.parent
        while d != repo and d.exists() and not any(d.iterdir()):
            d.rmdir()
            d = d.parent
        current.pop(p)
    for p, data in sorted(target.items()):
        if current.get(p) != data:
            f = repo / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
            current[p] = data


def tree_at(recs: list[FileRec], upto: int, variant: str, tl: Timeline) -> tuple[dict, list]:
    target, renames = {}, []
    for r in recs:
        if not exists_at(r, upto, variant, tl):
            continue
        p = path_at(r, upto, tl)
        data = content_at(r, upto, variant, tl)
        if data is None:
            continue
        if p in target:
            raise ValueError(f"two sources for {p}")
        target[p] = data
        if r.renamed_from and tl.p(r.renamed_by) == upto:
            renames.append((r.renamed_from, r.path))
    return target, renames


def build_variant_a(recs, tl: Timeline, out: pathlib.Path) -> list[Commit]:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    git(out, "init", "-q", "-b", "main")
    current: dict[str, bytes] = {}
    made = []
    a_commits = [c for c in tl.order if "a" in c.variants and c.variants != ["b"] and tl.eff(c.id) == c.id]
    for c in a_commits:
        upto = tl.pos[c.id]
        target, renames = tree_at(recs, upto, "a", tl)
        sync_tree(out, current, target, renames)
        commit(out, c)
        made.append(c)
    return made


def build_from_a(a_dir: pathlib.Path, out: pathlib.Path, recs, tl: Timeline, variant: str, extra: Commit):
    if out.exists():
        shutil.rmtree(out)
    git(a_dir.parent, "clone", "-q", "--no-local", a_dir.name, out.name)
    git(out, "remote", "remove", "origin")
    current = {}
    for p in git(out, "ls-files", "-z").stdout.split("\0"):
        if p:
            current[p] = (out / p).read_bytes()
    upto = tl.pos[extra.id]
    target, renames = tree_at(recs, upto, variant, tl)
    sync_tree(out, current, target, renames)
    commit(out, extra)


# ---------------------------------------------------------------------------------------------

def run_generators(regen: bool, skip: bool):
    if skip:
        return
    for half in HALVES:
        gen = ROOT / "generators" / f"code_{half}" / "generate.py"
        missing = not (SRC / half).exists() or not any((SRC / half).iterdir())
        if (regen or missing) and gen.exists():
            print(f"running {gen.relative_to(ROOT)}")
            subprocess.run([PY, "-I", str(gen)], check=True, cwd=ROOT, timeout=1200,
                           stdout=subprocess.DEVNULL)
        elif missing:
            print(f"WARN {half} half missing and {gen.relative_to(ROOT)} not found: building without it")


def tracked(repo: pathlib.Path) -> tuple[int, int, int]:
    files = [p for p in git(repo, "ls-files", "-z").stdout.split("\0") if p]
    sizes = [(repo / p).stat().st_size for p in files]
    return len(files), sum(sizes), max(sizes) if sizes else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regen", action="store_true", help="re-run both generators first")
    ap.add_argument("--skip-gen", action="store_true", help="never run the generators")
    ap.add_argument("--fold-extra", action="store_true",
                    help="fold the legacy half's extra commits into their fold_into world commits")
    ap.add_argument("--no-assert", action="store_true")
    args = ap.parse_args(argv)
    run_generators(args.regen, args.skip_gen)

    histories, recs = {}, []
    for half in HALVES:
        h, r = load_half(half)
        histories[half] = h
        recs += r
        print(f"{half}: {len(r)} source files" + ("" if r else " (missing)"))
    commits = load_commits(histories, args.fold_extra)
    tl = Timeline(commits, args.fold_extra)
    unknown = sorted({r.created_by for r in recs
                      if r.created_by not in commits and r.variants not in (["b"], ["c"])} |
                     {m["commit"] for r in recs for m in r.mods if m["commit"] not in commits})
    if unknown:
        raise SystemExit(f"history references unknown commits: {unknown}")

    OUT.mkdir(parents=True, exist_ok=True)
    a_dir, b_dir, c_dir = OUT / "variant_a", OUT / "variant_b", OUT / "variant_c"
    made = build_variant_a(recs, tl, a_dir)
    b_commit = next(c for c in tl.order if c.variants == ["b"])
    build_from_a(a_dir, b_dir, recs, tl, "b", b_commit)
    build_from_a(a_dir, c_dir, recs, tl, "c", commits[CM09])

    rows, problems = [], []
    for v, d in (("a", a_dir), ("b", b_dir), ("c", c_dir)):
        n, size, biggest = tracked(d)
        head = git(d, "rev-parse", "HEAD").stdout.strip()
        ncommits = int(git(d, "rev-list", "--count", "HEAD").stdout.strip())
        last = git(d, "log", "-1", "--format=%ad", "--date=short").stdout.strip()
        rows.append((v, n, size, biggest, ncommits, last, head))
        print(f"variant_{v}: {n} files, {size / 1e6:.2f} MB, {ncommits} commits, head {last} {head[:12]}")
        if biggest > BUDGET["file_mb"] * 1e6:
            problems.append(f"variant {v}: a file exceeds {BUDGET['file_mb']} MB")
    a, b, c = rows
    if not (BUDGET["a_files"][0] <= a[1] <= BUDGET["a_files"][1]):
        problems.append(f"variant a has {a[1]} files (limit {BUDGET['a_files']})")
    if not (BUDGET["a_target"][0] <= a[1] <= BUDGET["a_target"][1]):
        print(f"NOTE variant a has {a[1]} files, outside the 330-370 target (see notes)")
    if a[2] > BUDGET["a_mb"] * 1e6:
        problems.append(f"variant a is {a[2] / 1e6:.1f} MB (> {BUDGET['a_mb']})")
    if not (BUDGET["b_files"][0] <= b[1] <= BUDGET["b_files"][1]):
        problems.append(f"variant b has {b[1]} files (budget {BUDGET['b_files']})")
    if b[2] > BUDGET["b_mb"] * 1e6:
        problems.append(f"variant b is {b[2] / 1e6:.1f} MB (> {BUDGET['b_mb']})")
    if a[5] != HEAD_A:
        problems.append(f"variant a head is dated {a[5]}, expected {HEAD_A}")
    if b[4] != a[4] + 1 or c[4] != a[4] + 1:
        problems.append("variants b and c must each add exactly one commit to a")
    legacy_present = any(r.half == "legacy" for r in recs)

    lines = ["# Code repositories (generated)", "",
             "Built by `generators/code_repo/assemble.py` from `build/code_src/` (do not edit by hand).", "",
             "| Variant | Files | MB | Commits | Head date |", "|---|---|---|---|---|"]
    for v, n, size, biggest, nc, last, head in rows:
        lines.append(f"| {v} | {n} | {size / 1e6:.2f} | {nc} | {last} |")
    lines += ["", f"Legacy half present: {'yes' if legacy_present else 'NO (modern half only)'}.", "",
              "## History of variant a", "", "| Date | Author | Message |", "|---|---|---|"]
    for c in made:
        lines.append(f"| {git_date(c)[:10]} | {W.name_of(c.author, dt.date.fromisoformat(c.date))} | "
                     f"{c.message.replace('|', '/')} |")
    lines += ["", f"Variant b adds: {b_commit.message} ({b_commit.date}).",
              f"Variant c adds: {commits[CM09].message} ({commits[CM09].date}).", ""]
    if problems:
        lines += ["## Budget problems", ""] + [f"- {p}" for p in problems] + [""]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    for p in problems:
        print("BUDGET", p)
    if problems and not args.no_assert:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
