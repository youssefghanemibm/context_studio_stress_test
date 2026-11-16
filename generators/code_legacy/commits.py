"""Every commit that touches legacy/ files, in chronological order.

World commits (CM-xx) come from corpus_plan.yaml. The XC-xx commits are legacy-only source
syncs that the world implies (renames, ticketed CLARA changes, parameter rows, new programs) but
that corpus_plan does not list; their dates, authors and tickets come from key_tickets.yaml,
programs.yaml (since / renamed_from), copybooks.yaml (field_history) and tables.yaml
(T_PARAM param_rows). history.yaml documents them for the repo assembler.
"""
from __future__ import annotations

# (id, date, author person id, message, variants, tickets)
EXTRA = [
    ("XC-01", "2025-03-01", "P024",
     "CLRFR020/CLRFR030: rename FNETCAL1 and FNETREF1 after the FRAUDNET -> Sentinel rename", ["a", "b", "c"], []),
    ("XC-02", "2025-04-25", "P023",
     "CHUB-138 RSVMOVE: widen RM-AMOUNT to S9(11)V99 for Nordic large losses", ["a", "b", "c"], ["CHUB-138"]),
    ("XC-03", "2025-08-28", "P024",
     "T_PARAM seed: REC_PURSUE_MIN_GBP 1000 valid from 2025-09-01 (BR-REC-003 v3)", ["a", "b", "c"], []),
    ("XC-04", "2026-02-27", "P023",
     "CHUB-241 CLRRS210 reserve parallel-run reconciliation and job CLRDRSV9", ["a", "b", "c"], ["CHUB-241"]),
    ("XC-05", "2026-03-30", "P024",
     "CHUB-205 T_PARAM: FRD_REFER_THRESH 70 -> 65 valid from 2026-04-01", ["a", "b", "c"], ["CHUB-205"]),
    ("XC-06", "2026-03-31", "P026",
     "CHUB-207 disable auto-decline sweep CLRFR140; remove CLRNFR99 from the schedule", ["a", "b", "c"], ["CHUB-207"]),
    ("XC-07", "2026-06-26", "P024",
     "CHUB-208 CLRFR090 NISA-FR1 quarterly return extract and job CLRQFR01", ["a", "b", "c"], ["CHUB-208"]),
    ("XC-08", "2026-06-30", "P024",
     "CHUB-318 T_PARAM: RSV_T3_REVIEW_DAYS 21 -> 14 valid from 2026-07-01", ["a", "b", "c"], ["CHUB-318"]),
    ("XC-09", "2026-08-28", "P023",
     "CLRRS210/CLRDRSV9: retire parallel-run reconciliation after the parallel run ended", ["a", "b", "c"], ["CHUB-241"]),
    ("XC-10", "2026-09-30", "P024",
     "CHUB-395 CLARA: add CLR.T_PARAM FRD_REFER_T3_THRESH = 60 valid from 2026-10-01", ["a", "b", "c"], ["CHUB-395"]),
    ("XC-11", "2026-10-20", "P052",
     "legacy/clara/docs: program inventory, batch job notes and DB2 object list", ["a", "b", "c"], []),
]

WORLD_IDS = ["CM-01", "CM-02", "CM-03", "CM-05", "CM-09"]   # world commits that touch legacy files


def all_commits(W) -> list[dict]:
    out = []
    for cid in WORLD_IDS:
        c = W.commits[cid]
        variants = ["c"] if c["variant"] == "c" else ["a", "b", "c"]
        out.append({"id": cid, "world": True, "date": c["date"], "author": c["author"],
                    "message": c["message"], "variants": variants, "tickets": list(c.get("tickets", []))})
    for cid, date, author, msg, variants, tickets in EXTRA:
        out.append({"id": cid, "world": False, "date": date, "author": author, "message": msg,
                    "variants": variants, "tickets": tickets})
    out.sort(key=lambda c: (c["date"], c["id"]))
    world_a = sorted([c for c in W.commits.values() if c["variant"] == "a"], key=lambda c: c["date"])
    for c in out:
        p = W.people[c["author"]]
        c["author_name"] = p["name"]
        c["author_email"] = p["email"]
        if not c["world"]:
            later = [w for w in world_a if w["date"] >= c["date"]]
            earlier = [w for w in world_a if w["date"] < c["date"]]
            c["fold_into"] = later[0]["id"] if later else earlier[-1]["id"]
        else:
            c["fold_into"] = None
    return out


def order(W) -> list[str]:
    return [c["id"] for c in all_commits(W)]


C_ONLY = {"CM-09"}
