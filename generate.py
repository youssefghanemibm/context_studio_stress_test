#!/usr/bin/env python3
"""Rebuild the whole suite from the world model.

    .venv/bin/python -I generate.py                 # everything
    .venv/bin/python -I generate.py --skip-verify   # generate only
    .venv/bin/python -I generate.py --only visuals,text
    .venv/bin/python -I generate.py --jobs 4

Order: world model -> family generators (in parallel) -> code repos -> batches -> index -> verify.
Every step is deterministic: same inputs, same corpus, same answer key.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
PY = [sys.executable, "-I"]

FAMILIES = ["long_docs", "visuals", "structured", "text", "guardrail_rejected"]
CODE_ASSEMBLER = ROOT / "generators" / "code_repo" / "assemble.py"


def run(cmd: list[str], label: str) -> tuple[str, int, float, str]:
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    return label, proc.returncode, time.time() - t0, out


def step(cmd: list[str], label: str) -> None:
    label, rc, dt, out = run(cmd, label)
    status = "ok" if rc == 0 else f"FAILED (exit {rc})"
    print(f"[{label}] {status} in {dt:.0f}s")
    if rc != 0:
        print(out[-4000:])
        sys.exit(rc)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma-separated families to regenerate (default: all)")
    ap.add_argument("--jobs", type=int, default=3, help="family generators to run in parallel")
    ap.add_argument("--skip-world", action="store_true")
    ap.add_argument("--skip-code", action="store_true")
    ap.add_argument("--skip-verify", action="store_true")
    ap.add_argument("--no-ocr", action="store_true", help="skip OCR in index/verify (faster, weaker)")
    args = ap.parse_args()

    if not args.skip_world:
        step(PY + ["world/build_world.py"], "world:build")
        step(PY + ["world/validate_world.py"], "world:validate")

    families = args.only.split(",") if args.only else FAMILIES
    scripts = []
    for fam in families:
        script = ROOT / "generators" / fam / "generate.py"
        if script.exists():
            scripts.append((fam, script))
        else:
            print(f"[{fam}] no generator at {script.relative_to(ROOT)}; skipped")

    with cf.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futs = [pool.submit(run, PY + [str(s)], f"gen:{fam}") for fam, s in scripts]
        failed = False
        for fut in cf.as_completed(futs):
            label, rc, dt, out = fut.result()
            print(f"[{label}] {'ok' if rc == 0 else f'FAILED (exit {rc})'} in {dt:.0f}s")
            if rc != 0:
                failed = True
                print(out[-4000:])
        if failed:
            sys.exit(1)

    if not args.skip_code and not args.only and CODE_ASSEMBLER.exists():
        step(PY + [str(CODE_ASSEMBLER)], "code:assemble")

    make_batches = ROOT / "harness" / "make_batches.py"
    if make_batches.exists():
        step(PY + [str(make_batches)], "batches")

    if args.skip_verify:
        return
    idx = PY + ["harness/build_index.py"] + (["--no-ocr"] if args.no_ocr else [])
    step(idx, "index")
    ver = PY + ["harness/verify_corpus.py", "--json", "build/verify_report.json"] + (["--no-ocr"] if args.no_ocr else [])
    step(ver, "verify")


if __name__ == "__main__":
    main()
