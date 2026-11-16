"""Shared world access and guards for the raster document builders."""
from __future__ import annotations

import datetime as dt
import pathlib

from generators.common import util
from world.worldlib import load_world

W = load_world()
OUT_DIR = util.UPLOAD / "visuals"
CACHE = util.BUILD / "cache" / "vs_raster"


class ExclusivityError(AssertionError):
    pass


def guard(fid: str, ref: str, field: str | None = None) -> None:
    """Raise unless file `fid` may state `field` of `ref` (exclusivity, incl. guards)."""
    if not W.may_state(fid, ref, field):
        raise ExclusivityError(f"{fid} may not state {ref}#{field} (reserved for {W.is_exclusive(ref, field)})")


def guard_all(fid: str, items) -> None:
    for it in items:
        if isinstance(it, tuple):
            guard(fid, *it)
        else:
            guard(fid, it)


def anchor(fid: str) -> dict:
    return W.anchor(fid)


def adate(fid: str) -> str:
    return str(W.anchor(fid)["date"])[:10]


def out_path(fid: str) -> pathlib.Path:
    return OUT_DIR / W.anchor(fid)["filename"]


def rel(fid: str) -> str:
    return f"corpus/upload/visuals/{W.anchor(fid)['filename']}"


def placement(fid: str, key: str) -> dict:
    for p in W.placements_for(fid):
        if p["key"] == key:
            return p
    raise KeyError(f"{fid} has no placement {key}")


def name(pid: str, d: str) -> str:
    return W.name_of(pid, d)


def title(pid: str, d: str) -> str:
    t = W.title_of(pid, d)
    if t is None:
        raise ValueError(f"{pid} has no title on {d}")
    return t


def who(pid: str, d: str) -> str:
    """'Name — Title' as of date."""
    return f"{name(pid, d)} — {title(pid, d)}"


def initials(pid: str, d: str) -> str:
    return "".join(w[0] for w in name(pid, d).replace("-", " ").split() if w[0].isalpha()).upper()[:3]


def sysname(sid: str, d: str) -> str:
    return W.system_name(sid, d)


def svcname(svc: str, d: str) -> str:
    return W.service_name(svc, d)


def team_name(tid: str, d: str) -> str:
    return W.team_name(tid, d)


def minus_days(d: str, n: int) -> str:
    return (dt.date.fromisoformat(d) - dt.timedelta(days=n)).isoformat()


def plus_days(d: str, n: int) -> str:
    return (dt.date.fromisoformat(d) + dt.timedelta(days=n)).isoformat()


def employed(pid: str, d: str) -> bool:
    return W.employed(pid, d)


def program_exists(pgm: str, d: str) -> bool:
    p = W.programs.get(pgm)
    return bool(p) and str(p.get("since", "1900-01-01")) <= d


def program_id(pgm: str, d: str) -> str:
    """Program id in use on date d (programs.yaml renamed_from: e.g. CLRFR030 was FNETREF1 before 2025-03-01)."""
    rf = (W.programs.get(pgm) or {}).get("renamed_from")
    return rf["old_id"] if rf and str(d) < str(rf["date"]) else pgm


def table_exists(tname: str, d: str) -> bool:
    t = W.tables.get(tname)
    return bool(t) and str(t.get("created") or "1900-01-01") <= d


def interface_live(iid: str, d: str) -> bool:
    i = W.interfaces[iid]
    return str(i.get("since", "1900-01-01")) <= d and i.get("status") != "planned" or \
        (i.get("status") == "planned" and False)


def rule_text(rid: str, d: str) -> str | None:
    v = W.rule_version(rid, d)
    return v["text"] if v else None


def rule_ver(rid: str, d: str) -> dict | None:
    return W.rule_version(rid, d)


def _renames() -> list[tuple[str, str, str]]:
    out = []
    for s in W.systems.values():
        for r in s.get("renames") or []:
            out.append((r["from_name"], r["to_name"], str(r["date"])[:10]))
    for s in W.services.values():
        for r in s.get("renames") or []:
            out.append((r["from_name"], r["to_name"], str(r["date"])[:10]))
    return out


RENAMES = _renames()


def asof_names(s: str, d: str) -> str:
    """Rewrite current system/service names in world free text (interface formats, table descriptions)
    to the names in use on date d, so a document never uses a name before its rename date."""
    for old, new, rd in RENAMES:
        if d < rd and new in s:
            s = s.replace(f"{old} / {new}", old).replace(f"{new} / {old}", old).replace(new, old)
    return s
