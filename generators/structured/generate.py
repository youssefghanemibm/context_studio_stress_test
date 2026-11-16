#!/usr/bin/env python3
"""Family entry point: runs every gen_*.py part in this folder (parts may run in parallel).

Copy this file to generators/<family>/generate.py when a family is split into parts.
Each part writes only its own file ids and its own manifests/<family>.<part>.facts.yaml.
"""
import concurrent.futures as cf
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def run(part: pathlib.Path):
    p = subprocess.run([sys.executable, "-I", str(part), *sys.argv[1:]], cwd=ROOT,
                       capture_output=True, text=True)
    return part.name, p.returncode, p.stdout + p.stderr


def main() -> int:
    parts = sorted(HERE.glob("gen_*.py"))
    if not parts:
        print(f"no gen_*.py parts in {HERE}")
        return 1
    rc_all = 0
    with cf.ThreadPoolExecutor(max_workers=len(parts)) as pool:
        for name, rc, out in pool.map(run, parts):
            print(out.rstrip())
            print(f"[{HERE.name}/{name}] {'ok' if rc == 0 else f'FAILED exit {rc}'}")
            rc_all = rc_all or rc
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
