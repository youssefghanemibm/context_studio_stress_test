"""Shared pieces for the meeting transcripts (headers, speaker maps, calibration)."""
from __future__ import annotations

from generators.common import util

from .common import W, Facts, D, long_date, name, title, first
from .dialogue import Meeting


def speakers_for(meeting_id: str, d, overrides: dict | None = None) -> dict:
    """Speaker map for a meeting from timeline.meetings attendees (labels as-of the date)."""
    m = W.meetings[meeting_id]
    out = {}
    for pid in m["attendees"]:
        lab = name(pid, d)
        out[pid] = {"label": lab, "first": first(pid, d), "pid": pid, "role": title(pid, d)}
    for pid, o in (overrides or {}).items():
        out[pid].update(o)
    return out


def org_of(pid: str) -> str:
    emp = W.people[pid]["employer"]
    if emp == "ORG-IBM":
        return "IBM Consulting"
    if emp == "ORG-CORVANE":
        return "Corvane Mutual"
    if emp.startswith("VEN-"):
        return W.vendors[emp]["name"]
    if emp.startswith("REG-"):
        return "NISA"
    return emp


def transcript_header(*, doc_ref: str, title_: str, meeting_id: str, venue: str, chair: str,
                      author: str, approver: str, speakers: dict, d, versions: list[tuple],
                      extra_notes: list[str] = (), forum_line: str | None = None,
                      classification: str = "Internal") -> list[str]:
    m = W.meetings[meeting_id]
    start = m["start_time"]
    h, mi = map(int, str(start).split(":"))
    end_min = h * 60 + mi + m["duration_minutes"]
    end = f"{end_min // 60:02d}:{end_min % 60:02d}"
    rule = "=" * 92
    L = [
        "CORVANE MUTUAL INSURANCE SOCIETY LIMITED",
        title_.upper(),
        rule,
        "",
        "DOCUMENT CONTROL",
        f"  Document reference : {doc_ref}",
        f"  Title              : {title_}",
        f"  Meeting            : {m['title']}",
    ]
    if forum_line:
        L.append(f"  Forum              : {forum_line}")
    L += [
        f"  Date and time      : {long_date(d)}, {start}-{end} UK time ({m['duration_minutes']} minutes)",
        f"  Venue              : {venue}",
        f"  Chair              : {speakers[chair]['label']}, {speakers[chair]['role']}",
        f"  Prepared by        : {name(author, d)}, {title(author, d)} ({org_of(author)})",
        f"  Approved by        : {speakers[approver]['label'] if approver in speakers else name(approver, d)}",
        "  Status             : Final",
        f"  Classification     : {classification}",
        "",
        "VERSION HISTORY",
        "  Version  Date        Author / approver         Change",
    ]
    for v, vd, who, chg in versions:
        L.append(f"  {v:<8} {vd:<11} {who:<25} {chg}")
    L += ["", "ATTENDEES"]
    for k, s in speakers.items():
        if s.get("silent"):
            continue
        role = s.get("display_role") or s["role"]
        org = org_of(s["pid"])
        role_txt = role if org == "Corvane Mutual" else f"{role}, {org}"
        L.append(f"  {s['label']:<28} {role_txt}")
    L += [
        "",
        "NOTES ON THIS TRANSCRIPT",
        "  - Timestamps are elapsed time from the start of the recording (hh:mm:ss).",
        "  - Speaker labels follow the display names on the bridge and were checked by hand.",
        "  - [inaudible] and [crosstalk] mark passages the transcription could not resolve.",
    ]
    for n in extra_notes:
        L.append(f"  - {n}")
    L += ["", "-" * 38 + " TRANSCRIPT " + "-" * 42, ""]
    return L


def footer(m: Meeting, d, author: str) -> None:
    m.doc.add("")
    m.doc.add("-" * 38 + " END OF TRANSCRIPT " + "-" * 35)
    m.doc.add(f"Recording length {m.duration // 3600:02d}:{(m.duration % 3600) // 60:02d}:00. "
              f"Transcript reviewed by {name(author, d)}. Corvane Mutual - Internal.")


def calibrate(fid: str, build, facts: Facts, lo: int, hi: int, wps0: float):
    """Build the transcript at increasing/decreasing speech rates until the word count is in range."""
    wps = wps0
    for attempt in range(8):
        tmp = Facts()
        m = build(tmp, round(wps, 3))
        n = m.words()
        if lo <= n <= hi:
            break
        target = (lo + hi) / 2
        wps = wps * target / n
    else:
        raise RuntimeError(f"{fid}: could not calibrate word count ({n})")
    for e in tmp.entries:
        facts.entries.append(e)
    facts.counters[fid] = tmp.counters.get(fid, 0)
    return m, n
