"""Email thread rendering for .txt exports (three export styles, signatures, disclaimers).

Every message appears exactly once unquoted in the file; facts are recorded only against the
unquoted rendering so that ``text_lines`` locators point at clean text.
"""
from __future__ import annotations

import dataclasses
import random
from typing import Sequence

from . import phrases as PH
from .core import (W, Doc, Person, person, rfc2822, outlook_sent, zone_of, msgid, D, pick)


@dataclasses.dataclass
class F:
    """A fact to record on the span of the element it is attached to."""
    needle: str
    statement: str | None = None
    kind: str = "general"
    world_ref: str | None = None
    key: str | None = None          # placement key (copies statement/kind/world_ref/exclusive)
    notes: str | None = None
    exclusive: bool = False


@dataclasses.dataclass
class P:
    """A body paragraph. ``raw`` keeps line breaks (lists, tables) instead of wrapping."""
    text: str
    facts: Sequence[F] = ()
    raw: bool = False


@dataclasses.dataclass
class Msg:
    sender: str                       # pid
    to: Sequence                      # pids or literal "Name <addr>" strings
    date: str
    time: str
    subject: str
    body: Sequence                    # str | P
    cc: Sequence = ()
    greeting: str | None = None
    signoff: str | None = None
    signame: str | None = None        # short name under the sign-off
    sig: str = "full"                 # full | short | none | custom
    sig_lines: Sequence[str] = ()     # for sig="custom"
    sig_facts: Sequence[F] = ()       # facts located on the sign-off + signature block
    whole_facts: Sequence[F] = ()     # facts located on the whole message (greeting..signature)
    disclaimer: bool = True
    display_name: str | None = None   # e.g. ASCII spelling in the From header
    attachments: Sequence[str] = ()
    importance: str | None = None
    mobile: bool = False
    forward: "Msg | None" = None      # message forwarded inside this one
    forward_note: str = ""


def addr_of(x, d, style: str) -> str:
    if isinstance(x, str) and x in W.people:
        p = person(x, d)
        return p.outlook_addr() if style == "outlook" else p.addr()
    return str(x)


def signature_lines(p: Person, kind: str, r: random.Random, display_name: str | None = None) -> list[str]:
    name = display_name or p.name
    if kind == "none":
        return []
    if kind == "short":
        return [name, p.title] if p.title else [name]
    lines = [name, p.title]
    if p.employer == "ORG-CORVANE":
        lines.append(p.org_short if r.random() < 0.5 else p.org)
        if p.address:
            lines.append(p.address)
        tel = p.phone
        lines.append(pick(r, [f"T: {tel}", f"Tel: {tel}", f"Mobile: {tel}", f"M: {tel}"]))
        lines.append(p.email)
    elif p.employer == "ORG-IBM":
        lines.append(pick(r, ["IBM Consulting | Programme Skerry", "IBM Consulting – Programme Skerry",
                              "IBM Consulting"]))
        lines.append(pick(r, [f"Mobile: {p.phone}", f"M: {p.phone}"]))
        lines.append(p.email)
    elif p.employer == "REG-NISA":
        lines.append("National Insurance Supervisory Authority")
        lines.append("1 Regent Quay, London E14 9ZZ")
        lines.append(p.email)
    else:
        lines.append(p.org)
        lines.append(f"T: {p.phone}")
        lines.append(p.email)
    return [ln for ln in lines if ln]


def disclaimer_for(p: Person, r: random.Random) -> str:
    if p.employer == "ORG-CORVANE":
        if p.location_id in ("LOC-OSL", "LOC-STO", "LOC-CPH"):
            return pick(r, PH.CORVANE_NORDIC_DISCLAIMERS)
        return pick(r, PH.CORVANE_DISCLAIMERS)
    if p.employer == "ORG-IBM":
        return pick(r, PH.IBM_DISCLAIMERS)
    if p.employer == "REG-NISA":
        return "NISA – OFFICIAL. This message is intended for the addressee only."
    return PH.VENDOR_DISCLAIMER


class ThreadWriter:
    def __init__(self, doc: Doc, r: random.Random, width: int = 74):
        self.doc = doc
        self.r = r
        self.width = width
        self.style = ""

    # ------------------------------------------------------------------ body
    def _record(self, span, facts: Sequence[F]):
        for f in facts:
            if f.key:
                self.doc.place(span, f.key, f.needle, statement=f.statement, notes=f.notes,
                               kind=None if f.kind == "general" else f.kind)
            else:
                self.doc.fact(span, f.needle, f.statement, kind=f.kind, world_ref=f.world_ref,
                              exclusive=f.exclusive, notes=f.notes)

    def body(self, m: Msg, record: bool = True, quote: str = "") -> None:
        d = self.doc
        p = person(m.sender, m.date)
        msg_start = d.n + 1
        if m.greeting:
            d.line(quote + m.greeting)
            d.blank() if not quote else d.line(quote.rstrip())
        for item in m.body:
            if isinstance(item, str):
                item = P(item)
            if item.raw:
                span = d.block([quote + ln for ln in item.text.split("\n")])
            else:
                span = d.para(item.text, width=self.width - len(quote), prefix=quote)
            if record:
                self._record(span, item.facts)
            d.line(quote.rstrip()) if quote else d.blank()
        # sign-off and signature
        start = d.n + 1
        if m.signoff:
            d.line(quote + m.signoff)
        if m.signame:
            d.line(quote + m.signame)
        if quote:
            return
        if m.sig in ("full", "short"):
            if m.signoff or m.signame:
                d.blank()
            if self.r.random() < 0.5:
                d.line("--")
            d.block(signature_lines(p, m.sig, self.r, m.display_name))
        elif m.sig == "custom":
            d.block(list(m.sig_lines))
        end = d.n
        if record and m.sig_facts:
            self._record((start, max(start, end)), m.sig_facts)
        if record and m.whole_facts:
            self._record((msg_start, max(msg_start, end)), m.whole_facts)
        if m.mobile:
            if not hasattr(m, "_mobile_text"):
                m._mobile_text = pick(self.r, PH.MOBILE_FOOTER)
            d.blank()
            d.line(m._mobile_text)
        if m.attachments and self.style != "outlook":
            d.blank()
            for a in m.attachments:
                d.line(f"[Attachment: {a}]")
        if m.disclaimer:
            d.blank()
            d.para(disclaimer_for(p, self.r), width=self.width)
        if m.forward is not None:
            d.blank()
            self.forwarded(m.forward)

    def forwarded(self, f: Msg):
        d = self.doc
        fp = person(f.sender, f.date)
        d.line(pick(self.r, ["---------- Forwarded message ---------", "-----Forwarded Message-----",
                             "Begin forwarded message:"]))
        d.line(f"From: {fp.addr(f.display_name)}")
        d.line(f"Date: {rfc2822(f.date, f.time, zone=zone_of(f.sender))}")
        d.line(f"Subject: {f.subject}")
        d.line("To: " + "; ".join(addr_of(x, f.date, 'plain') for x in f.to))
        if f.cc:
            d.line("Cc: " + "; ".join(addr_of(x, f.date, 'plain') for x in f.cc))
        d.blank()
        saved = (f.disclaimer, f.forward)
        f.disclaimer, f.forward = False, None
        self.body(f, record=False)
        f.disclaimer, f.forward = saved

    # ------------------------------------------------------------------ headers
    def header_rfc(self, m: Msg, k: int, domain: str, reply_to: str | None = None):
        d = self.doc
        p = person(m.sender, m.date)
        d.line(f"From: {p.addr(m.display_name)}")
        d.line("To: " + ", ".join(addr_of(x, m.date, 'plain') for x in m.to))
        if m.cc:
            d.line("Cc: " + ", ".join(addr_of(x, m.date, 'plain') for x in m.cc))
        d.line(f"Date: {rfc2822(m.date, m.time, sec=self.r.randint(0, 59), zone=zone_of(m.sender))}")
        d.line(f"Subject: {m.subject}")
        d.line(f"Message-ID: {msgid(self.doc.fid, k, domain)}")
        if reply_to:
            d.line(f"In-Reply-To: {reply_to}")
        if m.importance:
            d.line(f"Importance: {m.importance}")
        d.blank()

    def header_outlook(self, m: Msg, separator: str | None):
        d = self.doc
        p = person(m.sender, m.date)
        if separator:
            d.line(separator)
        disp = f"{m.display_name} <{p.email}>" if m.display_name else p.outlook_addr()
        d.line(f"From: {disp}")
        d.line(f"Sent: {outlook_sent(m.date, m.time)}")
        d.line("To: " + "; ".join(addr_of(x, m.date, 'outlook') for x in m.to))
        if m.cc:
            d.line("Cc: " + "; ".join(addr_of(x, m.date, 'outlook') for x in m.cc))
        d.line(f"Subject: {m.subject}")
        if m.importance:
            d.line(f"Importance: {m.importance}")
        if m.attachments:
            d.line("Attachments: " + "; ".join(m.attachments))
        d.blank()

    def header_archive(self, m: Msg, k: int, total: int):
        d = self.doc
        p = person(m.sender, m.date)
        d.line("=" * 72)
        d.line(f"Message {k} of {total}")
        d.line(f"From:     {p.addr(m.display_name)}")
        d.line(f"Sent:     {rfc2822(m.date, m.time, sec=self.r.randint(0, 59), zone=zone_of(m.sender))}")
        d.line("To:       " + "; ".join(addr_of(x, m.date, 'plain') for x in m.to))
        if m.cc:
            d.line("Cc:       " + "; ".join(addr_of(x, m.date, 'plain') for x in m.cc))
        d.line(f"Subject:  {m.subject}")
        if m.importance:
            d.line(f"Priority: {m.importance}")
        d.line("-" * 72)
        d.blank()

    # ------------------------------------------------------------------ whole threads
    def render(self, msgs: Sequence[Msg], style: str, domain: str = "corvane-mutual.example",
               banner: str | None = None):
        d = self.doc
        self.style = style
        if style == "archive":
            d.line(banner or pick(self.r, PH.PRINT_BANNERS))
            d.line(f"Conversation: {msgs[0].subject}")
            d.line(f"Messages: {len(msgs)}")
            d.blank()
            for k, m in enumerate(msgs, 1):
                self.header_archive(m, k, len(msgs))
                self.body(m)
                d.blank()
            d.line("=" * 72)
            d.line("End of conversation")
        elif style == "outlook":
            order = list(reversed(msgs))
            for k, m in enumerate(order):
                sep = None if k == 0 else pick(self.r, ["-----Original Message-----", "_" * 32, ""])
                if k > 0:
                    d.blank()
                self.header_outlook(m, sep or None)
                self.body(m)
        elif style == "mbox":
            prev_id = None
            for k, m in enumerate(msgs, 1):
                mid = msgid(d.fid, k, domain)
                self.header_rfc(m, k, domain, reply_to=prev_id)
                self.body(m)
                if k > 1:
                    pm = msgs[k - 2]
                    pp = person(pm.sender, pm.date)
                    d.blank()
                    d.line(f"On {D(pm.date).strftime('%a')} {D(pm.date).day} {D(pm.date).strftime('%b %Y')} at {pm.time}, "
                           f"{pm.display_name or pp.name} <{pp.email}> wrote:")
                    self.body(pm, record=False, quote="> ")
                d.blank()
                d.line("")
                prev_id = mid
        elif style == "single":
            m = msgs[0]
            self.header_rfc(m, 1, domain)
            self.body(m)
        else:
            raise ValueError(style)
