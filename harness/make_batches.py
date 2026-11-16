#!/usr/bin/env python
"""Split the upload corpus into upload batches, in two different orders.

The product is loaded by hand, one batch at a time, through a browser upload dialog. Loading
the same files in two different orders, into two separate contexts, shows whether what the
knowledge-graph tool builds (and later answers) depends on upload order and on which files
were ingested together.

    Order A  "by family": the family folders long_docs, visuals, structured, text, guardrail
             (then any other folder, then loose files), each sorted by file id, packed into
             batches greedily in that order.
    Order B  "interleaved": a seeded shuffle that mixes the families, packed first-fit-decreasing
             on size (sizes compared in whole MB, so similar-sized files keep their shuffled,
             family-mixed order), then the order of the batches is shuffled too.

The two orders must differ in which files share a batch; the script reports the share of
co-batched file pairs the two orders have in common.

Batch limits are configurable defaults, not facts about any product:
    --max-files 30     files per batch
    --max-mb 100       MB per batch, decimal (1 MB = 1,000,000 bytes)
    --headroom-mb 2    safety margin: batches are packed to max-mb minus headroom-mb
A single file larger than one batch is an error.

Usage:
    .venv/bin/python -I harness/make_batches.py                # write the CSVs and BATCHES.md
    .venv/bin/python -I harness/make_batches.py --materialize  # ... and one folder per batch
    .venv/bin/python -I harness/make_batches.py --check        # validate the existing CSVs
    .venv/bin/python -I harness/make_batches.py --root build/test_batches   # another corpus root

Inputs: <root>/corpus/upload/** (accepted upload extensions only; dotfiles skipped).
Outputs, under <root>/batches/:
    order_A.csv, order_B.csv   columns order,batch,seq,file,family,ext,bytes: one row per file in
                               upload order; batch is 1-based; seq is the position inside the
                               batch; file is the root-relative POSIX path
    BATCHES.md                 per-order batch tables and the upload procedure
    materialized/order_<X>/batch_<NN>/   (--materialize) hard links, or copies when linking
                               fails, so a person can drag one folder per batch into the upload
                               dialog; gitignored; re-run after regenerating the corpus

Output is deterministic: same corpus and options, same files.
Exit codes: 0 ok; 1 --check found problems; 2 bad options or a file larger than one batch.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import collections
import csv
import dataclasses
import hashlib
import itertools
import os
import random
import re
import shutil

Path = pathlib.Path

ACCEPTED_EXT = (".docx", ".doc", ".md", ".xlsx", ".txt", ".json", ".csv", ".pdf", ".pptx", ".xml",
                ".html", ".yaml", ".yml")
FAMILY_ORDER = ("long_docs", "visuals", "structured", "text", "guardrail")
ORDER_B_SEED = "upload-order-B/v1"   # change only on purpose: it changes every order-B batch
MAX_SALTS = 64                        # alternative order-B seeds tried if B would co-batch like A
CSV_COLUMNS = ["order", "batch", "seq", "file", "family", "ext", "bytes"]
MB = 1_000_000
FILE_ID_RE = re.compile(r"^([A-Za-z]{2}\d{3})(?=[_.]|$)")


@dataclasses.dataclass(frozen=True)
class UploadFile:
    path: str     # root-relative POSIX path, e.g. corpus/upload/long_docs/LD001_x.docx
    family: str   # first folder under corpus/upload ("" for loose files)
    ext: str
    size: int
    file_id: str

    @property
    def name(self) -> str:
        return self.path.rsplit("/", 1)[-1]


@dataclasses.dataclass
class Plan:
    a: list[list[UploadFile]]
    b: list[list[UploadFile]]
    salt: int
    pairs_a: set
    pairs_b: set
    notes: list[str]


# ---------------------------------------------------------------------------------------------
# Corpus scan
# ---------------------------------------------------------------------------------------------

def scan(root: Path) -> tuple[list[UploadFile], list[str], int]:
    """(accepted files, skipped non-accepted paths, number of skipped dotfiles)."""
    upload = root / "corpus" / "upload"
    files: list[UploadFile] = []
    skipped: list[str] = []
    dotfiles = 0
    if not upload.is_dir():
        return files, skipped, dotfiles
    for p in sorted(upload.rglob("*")):
        if not p.is_file():
            continue
        if p.name.startswith("."):
            dotfiles += 1
            continue
        rel = p.relative_to(root).as_posix()
        ext = p.suffix.lower()
        if ext not in ACCEPTED_EXT:
            skipped.append(rel)
            continue
        parts = p.relative_to(upload).parts
        m = FILE_ID_RE.match(p.name)
        files.append(UploadFile(path=rel, family=parts[0] if len(parts) > 1 else "", ext=ext,
                                size=p.stat().st_size, file_id=m.group(1).upper() if m else p.stem))
    return files, skipped, dotfiles


def family_rank(family: str) -> tuple:
    if family in FAMILY_ORDER:
        return (0, FAMILY_ORDER.index(family), "")
    return (1, 0, family) if family else (2, 0, "")


# ---------------------------------------------------------------------------------------------
# Packing
# ---------------------------------------------------------------------------------------------

def pack_greedy(seq: list[UploadFile], max_files: int, cap: int) -> list[list[UploadFile]]:
    """Fill batches in sequence; open a new one when the next file would break a limit."""
    batches: list[list[UploadFile]] = []
    cur: list[UploadFile] = []
    cur_bytes = 0
    for f in seq:
        if cur and (len(cur) >= max_files or cur_bytes + f.size > cap):
            batches.append(cur)
            cur, cur_bytes = [], 0
        cur.append(f)
        cur_bytes += f.size
    if cur:
        batches.append(cur)
    return batches


def pack_ffd(seq: list[UploadFile], max_files: int, cap: int) -> list[list[UploadFile]]:
    """First-fit-decreasing on size (whole MB; ties keep ``seq`` order). Batches keep ``seq`` order inside."""
    pos = {f.path: i for i, f in enumerate(seq)}
    bins: list[list] = []   # [files, bytes]
    for f in sorted(seq, key=lambda f: (-(f.size // MB), pos[f.path])):
        for b in bins:
            if len(b[0]) < max_files and b[1] + f.size <= cap:
                b[0].append(f)
                b[1] += f.size
                break
        else:
            bins.append([[f], f.size])
    return [sorted(b[0], key=lambda f: pos[f.path]) for b in bins]


def order_a(files: list[UploadFile], max_files: int, cap: int) -> list[list[UploadFile]]:
    seq = sorted(files, key=lambda f: (family_rank(f.family), f.file_id.casefold(), f.path))
    return pack_greedy(seq, max_files, cap)


def order_b(files: list[UploadFile], max_files: int, cap: int, salt: int = 0) -> list[list[UploadFile]]:
    rng = random.Random(f"{ORDER_B_SEED}#{salt}")   # str seeds are stable across runs and platforms
    seq = sorted(files, key=lambda f: f.path)
    rng.shuffle(seq)
    batches = pack_ffd(seq, max_files, cap)
    rng.shuffle(batches)
    return batches


def co_batched_pairs(batches: list[list[UploadFile]]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for b in batches:
        pairs.update(itertools.combinations(sorted(f.path for f in b), 2))
    return pairs


def flat(batches: list[list[UploadFile]]) -> list[str]:
    return [f.path for b in batches for f in b]


def make_plan(files: list[UploadFile], max_files: int, cap: int) -> Plan:
    a = order_a(files, max_files, cap)
    pa, seq_a = co_batched_pairs(a), flat(a)
    notes: list[str] = []
    found = None
    for salt in range(MAX_SALTS if len(files) >= 2 else 0):
        b = order_b(files, max_files, cap, salt)
        pb = co_batched_pairs(b)
        if flat(b) != seq_a and (pa != pb or (len(a) == 1 and len(b) == 1)):
            found = (salt, b, pb)
            break
    if found is None:   # no salt helps (tiny corpus): keep the base seed
        b = order_b(files, max_files, cap, 0)
        found = (0, b, co_batched_pairs(b))
    salt, b, pb = found
    if salt:
        notes.append(f"order B uses seed salt {salt}: lower salts co-batched the files exactly like order A")
    if len(files) < 2:
        notes.append("fewer than 2 files: both orders are identical (the verifier's batch check will fail)")
    elif len(a) == 1 and len(b) == 1:
        notes.append("the whole corpus fits in one batch: both orders put every file together, "
                     "so batch-composition effects cannot be tested")
    elif pa == pb:
        notes.append(f"order B still co-batches the files exactly like order A after {MAX_SALTS} seeds")
    return Plan(a=a, b=b, salt=salt, pairs_a=pa, pairs_b=pb, notes=notes)


def overlap_stats(pa: set, pb: set) -> dict:
    both, union = len(pa & pb), len(pa | pb)
    return {"both": both, "union": union, "a": len(pa), "b": len(pb),
            "jaccard_pct": 100.0 * both / union if union else None,
            "of_a_pct": 100.0 * both / len(pa) if pa else None}


# ---------------------------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------------------------

def fmt_mb(n: int) -> str:
    return "0.0" if n == 0 else ("<0.1" if n < MB / 20 else f"{n / MB:.1f}")


def fmt_pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.1f}%"


def mix(values: list[str]) -> str:
    c = collections.Counter(values)
    return ", ".join(f"{k} {n}" for k, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def write_csv(path: Path, order: str, batches: list[list[UploadFile]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(CSV_COLUMNS)
        for bi, batch in enumerate(batches, 1):
            for si, f in enumerate(batch, 1):
                w.writerow([order, bi, si, f.path, f.family, f.ext, f.size])


def batch_folder_names(batches: list[list[UploadFile]]) -> list[tuple[str, list[tuple[str, UploadFile]]]]:
    """[(batch folder name, [(file name inside it, file)])]; colliding names get a family prefix."""
    width = max(2, len(str(len(batches))))
    out = []
    for bi, batch in enumerate(batches, 1):
        used: set[str] = set()
        entries = []
        for f in batch:
            name = f.name
            if name in used:
                name = f"{f.family or 'root'}__{name}"
            used.add(name)
            entries.append((name, f))
        out.append((f"batch_{bi:0{width}d}", entries))
    return out


def render_md(plan: Plan, files: list[UploadFile], max_files: int, max_mb: float, headroom_mb: float,
              cap: int) -> str:
    total = sum(f.size for f in files)
    ov = overlap_stats(plan.pairs_a, plan.pairs_b)
    seed = f"`{ORDER_B_SEED}`" + (f", salt {plan.salt}" if plan.salt else "")
    lines = [
        "# Upload batches",
        "",
        f"Generated by `harness/make_batches.py` from `corpus/upload/`: {len(files)} files, {fmt_mb(total)} MB. "
        "Don't edit by hand; re-run the script after the corpus changes.",
        "",
        f"Limits per batch: at most {max_files} files and {max_mb:g} MB (decimal: 1 MB = 1,000,000 bytes), "
        f"packed to {cap / MB:g} MB to leave {headroom_mb:g} MB of headroom. "
        "These are the script's configurable defaults (`--max-files`, `--max-mb`, `--headroom-mb`).",
        "",
        "| Order | How it is built | Batches | Files | MB |",
        "|---|---|---|---|---|",
        f"| A | by family: {' → '.join(FAMILY_ORDER)}, then file id; packed greedily | {len(plan.a)} | "
        f"{len(files)} | {fmt_mb(total)} |",
        f"| B | interleaved: seeded shuffle (seed {seed}), first-fit-decreasing on size, batch order "
        f"shuffled | {len(plan.b)} | {len(files)} | {fmt_mb(total)} |",
        "",
        f"**Co-batching overlap: {fmt_pct(ov['jaccard_pct'])}.** Of the {ov['union']} file pairs that share a "
        f"batch in either order, {ov['both']} share one in both ({fmt_pct(ov['of_a_pct'])} of order A's "
        f"{ov['a']} pairs).",
        "",
    ]
    for n in plan.notes:
        lines.append(f"- Note: {n}")
    if plan.notes:
        lines.append("")
    lines += [
        "## How to upload",
        "",
        "1. Run `.venv/bin/python -I harness/make_batches.py --materialize`. It creates "
        "`batches/materialized/order_A/batch_01/` and so on: one folder per batch, holding hard links to the "
        "corpus files.",
        "2. Use a new, empty context for each order. Upload order A's batches into one context and order B's "
        "into another, in batch-number order.",
        "3. For each batch, drag the batch folder's files into the product's upload dialog. Wait until "
        "ingestion of the whole batch has finished before you start the next batch.",
        "4. Record each batch's start and finish time, and any file that failed or was flagged.",
        "",
    ]
    for label, batches in (("A", plan.a), ("B", plan.b)):
        names = batch_folder_names(batches)
        lines += [f"## Order {label}", "",
                  "| Batch | Folder | Files | MB | Extensions | Families |",
                  "|---|---|---|---|---|---|"]
        for bi, (batch, (folder, _)) in enumerate(zip(batches, names), 1):
            lines.append(f"| {bi} | `{folder}` | {len(batch)} | {fmt_mb(sum(f.size for f in batch))} | "
                         f"{mix([f.ext for f in batch])} | {mix([f.family or '(root)' for f in batch])} |")
        lines.append("")
    return "\n".join(lines)


def materialize(root: Path, order: str, batches: list[list[UploadFile]]) -> tuple[Path, int, int]:
    base = root / "batches" / "materialized" / f"order_{order}"
    safe_parent = (root / "batches" / "materialized").resolve()
    if base.exists():
        if base.resolve().parent != safe_parent:
            raise SystemExit(f"refusing to delete {base}: not inside {safe_parent}")
        shutil.rmtree(base)
    links = copies = 0
    for folder, entries in batch_folder_names(batches):
        d = base / folder
        d.mkdir(parents=True)
        for name, f in entries:
            src, dst = root / f.path, d / name
            try:
                os.link(src, dst)
                links += 1
            except OSError:
                shutil.copy2(src, dst)
                copies += 1
    return base, links, copies


# ---------------------------------------------------------------------------------------------
# --check
# ---------------------------------------------------------------------------------------------

def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_order_csv(path: Path, order: str, current: dict[str, UploadFile], root: Path,
                   problems: list[str]) -> list[list[UploadFile]] | None:
    name = f"batches/{path.name}"
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rdr = csv.DictReader(fh)
        if [c.strip() for c in (rdr.fieldnames or [])] != CSV_COLUMNS:
            problems.append(f"{name}: columns are {rdr.fieldnames}, expected {CSV_COLUMNS}")
            return None
        rows = list(rdr)
    batches: list[list[UploadFile]] = []
    seen: collections.Counter = collections.Counter()
    cur_b = cur_s = 0
    for k, r in enumerate(rows, 2):
        where = f"{name} line {k}"
        try:
            bi, si, nbytes = int(r["batch"]), int(r["seq"]), int(r["bytes"])
        except (TypeError, ValueError):
            problems.append(f"{where}: batch, seq and bytes must be integers")
            continue
        if not 1 <= bi <= len(rows):
            problems.append(f"{where}: batch {bi} out of range")
            continue
        if (r["order"] or "").strip() != order:
            problems.append(f"{where}: order is {r['order']!r}, expected {order!r}")
        if not ((bi == cur_b and si == cur_s + 1) or (bi == cur_b + 1 and si == 1)):
            problems.append(f"{where}: batch {bi} seq {si} after batch {cur_b} seq {cur_s} (rows must be in "
                            "upload order, batches numbered from 1, seq from 1 inside each batch)")
        cur_b, cur_s = bi, si
        p = r["file"].strip()
        seen[p] += 1
        f = current.get(p)
        if f is None:
            fp = root / p
            why = ("not in the corpus" if not fp.exists() else
                   "not an accepted upload type or a dotfile")
            problems.append(f"{where}: {p} is {why}")
            f = UploadFile(path=p, family=r["family"], ext=r["ext"], size=nbytes, file_id="")
        else:
            if nbytes != f.size:
                problems.append(f"{where}: {p} is {f.size} bytes on disk, {nbytes} in the CSV (stale: re-run)")
            if r["family"] != f.family or r["ext"] != f.ext:
                problems.append(f"{where}: family/ext columns do not match {p}")
        while len(batches) < bi:
            batches.append([])
        batches[bi - 1].append(f)
    for p, n in seen.items():
        if n > 1:
            problems.append(f"{name}: {p} listed {n} times")
    missing = sorted(set(current) - set(seen))
    if missing:
        problems.append(f"{name}: {len(missing)} upload file(s) missing, e.g. {missing[:5]}")
    return [b for b in batches if b]


def check_materialized(root: Path, order: str, batches: list[list[UploadFile]],
                       problems: list[str], info: list[str]) -> None:
    base = root / "batches" / "materialized" / f"order_{order}"
    if not base.exists():
        info.append(f"order {order}: not materialised (run with --materialize to create the batch folders)")
        return
    expected = {folder: dict(entries) for folder, entries in batch_folder_names(batches)}
    actual = {d.name for d in base.iterdir() if d.is_dir()}
    stale = []
    for folder in sorted(actual - set(expected)):
        stale.append(f"extra folder {folder}")
    for folder, entries in expected.items():
        d = base / folder
        have = {p.name for p in d.iterdir() if p.is_file()} if d.is_dir() else set()
        for name in sorted(have - set(entries)):
            stale.append(f"{folder}/{name} is not in this batch")
        for name, f in entries.items():
            dst, src = d / name, root / f.path
            if name not in have:
                stale.append(f"{folder}/{name} missing")
            elif not src.exists():
                continue
            else:
                ds, ss = dst.stat(), src.stat()
                same = (ds.st_ino == ss.st_ino and ds.st_dev == ss.st_dev) or (
                    ds.st_size == ss.st_size and sha1(dst) == sha1(src))
                if not same:
                    stale.append(f"{folder}/{name} differs from {f.path}")
    if stale:
        problems.append(f"batches/materialized/order_{order} is stale ({len(stale)} issue(s), e.g. "
                        f"{stale[:3]}): re-run with --materialize")
    else:
        info.append(f"order {order}: materialised folders match the CSV")


def run_check(root: Path, files: list[UploadFile], max_files: int, max_mb: float, cap: int) -> int:
    problems: list[str] = []
    warnings: list[str] = []
    info: list[str] = []
    current = {f.path: f for f in files}
    paths = {o: root / "batches" / f"order_{o}.csv" for o in "AB"}
    if not any(p.exists() for p in paths.values()):
        if files:
            problems.append("batches/order_A.csv and order_B.csv not found: run harness/make_batches.py")
        else:
            info.append("no upload files and no batch CSVs: nothing to check")
        return report_check(problems, warnings, info)
    loaded: dict[str, list[list[UploadFile]]] = {}
    for o, p in paths.items():
        if not p.exists():
            problems.append(f"batches/{p.name} not found")
            continue
        batches = read_order_csv(p, o, current, root, problems)
        if batches is None:
            continue
        loaded[o] = batches
        for bi, b in enumerate(batches, 1):
            size = sum(f.size for f in b)
            if len(b) > max_files:
                problems.append(f"order {o} batch {bi}: {len(b)} files (max {max_files})")
            if size > max_mb * MB:
                problems.append(f"order {o} batch {bi}: {size / MB:.1f} MB (max {max_mb:g} MB)")
            elif size > cap:
                warnings.append(f"order {o} batch {bi}: {size / MB:.1f} MB is inside the headroom "
                                f"(packing target {cap / MB:g} MB)")
        info.append(f"order {o}: {sum(len(b) for b in batches)} files in {len(batches)} batches")
    if len(loaded) == 2:
        a, b = loaded["A"], loaded["B"]
        if set(flat(a)) != set(flat(b)):
            problems.append(f"orders differ in file set: {len(set(flat(a)) ^ set(flat(b)))} file(s) in only one")
        elif flat(a) == flat(b) and len(flat(a)) > 1:
            problems.append("order_A and order_B list the files in the same order")
        pa, pb = co_batched_pairs(a), co_batched_pairs(b)
        ov = overlap_stats(pa, pb)
        if pa == pb and not (len(a) == 1 and len(b) == 1) and pa:
            problems.append("order A and order B put exactly the same files together in batches")
        info.append(f"co-batching overlap {fmt_pct(ov['jaccard_pct'])} ({ov['both']} of {ov['union']} pairs)")
        fresh = make_plan(files, max_files, cap) if files else None
        if fresh and (flat(fresh.a) != flat(a) or flat(fresh.b) != flat(b)
                      or [len(x) for x in fresh.a] != [len(x) for x in a]
                      or [len(x) for x in fresh.b] != [len(x) for x in b]):
            warnings.append("the CSVs differ from what make_batches.py would write now with these limits "
                            "(corpus or options changed?): re-run it to refresh")
    for o, batches in loaded.items():
        check_materialized(root, o, batches, problems, info)
    return report_check(problems, warnings, info)


def report_check(problems: list[str], warnings: list[str], info: list[str]) -> int:
    for m in info:
        print(f"  ok    {m}")
    for m in warnings:
        print(f"  WARN  {m}")
    for m in problems:
        print(f"  FAIL  {m}")
    print("FAILED" if problems else "OK", f"({len(problems)} problem(s), {len(warnings)} warning(s))")
    return 1 if problems else 0


# ---------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT),
                    help="corpus root holding corpus/upload/ and batches/ (default: the repo)")
    ap.add_argument("--max-files", type=int, default=30, help="max files per batch (default 30)")
    ap.add_argument("--max-mb", type=float, default=100, help="max decimal MB per batch (default 100)")
    ap.add_argument("--headroom-mb", type=float, default=2,
                    help="safety margin: pack batches to max-mb minus this (default 2)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--materialize", action="store_true",
                      help="also create batches/materialized/order_<X>/batch_<NN>/ with hard links (copy fallback)")
    mode.add_argument("--check", action="store_true",
                      help="validate the existing CSVs against the corpus and limits; exit 1 on problems")
    args = ap.parse_args(argv)

    if args.max_files < 1:
        ap.error("--max-files must be at least 1")
    if not 0 <= args.headroom_mb < args.max_mb:
        ap.error("need 0 <= --headroom-mb < --max-mb")
    cap = int(round((args.max_mb - args.headroom_mb) * MB))
    root = Path(args.root).resolve()

    files, skipped, dotfiles = scan(root)
    if skipped:
        print(f"WARN: skipped {len(skipped)} file(s) with a non-accepted extension under corpus/upload "
              f"(the verifier will flag them), e.g. {skipped[:5]}", file=sys.stderr)

    if args.check:
        return run_check(root, files, args.max_files, args.max_mb, cap)

    too_big = [f for f in files if f.size > cap]
    if too_big:
        for f in too_big:
            print(f"ERROR: {f.path} is {f.size:,} bytes, larger than one batch ({cap:,} bytes = "
                  f"--max-mb {args.max_mb:g} minus --headroom-mb {args.headroom_mb:g}, decimal MB)",
                  file=sys.stderr)
        return 2
    out_dir = root / "batches"
    if not files:
        stale = [p.name for p in (out_dir / "order_A.csv", out_dir / "order_B.csv") if p.exists()]
        print("No accepted files under corpus/upload/: nothing to batch."
              + (f" Existing {', '.join(stale)} left untouched." if stale else ""))
        return 0

    plan = make_plan(files, args.max_files, cap)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "order_A.csv", "A", plan.a)
    write_csv(out_dir / "order_B.csv", "B", plan.b)
    (out_dir / "BATCHES.md").write_text(
        render_md(plan, files, args.max_files, args.max_mb, args.headroom_mb, cap), encoding="utf-8")

    ov = overlap_stats(plan.pairs_a, plan.pairs_b)
    total = sum(f.size for f in files)
    print(f"{len(files)} files, {fmt_mb(total)} MB"
          + (f" ({dotfiles} dotfile(s) skipped)" if dotfiles else ""))
    for label, batches in (("A", plan.a), ("B", plan.b)):
        print(f"order {label}: {len(batches)} batches, max {max(len(b) for b in batches)} files and "
              f"{fmt_mb(max(sum(f.size for f in b) for b in batches))} MB per batch")
    print(f"co-batching overlap: {fmt_pct(ov['jaccard_pct'])} of co-batched pairs shared "
          f"({ov['both']} of {ov['union']})")
    for n in plan.notes:
        print(f"NOTE: {n}")
    rel = out_dir.relative_to(root).as_posix()
    print(f"wrote {rel}/order_A.csv, {rel}/order_B.csv, {rel}/BATCHES.md")
    if args.materialize:
        for label, batches in (("A", plan.a), ("B", plan.b)):
            base, links, copies = materialize(root, label, batches)
            print(f"materialised {base.relative_to(root).as_posix()}/: {len(batches)} folders, "
                  f"{links} hard links, {copies} copies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
