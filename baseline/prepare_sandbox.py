#!/usr/bin/env python
"""Build the baseline sandbox: the corpus the product was given, and nothing else.

The baseline agent (a plain agent with file-system tools; see baseline/BASELINE_PROTOCOL.md) works
only inside this folder. The build writes:

    documents/   every accepted upload file from <corpus> (default corpus/upload/**), flattened to
                 file names only, as the product receives them (--keep-folders keeps the folders).
                 Dotfiles and non-accepted extensions are skipped and listed.
    code_repo/   the code repository (default build/code_repo/variant_a): a fresh single-branch
                 clone of its checked-out branch. The working tree is HEAD; .git holds only that
                 branch's history and tags (no remote, no reflogs, no other branches' objects).
                 --no-git-history drops .git; a source without .git is copied as a plain tree.

Corpus files are copied (never linked) and made read-only. Later, baseline/questions_for_agent.py
adds QUESTIONS_ONLY*.md; the agent may write scratch files under _scratch/ and, in prepared mode,
notes under _notes/. Nothing else belongs in the sandbox.

The build ends with a leak check and fails (exit 1) on any of:
  - answer-key strings: "fact_id:", "expected_answer", "must_include", "must_not_include",
    "acceptable_variants", or paths into world/ or manifests/ (world/data/..., manifests/*.facts.yaml),
    in text files, in the XML of Office files, in PDF text, in binary files' raw bytes, and in the code
    repo's whole git history (patches, messages, authors)
  - answer-key file names (*.facts.yaml, questions.yaml, WORLD.md, ...) anywhere, or a world/ or
    manifests/ folder under documents/
  - git refs other than one branch and its tags; a symlink that points outside the sandbox
It prints the file count and size, and writes a manifest beside the sandbox (outside the agent's
view): <out>.manifest.json with every file's sha256, a sandbox digest, the git head, and the agent
python environment.

Usage
  .venv/bin/python -I baseline/prepare_sandbox.py                           # -> build/baseline_sandbox
  .venv/bin/python -I baseline/prepare_sandbox.py --out ~/cs_baseline/sandbox  # outside the repo (preferred)
  .venv/bin/python -I baseline/prepare_sandbox.py --check --mode cold       # before every batch
  .venv/bin/python -I baseline/prepare_sandbox.py --root build/test_baseline   # a test corpus

--check re-verifies an existing sandbox: corpus files unchanged (sha256), no files added to
documents/ or code_repo/, only allowed top-level entries, same git head, and the leak scan again
(including QUESTIONS_ONLY*.md, _scratch/ and _notes/). --mode cold refuses _notes/; --mode prep (before
and right after the preparation session) allows _notes/ but refuses question files; --mode prepared
allows both.

Exit codes: 0 ok; 1 leak or integrity problem; 2 bad inputs or options.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import zipfile

from harness.make_batches import ACCEPTED_EXT

Path = pathlib.Path
MB = 1_000_000

DOCS_DIR = "documents"
CODE_DIR = "code_repo"
SCRATCH_DIR = "_scratch"
NOTES_DIR = "_notes"
QUESTION_GLOBS = ("QUESTIONS_ONLY.md", "QUESTIONS_ONLY_batch_*.md")
SKIP_NAMES = {".DS_Store", "Thumbs.db", "__pycache__", ".git"}

LEAK_PATTERNS = [
    ("fact_id:", re.compile(r"\bfact_id\s*:", re.I)),
    ("expected_answer", re.compile(r"\bexpected_answers?\b", re.I)),
    ("must_include", re.compile(r"\bmust_include\b", re.I)),
    ("must_not_include", re.compile(r"\bmust_not_include\b", re.I)),
    ("acceptable_variants", re.compile(r"\bacceptable_variants\b", re.I)),
    ("path under world/", re.compile(r"(?<![\w.-])world/(?:data/|wb/|worldlib|WORLD\.md|build_world|validate_world)")),
    ("path under manifests/", re.compile(r"(?<![\w.-])manifests/(?:[\w.-]+\.facts\.ya?ml|files\.csv)")),
]
FORBIDDEN_NAMES = ["*.facts.yaml", "*.facts.yml", "questions.yaml", "graph_expectations*.yaml", "placements.yaml",
                   "corpus_plan.yaml", "contradictions.yaml", "worldlib.py", "WORLD.md", "NOTES.local.md",
                   "*.local.md", "*_score.json", "CATEGORIES.md", "WRITING_GUIDE.md"]
FORBIDDEN_DIRS = {"world", "manifests"}
TEXT_MEMBER_RX = re.compile(r"\.(xml|rels|vml|txt|json|html?|md|csv)$", re.I)


class UsageError(Exception):
    """Bad inputs or options; printed without a traceback (exit 2)."""


# ---------------------------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------------------------

def rel(p: Path, base: Path = ROOT) -> str:
    try:
        return Path(p).resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return Path(p).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt_mb(n: int) -> str:
    return f"{n / MB:,.1f} MB"


def git(repo: Path, *args: str, check: bool = True) -> str:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1", LC_ALL="C")
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, env=env, timeout=900)
    if check and r.returncode != 0:
        raise UsageError(f"git {' '.join(args)} failed in {repo}: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r.stdout.decode("utf-8", "replace")


def force_rmtree(path: Path) -> None:
    """rmtree that also removes read-only files and folders (the sandbox makes the corpus read-only)."""
    def onexc(func, p, _exc):
        os.chmod(os.path.dirname(p), 0o755)
        if not os.path.islink(p):
            os.chmod(p, 0o755 if os.path.isdir(p) else 0o644)
        func(p)
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        for dirpath, _, _ in os.walk(path):          # make folders writable first, so files can go
            os.chmod(dirpath, 0o755)
        shutil.rmtree(path, onexc=onexc)


def make_read_only(top: Path, skip: set[str] = frozenset()) -> None:
    """Drop write bits on files and folders under top, top included (folders after their content)."""
    for dirpath, dirnames, filenames in os.walk(top, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if not os.path.islink(p):
                os.chmod(p, stat.S_IMODE(os.lstat(p).st_mode) & ~0o222)
    for dirpath, _, _ in os.walk(top, topdown=False):
        if any(part in skip for part in Path(dirpath).relative_to(top).parts):
            continue
        os.chmod(dirpath, stat.S_IMODE(os.lstat(dirpath).st_mode) & ~0o222)


def walk_files(top: Path, prune_git: bool = True) -> list[Path]:
    """Files under top, sorted; symlinks (to files or folders) are listed, never followed."""
    out = []
    for dirpath, dirnames, filenames in os.walk(top):
        if prune_git:
            dirnames[:] = [d for d in dirnames if d != ".git"]
        links = [d for d in dirnames if os.path.islink(os.path.join(dirpath, d))]
        dirnames[:] = sorted(d for d in dirnames if d not in links)
        for fn in sorted(filenames + links):
            out.append(Path(dirpath) / fn)
    return out


def dir_bytes(top: Path) -> int:
    return sum(p.lstat().st_size for p in walk_files(top, prune_git=False)) if top.exists() else 0


# ---------------------------------------------------------------------------------------------
# leak scan
# ---------------------------------------------------------------------------------------------

def texts_of(path: Path, warnings: list[str]):
    """Yield (where, text) views of a file for the leak scan."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        warnings.append(f"{path}: unreadable ({exc})")
        return
    if data[:4] == b"PK\x03\x04" and zipfile.is_zipfile(path):
        try:
            with zipfile.ZipFile(path) as z:
                for info in z.infolist():
                    if info.is_dir() or info.file_size > 200 * MB:
                        continue
                    raw = z.read(info)
                    if TEXT_MEMBER_RX.search(info.filename) or b"\x00" not in raw[:8192]:
                        txt = raw.decode("utf-8", "ignore")
                        yield info.filename, txt
                        if "<" in txt:
                            yield f"{info.filename} (tags stripped)", re.sub(r"<[^>]+>", "", txt)
        except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
            warnings.append(f"{path}: zip not readable for the leak scan ({exc}); raw bytes scanned")
            yield "raw", data.decode("latin-1")
        return
    if data[:5] == b"%PDF-":
        try:
            import pymupdf  # noqa: PLC0415 (optional: raw bytes are scanned regardless)
            with pymupdf.open(path) as doc:
                for i, page in enumerate(doc):
                    yield f"page {i + 1}", page.get_text()
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{path}: PDF text not extracted for the leak scan ({exc}); raw bytes scanned")
        yield "raw", data.decode("latin-1")
        return
    if b"\x00" in data[:8192]:
        yield "raw (latin-1)", data.decode("latin-1")
        yield "raw (utf-16)", data.decode("utf-16-le", "ignore")
        return
    yield "text", data.decode("utf-8", "replace")


def scan_text(label: str, text: str, hits: list[str]) -> None:
    for name, rx in LEAK_PATTERNS:
        m = rx.search(text)
        if m:
            s = max(0, m.start() - 40)
            ctx = re.sub(r"\s+", " ", text[s:m.end() + 40]).strip()
            hits.append(f"{label}: {name!r} near …{ctx}…")


def forbidden_name(relpath: str) -> str | None:
    name = relpath.rsplit("/", 1)[-1]
    return next((pat for pat in FORBIDDEN_NAMES if fnmatch.fnmatch(name, pat)), None)


def leak_scan(sandbox: Path) -> tuple[list[str], list[str], int]:
    """(problems, warnings, files scanned) over everything in the sandbox, plus git history."""
    problems, warnings = [], []
    files = walk_files(sandbox)
    for p in files:
        r = p.relative_to(sandbox).as_posix()
        parts = r.split("/")
        pat = forbidden_name(r)
        if pat:
            problems.append(f"{r}: answer-key file name ({pat})")
        if parts[0] == DOCS_DIR and any(x in FORBIDDEN_DIRS for x in parts[1:-1]):
            problems.append(f"{r}: file under a world/ or manifests/ folder")
        elif any(x in FORBIDDEN_DIRS for x in parts[:-1]):
            warnings.append(f"{r}: path has a folder named world or manifests (check it is genuine corpus content)")
        if p.is_symlink():
            target = p.resolve()
            if not target.is_relative_to(sandbox.resolve()):
                problems.append(f"{r}: symlink points outside the sandbox ({target})")
            continue
        for where, text in texts_of(p, warnings):
            scan_text(f"{r} [{where}]", text, problems)
    repo = sandbox / CODE_DIR
    if (repo / ".git").is_dir():
        problems += git_problems(repo)
        hist = git(repo, "log", "--all", "-p", "--no-color", "--no-ext-diff",
                   "--format=commit %H%nAuthor: %an <%ae>%nCommitter: %cn <%ce>%n%n%B")
        scan_text(f"{CODE_DIR} [git history]", hist, problems)
        for name in ("config", "description", "packed-refs", "HEAD"):
            f = repo / ".git" / name
            if f.is_file():
                scan_text(f"{CODE_DIR}/.git/{name}", f.read_text("utf-8", "replace"), problems)
    return problems, warnings, len(files)


def git_problems(repo: Path) -> list[str]:
    problems = []
    refs = git(repo, "for-each-ref", "--format=%(refname)").split()
    heads = [r for r in refs if r.startswith("refs/heads/")]
    other = [r for r in refs if not r.startswith(("refs/heads/", "refs/tags/"))]
    if len(heads) != 1:
        problems.append(f"{CODE_DIR}: expected exactly one branch, found {heads or 'none'}")
    if other:
        problems.append(f"{CODE_DIR}: unexpected git refs {other}")
    remotes = git(repo, "remote").split()
    if remotes:
        problems.append(f"{CODE_DIR}: git remotes left in place {remotes}")
    return problems


# ---------------------------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------------------------

def collect_corpus(corpus: Path, keep_folders: bool) -> tuple[list[tuple[Path, str]], list[str], int]:
    """([(source, dest relative to documents/)], skipped non-accepted paths, skipped dotfiles)."""
    picked, skipped, dotfiles, seen = [], [], 0, {}
    for p in sorted(corpus.rglob("*")):
        if not p.is_file():
            continue
        r = p.relative_to(corpus)
        if any(part.startswith(".") or part in SKIP_NAMES for part in r.parts):
            dotfiles += 1
            continue
        if p.suffix.lower() not in ACCEPTED_EXT:
            skipped.append(r.as_posix())
            continue
        dest = r.as_posix() if keep_folders else p.name
        if dest in seen:
            raise UsageError(f"two corpus files would both become documents/{dest}: {seen[dest]} and {r.as_posix()} "
                             "(rename one, or pass --keep-folders)")
        seen[dest] = r.as_posix()
        picked.append((p, dest))
    return picked, skipped, dotfiles


def copy_code(src: Path, dest: Path, keep_history: bool, notes: list[str]) -> dict:
    """Copy the code repo; returns git facts for the manifest."""
    if not (src / ".git").exists():
        notes.append(f"{rel(src)} is not a git repository: copied as a plain tree, no history")
        shutil.copytree(src, dest, symlinks=True, ignore=shutil.ignore_patterns(*SKIP_NAMES))
        return {"source_is_git": False, "history_included": False}
    branch = git(src, "symbolic-ref", "-q", "--short", "HEAD", check=False).strip()
    if not branch:
        raise UsageError(f"{rel(src)} has a detached HEAD; check out the branch the product was given")
    if git(src, "status", "--porcelain", "--untracked-files=no").strip():
        notes.append(f"{rel(src)} has uncommitted changes; the sandbox has HEAD only (what a clone sees)")
    url = src.resolve().as_uri()
    git(dest.parent, "clone", "--quiet", "--single-branch", "--branch", branch, "--no-hardlinks", url, dest.name)
    git(dest, "remote", "remove", "origin")
    shutil.rmtree(dest / ".git" / "logs", ignore_errors=True)
    git(dest, "gc", "--quiet", "--prune=now")
    info = {
        "source_is_git": True,
        "branch": branch,
        "head": git(dest, "rev-parse", "HEAD").strip(),
        "commits": int(git(dest, "rev-list", "--count", "HEAD").strip() or 0),
        "tags": len(git(dest, "tag", "--list").split()),
        "first_commit_date": (git(dest, "log", "--reverse", "--format=%aI").splitlines() or [""])[0],
        "last_commit_date": git(dest, "log", "-1", "--format=%aI").strip(),
        "history_included": keep_history,
    }
    if not keep_history:
        force_rmtree(dest / ".git")
    return info


PY_PROBE = r"""
import importlib, importlib.metadata as md, json, sys
mods = {"docx": "python-docx", "pptx": "python-pptx", "openpyxl": "openpyxl", "pymupdf": "pymupdf",
        "ocrmac": "ocrmac", "PIL": "pillow", "yaml": "pyyaml"}
out = {"python": sys.version.split()[0], "packages": {}, "missing": []}
for mod, dist in mods.items():
    try:
        importlib.import_module(mod)
        out["packages"][dist] = md.version(dist)
    except Exception as exc:
        out["missing"].append(f"{dist} ({type(exc).__name__})")
print(json.dumps(out))
"""


def probe_python(python: Path) -> dict:
    try:
        r = subprocess.run([str(python), "-I", "-c", PY_PROBE], capture_output=True, text=True, timeout=120)
        info = json.loads(r.stdout.strip().splitlines()[-1])
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired) as exc:
        info = {"error": f"{type(exc).__name__}: {exc}", "missing": ["(python not runnable)"]}
    info["path"] = str(python)
    info["tools"] = {t: bool(shutil.which(t)) for t in ("git", "textutil", "unzip")}
    return info


def file_records(sandbox: Path) -> list[dict]:
    recs = []
    for top in (DOCS_DIR, CODE_DIR):
        base = sandbox / top
        if base.exists():
            for p in walk_files(base):
                recs.append({"path": p.relative_to(sandbox).as_posix(), "bytes": p.lstat().st_size,
                             "sha256": "symlink:" + os.readlink(p) if p.is_symlink() else sha256(p)})
    return recs


def digest(records: list[dict], git_info: dict | None) -> str:
    h = hashlib.sha256()
    for r in sorted(records, key=lambda r: r["path"]):
        h.update(f"{r['path']}\t{r['sha256']}\n".encode())
    if git_info and git_info.get("history_included"):
        h.update(f"git\t{git_info.get('head')}\n".encode())
    return h.hexdigest()


def manifest_path(out: Path) -> Path:
    return out.parent / f"{out.name}.manifest.json"


def guard_out(out: Path, inputs: list[Path], force: bool) -> None:
    o = out.resolve()
    for i in inputs:
        i = i.resolve()
        if o == i or o.is_relative_to(i) or i.is_relative_to(o):
            raise UsageError(f"--out {out} overlaps an input folder ({i})")
    if o in (ROOT.resolve(), Path.home().resolve(), Path("/")):
        raise UsageError(f"--out {out} is not a sandbox folder")
    if out.exists() and any(out.iterdir()) and not manifest_path(out).exists() and not force:
        raise UsageError(f"{out} exists, is not empty and has no {manifest_path(out).name} beside it; "
                         "pass --force to replace it")


def build(args) -> int:
    root = Path(args.root).resolve()
    corpus = Path(args.corpus) if args.corpus else root / "corpus" / "upload"
    code = None if args.no_code else (Path(args.code_repo) if args.code_repo else root / "build" / "code_repo" / "variant_a")
    out = Path(args.out).expanduser() if args.out else root / "build" / "baseline_sandbox"
    python = Path(args.python) if args.python else ROOT / ".venv" / "bin" / "python"
    if not corpus.is_dir():
        raise UsageError(f"corpus folder {corpus} not found (generate the corpus first, or pass --corpus/--root)")
    if code is not None and not code.is_dir():
        raise UsageError(f"code repo {code} not found (build it first, pass --code-repo, or --no-code)")
    picked, skipped, dotfiles = collect_corpus(corpus, args.keep_folders)
    if not picked:
        raise UsageError(f"no accepted upload files under {corpus}")
    guard_out(out, [corpus] + ([code] if code else []), args.force)

    notes: list[str] = []
    if out.exists():
        force_rmtree(out)
    manifest_path(out).unlink(missing_ok=True)
    (out / DOCS_DIR).mkdir(parents=True)
    for src, dest in picked:
        d = out / DOCS_DIR / dest
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, d)
    git_info = None
    if code is not None:
        git_info = copy_code(code, out / CODE_DIR, not args.no_git_history, notes)
    make_read_only(out / DOCS_DIR)
    if code is not None:
        make_read_only(out / CODE_DIR, skip={".git"})

    problems, warnings, scanned = leak_scan(out)
    records = file_records(out)
    docs = [r for r in records if r["path"].startswith(DOCS_DIR + "/")]
    code_files = [r for r in records if r["path"].startswith(CODE_DIR + "/")]
    git_bytes = dir_bytes(out / CODE_DIR / ".git")
    total_bytes = sum(r["bytes"] for r in records) + git_bytes
    py = probe_python(python)
    manifest = {
        "tool": "baseline/prepare_sandbox.py", "format": 1,
        "status": "ok" if not problems else "leak_check_failed",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "sandbox": str(out.resolve()),
        "sources": {"root": str(root), "corpus": rel(corpus), "code_repo": rel(code) if code else None},
        "options": {"keep_folders": args.keep_folders, "git_history": bool(code) and not args.no_git_history},
        "counts": {"documents": len(docs), "documents_bytes": sum(r["bytes"] for r in docs),
                   "code_files": len(code_files), "code_bytes": sum(r["bytes"] for r in code_files),
                   "git_bytes": git_bytes, "files": len(records), "bytes": total_bytes},
        "git": git_info, "digest": digest(records, git_info), "python": py,
        "skipped_non_accepted": skipped, "skipped_dotfiles": dotfiles, "notes": notes,
        "leak_check": {"files_scanned": scanned, "problems": problems, "warnings": warnings},
        "files": records,
    }
    manifest_path(out).write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"sandbox {out}")
    print(f"  {DOCS_DIR}/  {len(docs)} files, {fmt_mb(manifest['counts']['documents_bytes'])}"
          + (f"  (skipped {len(skipped)} non-accepted, {dotfiles} dotfiles)" if skipped or dotfiles else ""))
    if git_info is not None:
        hist = (f", .git {fmt_mb(git_bytes)}: {git_info.get('commits')} commits on {git_info.get('branch')}"
                if git_info.get("history_included") else ", no git history")
        print(f"  {CODE_DIR}/  {len(code_files)} files, {fmt_mb(manifest['counts']['code_bytes'])}{hist}")
    print(f"  total  {len(records)} files, {fmt_mb(total_bytes)}; digest {manifest['digest'][:16]}")
    for n in notes:
        print(f"NOTE: {n}")
    if py.get("missing"):
        print(f"WARN: agent python {python} lacks {', '.join(py['missing'])}: the agent cannot read every format")
    for t, ok in py["tools"].items():
        if not ok:
            print(f"WARN: '{t}' not found on PATH")
    for what, path in (("the sandbox", out), ("the agent python", python)):
        if Path(path).expanduser().absolute().is_relative_to(ROOT):
            print(f"WARN: {what} is inside the test repository ({ROOT.name}/); fine for a dry run, but for a real "
                  "run put it outside, where its path names neither the product nor the test "
                  "(BASELINE_PROTOCOL.md, section 2)")
    for w in warnings[:20]:
        print(f"WARN: {w}")
    print(f"manifest {manifest_path(out)}")
    if problems:
        print(f"LEAK CHECK FAILED: {len(problems)} problem(s); do NOT give this sandbox to an agent", file=sys.stderr)
        for p in problems[:30]:
            print(f"  {p}", file=sys.stderr)
        return 1
    print(f"leak check passed: {scanned} files scanned"
          + (", plus the git history" if git_info and git_info.get("history_included") else ""))
    return 0


# ---------------------------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------------------------

def allowed_top(name: str, is_dir: bool, mode: str) -> bool:
    """cold: corpus, scratch, question files. prep: corpus, scratch, _notes/, NO question files (the
    preparation session must not see them). prepared: everything."""
    if is_dir:
        return name in (DOCS_DIR, CODE_DIR, SCRATCH_DIR) or (name == NOTES_DIR and mode in ("prep", "prepared"))
    return mode != "prep" and any(fnmatch.fnmatch(name, g) for g in QUESTION_GLOBS)


def check(args) -> int:
    root = Path(args.root).resolve()
    out = Path(args.out).expanduser() if args.out else root / "build" / "baseline_sandbox"
    mp = manifest_path(out)
    if not out.is_dir() or not mp.is_file():
        raise UsageError(f"no sandbox at {out} (or its manifest {mp.name} is missing): run prepare_sandbox.py first")
    man = json.loads(mp.read_text(encoding="utf-8"))
    problems, warnings = [], []
    if man.get("status") != "ok":
        problems.append(f"the manifest says {man.get('status')!r}: rebuild the sandbox")
    want = {r["path"]: r for r in man.get("files", [])}
    have = {r["path"]: r for r in file_records(out)}
    for p, r in want.items():
        if p not in have:
            problems.append(f"{p}: missing")
        elif have[p]["sha256"] != r["sha256"]:
            problems.append(f"{p}: modified")
    for p in sorted(set(have) - set(want)):
        problems.append(f"{p}: added to the corpus folders")
    for entry in sorted(out.iterdir()):
        if not allowed_top(entry.name, entry.is_dir(), args.mode):
            problems.append(f"{entry.name}{'/' if entry.is_dir() else ''}: not allowed at the sandbox top level "
                            f"(mode {args.mode})")
    scratch = out / SCRATCH_DIR
    if scratch.is_dir() and any(scratch.iterdir()):
        warnings.append(f"{SCRATCH_DIR}/ is not empty: wipe it before the next batch (rm -rf {scratch})")
    g = man.get("git") or {}
    repo = out / CODE_DIR
    if g.get("history_included"):
        if not (repo / ".git").is_dir():
            problems.append(f"{CODE_DIR}/.git: missing")
        else:
            head = git(repo, "rev-parse", "HEAD", check=False).strip()
            if head != g.get("head"):
                problems.append(f"{CODE_DIR}: HEAD is {head[:12] or '?'}, manifest says {str(g.get('head'))[:12]}")
    elif (repo / ".git").exists():
        problems.append(f"{CODE_DIR}/.git exists but the sandbox was built without history")
    leaks, leak_warnings, scanned = leak_scan(out)
    problems += leaks
    warnings += leak_warnings
    for w in warnings[:20]:
        print(f"WARN: {w}")
    if problems:
        print(f"CHECK FAILED ({out}, mode {args.mode}): {len(problems)} problem(s)", file=sys.stderr)
        for p in problems[:40]:
            print(f"  {p}", file=sys.stderr)
        return 1
    print(f"check passed ({out}, mode {args.mode}): {len(want)} corpus files unchanged, {scanned} files leak-scanned, "
          f"digest {man.get('digest', '')[:16]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT), help="tree holding corpus/upload and build/code_repo (default: repo root)")
    ap.add_argument("--corpus", help="upload corpus folder (default: <root>/corpus/upload)")
    ap.add_argument("--code-repo", help="code repository to include (default: <root>/build/code_repo/variant_a)")
    ap.add_argument("--no-code", action="store_true", help="no code repository in the sandbox")
    ap.add_argument("--no-git-history", action="store_true", help="working tree only, without .git")
    ap.add_argument("--keep-folders", action="store_true", help="keep corpus sub-folders instead of flattening")
    ap.add_argument("--out", help="sandbox folder (default: <root>/build/baseline_sandbox); replaced on rebuild")
    ap.add_argument("--python", help="the agent's python, probed for the document libraries "
                                     "(default: the repo's .venv/bin/python)")
    ap.add_argument("--force", action="store_true", help="replace --out even without a manifest beside it")
    ap.add_argument("--check", action="store_true", help="verify an existing sandbox instead of building")
    ap.add_argument("--mode", choices=["cold", "prep", "prepared"], default="cold",
                    help="with --check: cold = no _notes/; prep = before/while the preparation session: _notes/ "
                         "allowed, question files refused; prepared = _notes/ and question files allowed "
                         "(default: cold)")
    args = ap.parse_args(argv)
    try:
        return check(args) if args.check else build(args)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
