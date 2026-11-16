"""Helpers shared by the two manual content modules: rule paragraphs, needles, figure specs."""
from __future__ import annotations

import re

from .spec import Spec, long_date, money


def pick_needle(text: str) -> str:
    """A distinctive substring: a window around the first number, else the first words."""
    words = text.split()
    for i, w in enumerate(words):
        if re.search(r"\d", w) and not re.match(r"^(BR|CLX|NISA|CIRC)-", w):
            a, b = max(0, i - 3), min(len(words), i + 3)
            return " ".join(words[a:b]).rstrip(".,;:")
    return " ".join(words[:7]).rstrip(".,;:")


RULE_FORMATS_V72 = [
    lambda rid, v, t, eff: [{"text": f"{rid} (v{v}, effective {eff}). ", "bold": True}, {"text": t}],
    lambda rid, v, t, eff: [{"text": "Rule: ", "bold": True}, {"text": t + " "}, {"text": f"[{rid} v{v}]", "italic": True}],
    lambda rid, v, t, eff: [{"text": f"Under {rid} (version {v}): "}, {"text": t}],
    lambda rid, v, t, eff: [{"text": f"{rid}. ", "bold": True}, {"text": t + f" (Version {v}, in force from {eff}.)"}],
]
RULE_FORMATS_V61 = [
    lambda rid, v, t, eff: [{"text": f"Standard {rid}: ", "bold": True}, {"text": t}],
    lambda rid, v, t, eff: [{"text": t + " "}, {"text": f"({rid})", "italic": True}],
    lambda rid, v, t, eff: [{"text": f"{rid} — ", "bold": True}, {"text": t}],
]


def rule_p(S: Spec, rid: str, text: str | None = None, needle: str | None = None, kind: str = "general",
           statement: str | None = None, notes: str | None = None, fmt: int | None = None,
           as_of: str | None = None, extra_facts: list | None = None, comment=None) -> dict | None:
    v = S.rv(rid, as_of)
    ref = f"RULE:{rid}@v{v['version']}"
    if not S.may(ref, "text"):
        return None
    t = text or v["text"]
    eff = long_date(v["effective_from"])
    fmts = RULE_FORMATS_V61 if S.v61 else RULE_FORMATS_V72
    f_i = fmt if fmt is not None else S.r.randrange(len(fmts))
    runs = fmts[f_i % len(fmts)](rid, v["version"], t, eff)
    nd = needle or pick_needle(t)
    fct = S.fact(kind, statement or f"{rid} v{v['version']} ({S.fid}): {t}", nd, world_ref=ref, notes=notes)
    S.p(runs=runs, facts=[fct] + list(extra_facts or []), comment=comment)
    S.rule_sections.setdefault(rid, S.section)
    return fct


def gbp_or(cur: str, v) -> str:
    return money(v, "£" if cur == "GBP" else cur)
