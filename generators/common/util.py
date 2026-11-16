"""Shared helpers for every generator family (see docs/CONVENTIONS.md).

Import from any script after putting the repo root on sys.path:
    from generators.common import util
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import pathlib
import random
import shutil
from typing import Any, Iterable

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
GLOBAL_SEED = "corvane-cs-stress-2026"
FIXED_DT = _dt.datetime(2026, 11, 1, 9, 0, 0)

UPLOAD = ROOT / "corpus" / "upload"
REJECTED = ROOT / "corpus" / "rejected"
MANIFESTS = ROOT / "manifests"
BUILD = ROOT / "build"
SOFFICE = "/opt/homebrew/bin/soffice"

FAMILY_DIRS = {
    "LD": "long_docs",
    "VS": "visuals",
    "ST": "structured",
    "TX": "text",
    "GP": "guardrail",
}

ACCEPTED_EXT = {".docx", ".doc", ".md", ".xlsx", ".txt", ".json", ".csv", ".pdf",
                ".pptx", ".xml", ".html", ".yaml", ".yml"}


def rng(key: str) -> random.Random:
    """Deterministic RNG for a key (use the file id or file id + purpose)."""
    seed = int.from_bytes(hashlib.sha256(f"{GLOBAL_SEED}:{key}".encode()).digest()[:8], "big")
    return random.Random(seed)


def stable_hash(*parts: Any, n: int = 8) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:n]


def font_path(bold: bool = False, mono: bool = False) -> str:
    import matplotlib
    base = pathlib.Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    if mono:
        name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    else:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return str(base / name)


def font(size: int, bold: bool = False, mono: bool = False):
    from PIL import ImageFont
    return ImageFont.truetype(font_path(bold=bold, mono=mono), size)


def family_out(family_dir: str) -> pathlib.Path:
    return UPLOAD / family_dir


def reset_dir(path: pathlib.Path) -> pathlib.Path:
    """Delete and recreate an output directory (only ever call on your own family folder)."""
    path = pathlib.Path(path)
    assert ROOT in path.resolve().parents, f"refusing to reset {path}"
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def rel(path: os.PathLike | str) -> str:
    """Repo-relative POSIX path, as used in manifests and questions."""
    return pathlib.Path(path).resolve().relative_to(ROOT).as_posix()


def write_manifest(family: str, entries: Iterable[dict]) -> pathlib.Path:
    """Write manifests/<family>.facts.yaml with stable ordering and basic validation."""
    entries = list(entries)
    required = {"fact_id", "kind", "statement", "file", "locator", "needle"}
    seen = set()
    for e in entries:
        missing = required - e.keys()
        if missing:
            raise ValueError(f"manifest entry {e.get('fact_id')} missing {missing}")
        if e["fact_id"] in seen:
            raise ValueError(f"duplicate fact_id {e['fact_id']}")
        seen.add(e["fact_id"])
        e.setdefault("exclusive", False)
        e.setdefault("also_in", [])
        e.setdefault("world_ref", None)
    entries.sort(key=lambda e: e["fact_id"])
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    out = MANIFESTS / f"{family}.facts.yaml"
    with open(out, "w", encoding="utf-8") as fh:
        yaml.safe_dump(entries, fh, sort_keys=False, allow_unicode=True, width=120)
    return out


def soffice_convert(src: os.PathLike | str, fmt: str, outdir: os.PathLike | str,
                    profile_key: str = "default", timeout: int = 900) -> pathlib.Path:
    """Convert with LibreOffice using an isolated profile (safe to run in parallel)."""
    import subprocess
    src = pathlib.Path(src)
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    profile = BUILD / "lo_profiles" / profile_key
    profile.mkdir(parents=True, exist_ok=True)
    cmd = [SOFFICE, f"-env:UserInstallation=file://{profile}", "--headless",
           "--convert-to", fmt, "--outdir", str(outdir), str(src)]
    subprocess.run(cmd, check=True, timeout=timeout, capture_output=True)
    ext = fmt.split(":")[0]
    out = outdir / (src.stem + "." + ext)
    if not out.exists():
        raise RuntimeError(f"soffice produced nothing for {src} -> {fmt}")
    return out


def set_core_props(doc_props, title: str, author: str, when: _dt.datetime | _dt.date | None = None,
                   subject: str = "", keywords: str = "") -> None:
    """Set deterministic core properties on python-docx / python-pptx documents."""
    if when is None:
        when = FIXED_DT
    if isinstance(when, _dt.date) and not isinstance(when, _dt.datetime):
        when = _dt.datetime(when.year, when.month, when.day, 9, 0, 0)
    doc_props.title = title
    doc_props.author = author
    doc_props.last_modified_by = author
    doc_props.subject = subject
    doc_props.keywords = keywords
    doc_props.created = when
    doc_props.modified = when
    try:
        doc_props.revision = 1
    except Exception:
        pass
