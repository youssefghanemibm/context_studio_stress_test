#!/usr/bin/env python
"""Generate the modern half of Corvane's monorepo (Claims Hub) plus its history metadata.

    .venv/bin/python -I generators/code_modern/generate.py [--no-manifest]

Writes (and only these):
    build/code_src/modern/          final state of variant a, plus variant-b-only files
    build/code_src/modern/history.yaml
                                    per file: variants, created_by, renamed_from, modifications
                                    (before/after snippets) and the filler / variant-b commits
    build/code_src/modern_c/        CM-09 overrides and new files (variant c)
    manifests/code_modern.facts.yaml

The git repos themselves are built by generators/code_repo/assemble.py.
"""
from __future__ import annotations

import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import argparse  # noqa: E402
import shutil  # noqa: E402

import yaml  # noqa: E402

from generators.common import util  # noqa: E402
from harness import extract as X  # noqa: E402
import lib  # noqa: E402
from lib import (W, Repo, OUT_A, OUT_C, HISTORY, FILLER, B_COMMIT, FACT_PREFIX, line_range, norm_ws,  # noqa: E402
                 commit_date)
import services  # noqa: E402
import infra  # noqa: E402
import docs  # noqa: E402
import extras_b  # noqa: E402
import variant_c  # noqa: E402
import facts as facts_mod  # noqa: E402


class _Literal(str):
    pass


def _literal_repr(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|" if "\n" in data else None)


yaml.add_representer(_Literal, _literal_repr, Dumper=yaml.SafeDumper)


def build_repo() -> tuple[Repo, dict]:
    repo = Repo()
    repo.cm09_mods = {}
    services.build(repo)
    infra.build(repo)
    docs.build(repo)
    stats = extras_b.build(repo)
    variant_c.build(repo)
    repo.check_mods()
    return repo, stats


def write_outputs(repo: Repo) -> None:
    for d in (OUT_A, OUT_C):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    for path, fs in sorted(repo.files.items()):
        out = OUT_A / path
        out.parent.mkdir(parents=True, exist_ok=True)
        if fs.binary:
            out.write_bytes(fs.content)
        else:
            out.write_text(fs.content, encoding="utf-8", newline="\n")
    for path, text in sorted({**repo.c_overrides, **repo.c_new}.items()):
        out = OUT_C / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8", newline="\n")

    commits = []
    for cid, date, author, msg in FILLER:
        commits.append({"id": cid, "date": date, "author": author, "message": msg, "variants": ["a", "b", "c"]})
    cid, date, author, msg = B_COMMIT
    commits.append({"id": cid, "date": date, "author": author, "message": msg, "variants": ["b"]})
    files = {}
    for path, fs in sorted(repo.files.items()):
        e = {"variants": fs.variants, "created_by": fs.created_by}
        if fs.author:
            e["author"] = fs.author
        if fs.renamed_from:
            e["renamed_from"] = fs.renamed_from
            e["renamed_by"] = "CM-04"
        if fs.binary:
            e["binary"] = True
        mods = sorted(fs.mods, key=lambda m: commit_date(m["commit"]))
        mods += repo.cm09_mods.get(path, [])
        if mods:
            e["modifications"] = [{"commit": m["commit"], "before": _Literal(m["before"]),
                                   "after": _Literal(m["after"])} for m in mods]
        if path in repo.c_overrides:
            e["c_override"] = f"modern_c/{path}"
        files[path] = e
    for path in sorted(repo.c_new):
        files[path] = {"variants": ["c"], "created_by": "CM-09", "c_override": f"modern_c/{path}"}
    doc = {
        "format": "corvane-code-history/1",
        "half": "modern",
        "generated_by": "generators/code_modern/generate.py",
        "notes": ("Paths are repo-relative. 'created_by' is the commit that adds the file; files created before "
                  "CM-04 under services/reserve-engine or infra/terraform/modules/reserve-engine exist at "
                  "'renamed_from' until CM-04 moves them with git mv. A file's content before a commit is obtained "
                  "by replacing that commit's 'after' snippet with its 'before' snippet, newest commit first. "
                  "CM-09 modifications apply to variant c only; the full CM-09 files are in build/code_src/modern_c. "
                  "Files whose variants are [b] are added by the variant-b commit B-01."),
        "commits": commits,
        "files": files,
    }
    with open(HISTORY, "w", encoding="utf-8") as fh:
        yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True, width=120)


def manifest_entries(repo: Repo) -> list[dict]:
    out = []
    tag_ids = {}
    for i, f in enumerate(repo.facts, 1):
        fid = f"{FACT_PREFIX}-F{i:03d}"
        if f.get("tag"):
            tag_ids[f["tag"]] = fid
    for i, f in enumerate(repo.facts, 1):
        fid = f"{FACT_PREFIX}-F{i:03d}"
        v = f["variant"]
        e = {"fact_id": fid, "world_ref": f["world_ref"], "kind": f["kind"], "statement": f["statement"]}
        if f["loc"] == "code":
            text = repo.text_of(v, f["path"])
            start, end = line_range(text, f["needle"], f.get("span"), f.get("anchor"))
            e["file"] = f"build/code_repo/variant_{v}/{f['path']}"
            e["locator"] = {"kind": "code_lines", "variant": v, "path": f["path"], "start": start, "end": end}
        elif f["loc"] == "image":
            e["file"] = f"build/code_repo/variant_{v}/{f['path']}"
            e["locator"] = {"kind": "image_ocr", "ocr": True}
        else:
            e["file"] = f"build/code_repo/variant_{v}"
            e["locator"] = {"kind": "git_commit", "variant": v, "message_contains": f["message_contains"]}
        e["needle"] = norm_ws(f["needle"])
        e["exclusive"] = bool(f["exclusive"])
        also = []
        for a in f.get("also_in") or []:
            also.append(tag_ids[a[1:]] if a.startswith("@") else a)
        e["also_in"] = also
        if f.get("placement"):
            e["placement"] = f["placement"]
            e["placement_key"] = W.placements_by_id[f["placement"]]["key"]
        if f.get("notes"):
            e["notes"] = f["notes"]
        out.append(e)
    return out


def leak_check(repo: Repo) -> list[str]:
    """Exclusive needles of other families must not appear in any modern file."""
    problems = []
    texts = {}
    for path, fs in repo.files.items():
        if not fs.binary:
            texts[path] = X.normalize(fs.content)
    for path, t in {**repo.c_overrides, **repo.c_new}.items():
        texts["c:" + path] = X.normalize(t)
    for mf in sorted(util.MANIFESTS.glob("*.facts.yaml")):
        if mf.name.startswith("code_"):
            continue
        for e in yaml.safe_load(mf.read_text(encoding="utf-8")) or []:
            if not e.get("exclusive") or not isinstance(e.get("needle"), str):
                continue
            n = X.normalize(e["needle"])
            if len(n) < 6:
                continue
            for path, t in texts.items():
                if n in t:
                    problems.append(f"{e['fact_id']} needle {e['needle']!r} found in {path}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-manifest", action="store_true")
    args = ap.parse_args(argv)
    repo, stats = build_repo()
    write_outputs(repo)
    facts_mod.register(repo, stats)
    entries = manifest_entries(repo)
    if not args.no_manifest:
        util.write_manifest("code_modern", entries)
    leaks = leak_check(repo)
    for l in leaks:
        print("LEAK", l)
    a = [p for p, f in repo.files.items() if "a" in f.variants]
    b_only = [p for p, f in repo.files.items() if f.variants == ["b"]]
    size_a = sum(len(repo.files[p].content if repo.files[p].binary else repo.files[p].content.encode()) for p in a)
    size_b = sum(len(repo.files[p].content.encode()) for p in b_only)
    print(f"modern variant-a files {len(a)} ({size_a / 1e6:.2f} MB); variant-b-only files {len(b_only)} "
          f"({size_b / 1e6:.2f} MB); variant-c overrides {len(repo.c_overrides)} + new {len(repo.c_new)}")
    print(f"facts {len(entries)}; placements {sum(1 for e in entries if e.get('placement'))}; leaks {len(leaks)}")
    for p in sorted(a + b_only):
        fs = repo.files[p]
        n = len(fs.content) if fs.binary else len(fs.content.encode())
        units = "-" if fs.binary else str(fs.content.count("\n"))
        print(f"{p} {n} {units}")
    return 1 if leaks else 0


if __name__ == "__main__":
    raise SystemExit(main())
