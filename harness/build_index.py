#!/usr/bin/env python
"""Full-text index of the corpus, used for exclusivity, denylist, secret and PII checks.

For every file under corpus/upload and corpus/rejected, every tracked file of the generated
code repos (build/code_repo/variant_<x>/) and every repo's commit history, this writes
build/index/<sha1-of-relpath>.jsonl with one {file, locator, text} line per textual unit
(units come from harness.extract.iter_units, so every locator round-trips through resolve()).

Incremental: files whose sha1 is unchanged are skipped (state in build/index/_state.json).
OCR (the slow part) is fanned out per PDF page / image across a process pool first; the
results land in the shared OCR cache that extraction then reads.

Library:
    build(sources=None, index_dir=INDEX_DIR, jobs=8, ocr=True, force=False) -> stats dict
    search(pattern, regex=False, files=None, ...) -> list[hit dict]
    discover_sources(roots=None, include_code=True) -> list[Source]

CLI:
    python -I harness/build_index.py [--jobs 8] [--no-ocr] [--rebuild]
    python -I harness/build_index.py --search "Sentinel score" [--regex] [--files GLOB ...]
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import bisect
import concurrent.futures as cf
import fnmatch
import hashlib
import json
import multiprocessing
import os
import re
import subprocess
import time
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Iterator

from harness import extract as X

Path = pathlib.Path

INDEX_DIR = ROOT / "build" / "index"
STATE_NAME = "_state.json"
INDEX_FORMAT = 1
DEFAULT_ROOTS = (ROOT / "corpus" / "upload", ROOT / "corpus" / "rejected")


@dataclass(frozen=True)
class Source:
    """One indexable thing: a corpus file, a code-repo file, or a repo's git history."""
    rel: str                 # index key: repo-relative path (git history: "<repo>/.git")
    path: str                # absolute file path (or repo dir for git_log)
    kind: str = "file"       # "file" | "code" | "git_log"
    variant: str = ""        # code repo variant letter
    repo_path: str = ""      # path inside the code repo
    code_root: str = ""      # code repo root (passed to workers)


# ---------------------------------------------------------------------------------------------
# Discovery and fingerprints
# ---------------------------------------------------------------------------------------------

def _git(repo: Path, *args: str) -> str:
    res = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=120)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode(errors="replace").strip())
    return res.stdout.decode("utf-8", errors="replace")


def discover_sources(roots: Iterable[os.PathLike | str] | None = None, include_code: bool = True,
                     repo_root: Path = ROOT) -> list[Source]:
    """Corpus files under ``roots`` plus (optionally) every code repo variant's files and history."""
    out: list[Source] = []
    for root in (roots if roots is not None else DEFAULT_ROOTS):
        root = Path(root)
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file() and not any(part.startswith(".") or part == "__pycache__"
                                       for part in p.relative_to(root).parts):
                out.append(Source(X.rel_path(p, repo_root), str(p)))
    if include_code:
        code_root = X.code_repo_root(repo_root)
        for vdir in sorted(code_root.glob("variant_*")) if code_root.exists() else []:
            if not (vdir / ".git").exists():
                continue
            variant = vdir.name[len("variant_"):]
            try:
                listed = _git(vdir, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
                files = [f for f in listed.split("\x00") if f]
            except RuntimeError:
                files = [p.relative_to(vdir).as_posix() for p in vdir.rglob("*")
                         if p.is_file() and ".git" not in p.relative_to(vdir).parts]
            for f in sorted(set(files)):
                p = vdir / f
                if p.is_file():
                    out.append(Source(X.rel_path(p, repo_root), str(p), "code", variant, f, str(code_root)))
            out.append(Source(X.rel_path(vdir, repo_root) + "/.git", str(vdir), "git_log", variant, "",
                              str(code_root)))
    return out


def fingerprint(src: Source) -> str:
    if src.kind == "git_log":
        refs = _git(Path(src.path), "for-each-ref", "--format=%(objectname) %(refname)")
        head = _git(Path(src.path), "rev-parse", "HEAD")
        return hashlib.sha1((refs + head).encode()).hexdigest()
    return X.file_sha1(src.path)


def index_file_name(rel: str) -> str:
    return hashlib.sha1(rel.encode("utf-8")).hexdigest() + ".jsonl"


# ---------------------------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------------------------

def _version() -> dict:
    return {"index_format": INDEX_FORMAT, "extractor": X.EXTRACTOR_VERSION}


def load_state(index_dir: Path = INDEX_DIR) -> dict:
    p = Path(index_dir) / STATE_NAME
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"_meta": _version(), "files": {}}


def save_state(state: dict, index_dir: Path = INDEX_DIR) -> None:
    p = Path(index_dir) / STATE_NAME
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


# ---------------------------------------------------------------------------------------------
# Workers (top-level so they pickle under the spawn start method)
# ---------------------------------------------------------------------------------------------

def _units_for(src: Source, ocr: bool) -> Iterator[tuple[dict, str]]:
    if src.code_root:
        X.set_code_repo_root(src.code_root)
    if src.kind == "git_log":
        yield from X.iter_git_units(Path(src.path), src.variant)
    elif src.kind == "code":
        yield from X.iter_code_units(Path(src.path), src.variant, src.repo_path)
    else:
        yield from X.iter_units(src.path, ocr=ocr)


def _index_one(args: tuple) -> dict:
    src, index_dir, ocr, sha = args
    out = Path(index_dir) / index_file_name(src.rel)
    tmp = out.with_suffix(f".{os.getpid()}.tmp")
    n, err = 0, None
    t0 = time.time()
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            for loc, text in _units_for(src, ocr):
                fh.write(json.dumps({"file": src.rel, "locator": loc, "text": text}, ensure_ascii=False) + "\n")
                n += 1
    except Exception as exc:  # keep the partial index, record the error
        err = f"{type(exc).__name__}: {exc}"
    finally:
        if tmp.exists():
            os.replace(tmp, out)
    return {"rel": src.rel, "sha1": sha, "index": out.name, "units": n, "ocr": ocr, "error": err,
            "kind": src.kind, "seconds": round(time.time() - t0, 2)}


def _pool(jobs: int):
    return cf.ProcessPoolExecutor(max_workers=jobs, mp_context=multiprocessing.get_context("spawn"))


def _run_parallel(fn, items: list, jobs: int, label: str, verbose: bool) -> list:
    results, t0, last = [], time.time(), 0.0
    if not items:
        return results
    if jobs <= 1:
        it = map(fn, items)
        ex = None
    else:
        ex = _pool(jobs)
        it = ex.map(fn, items, chunksize=1 if len(items) < 400 else 4)
    try:
        for k, r in enumerate(it, 1):
            results.append(r)
            if verbose and (time.time() - last > 10 or k == len(items)):
                last = time.time()
                print(f"  {label}: {k}/{len(items)} ({time.time() - t0:.0f}s)", file=sys.stderr, flush=True)
    finally:
        if ex is not None:
            ex.shutdown()
    return results


# ---------------------------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------------------------

def build(sources: list[Source] | None = None, index_dir: os.PathLike | str = INDEX_DIR, jobs: int = 8,
          ocr: bool = True, force: bool = False, verbose: bool = True, prune: bool | None = None,
          repo_root: os.PathLike | str = ROOT) -> dict:
    """(Re)index changed sources (default: corpus/upload, corpus/rejected and code repos under
    ``repo_root``). Pruning of vanished files defaults to on for auto-discovery."""
    t0 = time.time()
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    state = load_state(index_dir)
    if state.get("_meta") != _version():
        force = True
        state = {"_meta": _version(), "files": {}}
    if prune is None:
        prune = sources is None
    if sources is None:
        repo_root = Path(repo_root)
        sources = discover_sources([repo_root / "corpus" / "upload", repo_root / "corpus" / "rejected"],
                                   repo_root=repo_root)
    files_state = state.setdefault("files", {})

    todo: list[tuple[Source, str]] = []
    skipped = 0
    for src in sources:
        try:
            sha = fingerprint(src)
        except Exception as exc:
            files_state[src.rel] = {"sha1": None, "error": f"fingerprint failed: {exc}", "units": 0,
                                    "index": index_file_name(src.rel), "kind": src.kind, "ocr": ocr}
            continue
        ent = files_state.get(src.rel)
        fresh = (not force and ent and ent.get("sha1") == sha and not ent.get("error")
                 and (ent.get("ocr") or not ocr) and (index_dir / ent.get("index", "")).exists())
        if fresh:
            skipped += 1
        else:
            todo.append((src, sha))

    ocr_errors: list[str] = []
    n_ocr = 0
    if ocr and todo:
        ocr_work = []
        for src, _ in todo:
            if src.kind == "file":
                ocr_work.extend(X.ocr_jobs(src.path))
        n_ocr = len(ocr_work)
        if verbose and ocr_work:
            print(f"OCR: {len(ocr_work)} pages/images to recognise with {jobs} processes", file=sys.stderr)
        for job, err in _run_parallel(X.run_ocr_job, ocr_work, jobs, "ocr", verbose):
            if err:
                ocr_errors.append(f"{job}: {err}")

    if verbose and todo:
        print(f"index: {len(todo)} sources to (re)index, {skipped} unchanged", file=sys.stderr)
    results = _run_parallel(_index_one, [(s, str(index_dir), ocr, sha) for s, sha in todo],
                            jobs if len(todo) > 4 else 1, "extract", verbose)
    for r in results:
        files_state[r.pop("rel")] = r

    removed = 0
    if prune:
        live = {s.rel for s in sources}
        for rel in list(files_state):
            if rel not in live:
                ent = files_state.pop(rel)
                f = index_dir / ent.get("index", index_file_name(rel))
                if f.exists():
                    f.unlink()
                removed += 1
    save_state(state, index_dir)
    errors = [f"{rel}: {e['error']}" for rel, e in files_state.items() if e.get("error")]
    stats = {"sources": len(sources), "updated": len(todo), "skipped": skipped, "removed": removed,
             "ocr_jobs": n_ocr, "ocr_errors": ocr_errors, "errors": errors,
             "units": sum(e.get("units", 0) for e in files_state.values()),
             "seconds": round(time.time() - t0, 1)}
    _LOADED.clear()
    return stats


# ---------------------------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------------------------

@dataclass
class _Loaded:
    rel: str
    mtime: int
    units: list
    norm: str
    norm_starts: list
    raw: str
    raw_starts: list


_LOADED: dict[str, _Loaded] = {}
_WS = re.compile(r"\s+")


def raw_normalize(text: str) -> str:
    """NFKC + whitespace collapse, case preserved (used for regex search)."""
    return _WS.sub(" ", unicodedata.normalize("NFKC", text or "")).strip()


def _join(pieces: list[str]) -> tuple[str, list[int]]:
    starts, pos = [], 0
    for p in pieces:
        starts.append(pos)
        pos += len(p) + 1
    return " ".join(pieces), starts


def _load(path: Path, rel: str) -> _Loaded:
    mt = path.stat().st_mtime_ns
    cached = _LOADED.get(rel)
    if cached and cached.mtime == mt:
        return cached
    units = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rec = json.loads(line)
                units.append((rec["locator"], rec["text"]))
    norm, ns = _join([X.normalize(t) for _, t in units])
    raw, rs = _join([raw_normalize(t) for _, t in units])
    L = _Loaded(rel, mt, units, norm, ns, raw, rs)
    _LOADED[rel] = L
    return L


def _selected(rel: str, files: Iterable[str] | None) -> bool:
    if not files:
        return True
    for f in files:
        f = str(f)
        if rel == f or fnmatch.fnmatch(rel, f) or rel.startswith(f.rstrip("/") + "/"):
            return True
    return False


def indexed_files(index_dir: os.PathLike | str = INDEX_DIR, files: Iterable[str] | None = None) -> list[str]:
    """Repo-relative paths present in the index (optionally filtered by globs/prefixes)."""
    st = load_state(Path(index_dir)).get("files", {})
    return sorted(rel for rel in st if _selected(rel, files))


def iter_loaded(index_dir: os.PathLike | str = INDEX_DIR, files: Iterable[str] | None = None) -> Iterator[_Loaded]:
    index_dir = Path(index_dir)
    st = load_state(index_dir).get("files", {})
    for rel in sorted(st):
        if not _selected(rel, files):
            continue
        p = index_dir / st[rel].get("index", index_file_name(rel))
        if p.exists():
            yield _load(p, rel)


def search(pattern: str | re.Pattern, regex: bool = False, files: Iterable[str] | None = None,
           index_dir: os.PathLike | str = INDEX_DIR, flags: int = re.IGNORECASE,
           max_hits: int | None = None, context: int = 60) -> list[dict]:
    """Find a needle (normalised substring, like extract.match) or a regex in the index.

    Plain search runs over normalised text (casefolded, quotes/dashes folded). Regex search
    runs over NFKC + whitespace-collapsed text with case preserved, using ``flags``.
    Units of one file are searched as one stream, so matches spanning units are found;
    each hit reports the unit where the match starts.
    Hit: {file, locator, match, snippet, unit}.
    """
    hits: list[dict] = []
    if regex:
        rx = pattern if isinstance(pattern, re.Pattern) else re.compile(pattern, flags)
    else:
        needle = X.normalize(str(pattern))
        if not needle:
            return hits
    for L in iter_loaded(index_dir, files):
        hay, starts = (L.raw, L.raw_starts) if regex else (L.norm, L.norm_starts)
        if regex:
            spans = ((m.start(), m.end()) for m in rx.finditer(hay) if m.end() > m.start())
        else:
            def _finds(h=hay):
                i = h.find(needle)
                while i >= 0:
                    yield i, i + len(needle)
                    i = h.find(needle, i + 1)
            spans = _finds()
        for s, e in spans:
            ui = max(0, bisect.bisect_right(starts, s) - 1)
            hits.append({"file": L.rel, "locator": L.units[ui][0], "match": hay[s:e],
                         "snippet": hay[max(0, s - context):e + context], "unit": ui})
            if max_hits and len(hits) >= max_hits:
                return hits
    return hits


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build or search the corpus full-text index.")
    ap.add_argument("--search", metavar="PATTERN", help="search the existing index instead of building")
    ap.add_argument("--regex", action="store_true", help="treat --search as a regular expression")
    ap.add_argument("--case-sensitive", action="store_true", help="regex search without IGNORECASE")
    ap.add_argument("--files", nargs="*", help="restrict search to these globs / path prefixes")
    ap.add_argument("--limit", type=int, default=100, help="max hits to print (default 100)")
    ap.add_argument("--build", action="store_true", help="with --search: refresh the index first")
    ap.add_argument("--jobs", type=int, default=8, help="worker processes (default 8)")
    ap.add_argument("--no-ocr", action="store_true", help="index without OCR (images/scans skipped)")
    ap.add_argument("--rebuild", action="store_true", help="ignore the incremental state")
    ap.add_argument("--index-dir", default=str(INDEX_DIR))
    ap.add_argument("--code-repo-root", help="directory holding variant_<x>/ code repos")
    args = ap.parse_args(argv)
    if args.code_repo_root:
        X.set_code_repo_root(args.code_repo_root)
    if not args.search or args.build:
        stats = build(index_dir=args.index_dir, jobs=args.jobs, ocr=not args.no_ocr, force=args.rebuild)
        print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in stats.items()}))
        for e in stats["errors"][:50] + stats["ocr_errors"][:50]:
            print(f"  ERROR {e}", file=sys.stderr)
    if args.search:
        flags = 0 if args.case_sensitive else re.IGNORECASE
        hits = search(args.search, regex=args.regex, files=args.files, index_dir=args.index_dir, flags=flags)
        for h in hits[:args.limit]:
            print(f"{h['file']}\t{json.dumps(h['locator'], ensure_ascii=False)}\t...{h['snippet']}...")
        nfiles = len({h["file"] for h in hits})
        print(f"{len(hits)} hit(s) in {nfiles} file(s)", file=sys.stderr)
        return 0 if hits else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
