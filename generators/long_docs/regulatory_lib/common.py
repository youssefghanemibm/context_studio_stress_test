"""Shared helpers for the regulatory long documents (world access, facts, phrase banks)."""
from __future__ import annotations

import datetime as dt
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from generators.common import util  # noqa: E402
from world.worldlib import load_world  # noqa: E402

W = load_world()
FAMILY_DIR = "long_docs"
MANIFEST_NAME = "long_docs.regulatory"
OUT_DIR = util.UPLOAD / FAMILY_DIR
CACHE = util.BUILD / "cache" / "ld_regulatory"
MY_FILES = ["LD003", "LD004", "LD005", "LD006", "LD007", "LD008", "LD009", "LD010", "LD011",
            "LD021", "LD022", "LD023"]

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


def d(s: str) -> dt.date:
    return dt.date.fromisoformat(str(s))


def long_date(s) -> str:
    x = d(s) if not isinstance(s, dt.date) else s
    return f"{x.day} {MONTHS[x.month - 1]} {x.year}"


def anchor(fid: str) -> dict:
    return W.anchor(fid)


def out_path(fid: str) -> pathlib.Path:
    return OUT_DIR / anchor(fid)["filename"]


def person(pid: str, when) -> tuple[str, str]:
    when = str(when)
    return W.name_of(pid, when), W.title_of(pid, when)


class NotAllowed(Exception):
    pass


def guard(fid: str, ref: str, field: str | None = None) -> None:
    """Raise unless file ``fid`` may state ``ref``/``field`` (exclusivity contract)."""
    if not W.may_state(fid, ref, field):
        raise NotAllowed(f"{fid} may not state {ref}#{field}")


def may(fid: str, ref: str, field: str | None = None) -> bool:
    return bool(W.may_state(fid, ref, field))


def rule_text(fid: str, rid: str, when) -> str | None:
    """Text of the rule version in force at ``when`` if ``fid`` may state it, else None."""
    v = W.rule_version(rid, str(when))
    if not v:
        return None
    ref = f"{rid}@v{v['version']}"
    if not W.may_state(fid, ref, "text"):
        return None
    return v["text"]


# ---------------------------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------------------------

class Facts:
    """Collects manifest entries for one file; fact ids are assigned in insertion order."""

    def __init__(self, fid: str):
        self.fid = fid
        self.file = f"corpus/upload/{FAMILY_DIR}/{anchor(fid)['filename']}"
        self.items: list[dict] = []

    def add(self, kind: str, statement: str, needle: str, locator: dict, world_ref: str | None = None,
            exclusive: bool = False, placement: str | None = None, placement_key: str | None = None,
            also_in: list | None = None, notes: str | None = None, **extra) -> str:
        fact_id = f"{self.fid}-F{len(self.items) + 1:03d}"
        e = {"fact_id": fact_id, "world_ref": world_ref, "kind": kind, "statement": statement,
             "file": self.file, "locator": locator, "needle": needle, "exclusive": bool(exclusive),
             "also_in": list(also_in or [])}
        if placement:
            e["placement"] = placement
            e["placement_key"] = placement_key
        if notes:
            e["notes"] = notes
        e.update(extra)
        self.items.append(e)
        return fact_id

    def placement(self, pl: dict, needle: str, locator: dict, statement: str | None = None,
                  notes: str | None = None, **extra) -> str:
        also = []
        for other in pl.get("also_in") or []:
            try:
                also.append(f"corpus/upload/{FAMILY_DIR}/{anchor(other)['filename']}")
            except Exception:
                also.append(str(other))
        return self.add(pl["kind"], statement or pl["fact"], needle, locator, world_ref=pl["world_ref"],
                        exclusive=bool(pl.get("exclusive")), placement=pl["placement_id"],
                        placement_key=pl.get("key"), also_in=also, notes=notes, **extra)

    def save(self) -> pathlib.Path:
        CACHE.mkdir(parents=True, exist_ok=True)
        p = CACHE / f"facts_{self.fid}.yaml"
        with open(p, "w", encoding="utf-8") as fh:
            yaml.safe_dump(self.items, fh, sort_keys=False, allow_unicode=True, width=120)
        return p


def placements(fid: str) -> dict[str, dict]:
    """Placements for a file keyed by their stable key."""
    return {p["key"]: p for p in W.placements_for(fid)}


def merge_manifest() -> pathlib.Path:
    entries = []
    for fid in MY_FILES:
        p = CACHE / f"facts_{fid}.yaml"
        if p.exists():
            entries.extend(yaml.safe_load(p.read_text(encoding="utf-8")) or [])
    return util.write_manifest(MANIFEST_NAME, entries)


# ---------------------------------------------------------------------------------------------
# Phrase banks
# ---------------------------------------------------------------------------------------------

class Deck:
    """Draw from phrase lists without repeating until a list is exhausted (deterministic)."""

    def __init__(self, key: str):
        self.r = util.rng(key)
        self._decks: dict[int, list] = {}

    def pick(self, options: list):
        k = id(options)
        deck = self._decks.get(k)
        if not deck:
            deck = list(range(len(options)))
            self.r.shuffle(deck)
            self._decks[k] = deck
        return options[deck.pop()]

    def choice(self, options):
        return self.r.choice(options)

    def randint(self, a, b):
        return self.r.randint(a, b)

    def random(self):
        return self.r.random()

    def shuffle(self, x):
        self.r.shuffle(x)

    def sample(self, x, n):
        return self.r.sample(x, n)

    def fill(self, template: str, slots: dict) -> str:
        out = template
        for _ in range(4):
            changed = False
            for k, v in slots.items():
                tok = "{" + k + "}"
                while tok in out:
                    out = out.replace(tok, self.pick(v) if isinstance(v, list) else str(v), 1)
                    changed = True
            if not changed:
                break
        return out


def fmt_money_m(x: float) -> str:
    return f"£{x:,.1f}m"


def fmt_int(n: int) -> str:
    return f"{n:,}"


def seeded(key: str) -> random.Random:
    return util.rng(key)
