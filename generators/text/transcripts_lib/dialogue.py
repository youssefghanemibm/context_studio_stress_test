"""Transcript engine: timestamped speaker turns, scripted (fact-bearing) turns at anchor times,
and topic-coherent filler talk generated from the phrase banks in between.
"""
from __future__ import annotations

import re

from . import phrases as P
from .common import TextDoc


def fmt_ts(sec: float) -> str:
    s = int(sec)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


_LOWERABLE = {"The", "We", "It", "There", "If", "On", "For", "My", "What", "From", "Let", "Can", "Everything",
              "To", "Part", "Whatever", "Just", "Honestly", "Personally", "One", "Once", "Every", "Is", "Are", "Do",
              "Has", "Have", "How", "Who", "Where", "Our", "That", "This", "Nobody", "Anything", "Some", "Maybe",
              "Mostly", "Not", "Short", "Gut", "Good", "Fair", "A", "Same", "Most", "In", "Any", "Everyone",
              "Could", "Would", "Should", "Did", "Does", "When", "Every", "Whatever", "Nothing", "Probably",
              "Possibly", "Steady", "Broadly", "Reasonably", "Comfortable", "Timing", "Knock-on", "Only", "Yes",
              "Partly", "Near", "Top", "Resourcing", "Finance's", "Most", "Tipping-off", "As", "Once", "With"}


def lower_first(s: str) -> str:
    w = s.split(" ", 1)[0]
    base = w.split("'")[0].rstrip(",.")
    if w in _LOWERABLE or base in _LOWERABLE:
        return s[:1].lower() + s[1:]
    return s


# Subject-verb agreement for plural topic subjects ("the DNS records is" -> "are").
PLURAL_VERB = {"is": "are", "isn't": "aren't", "was": "were", "wasn't": "weren't", "has": "have", "hasn't": "haven't",
               "needs": "need", "matters": "matter", "slips": "slip", "sits": "sit", "says": "say", "moves": "move",
               "lands": "land", "keeps": "keep", "looks": "look", "touches": "touch", "doesn't": "don't", "does": "do",
               "goes": "go", "seems": "seem", "feels": "feel", "depends": "depend", "gets": "get", "takes": "take",
               "comes": "come", "makes": "make", "belongs": "belong", "affects": "affect", "turns": "turn"}
_SINGULAR_S = ("ss", "us", "is", "ias", "sis", "news", "series", "status")


def is_plural(subject: str) -> bool:
    w = subject.split()[-1] if subject.split() else ""
    return len(w) > 2 and w.endswith("s") and w[-2].islower() and not w.lower().endswith(_SINGULAR_S)


class Topic:
    def __init__(self, name: str, subjects: list[str], domain: str | None = None, leads=(), lines=(),
                 qa=()):
        self.name = name
        self.subjects = list(subjects)
        self.domain = domain
        self.leads = list(leads)
        # topic-specific safe lines: (speaker_key or None, text)
        self.lines = [ln if isinstance(ln, tuple) else (None, ln) for ln in lines]
        # topic-specific question/answer pairs: (asker or None, question, answerer or None, answer)
        self.qa = list(qa)


class Meeting:
    def __init__(self, fid, path, facts, speakers: dict, rng, *, wps: float = 2.6, chair: str,
                 domain: str = "steering", duration_min: int = 120, meta_budget: int = 8,
                 digress_budget: int = 3, crosstalk_budget: int = 5):
        """speakers: key -> {"label": str, "first": str}"""
        self.doc = TextDoc(fid, path, facts)
        self.fid = fid
        self.sp = speakers
        self.r = rng
        self.wps = wps
        self.chair = chair
        self.domain = domain
        self.duration = duration_min * 60
        self.t = 0.0
        self.used: set[str] = set()
        self.last: str | None = None
        self.prev: str | None = None
        self.meta = list(P.META_SEQS)
        self.dig = list(P.DIGRESSION_SEQS)
        self.cross = list(P.CROSSTALK_SEQS)
        self.r.shuffle(self.meta)
        self.r.shuffle(self.dig)
        self.r.shuffle(self.cross)
        self.budget = {"meta": meta_budget, "dig": digress_budget, "cross": crosstalk_budget}
        self.last_event = {"meta": -1e9, "dig": -1e9, "cross": -1e9}
        self.spacing = {"meta": 420.0 * 120 / max(duration_min, 1) * duration_min / 120,
                        "dig": 1200.0, "cross": 600.0}
        self.answers: dict[str, list[str]] = {}
        self.turns = 0
        self.speech_lines: list[int] = []

    # -------------------------------------------------------------------------- basic output
    def header(self, lines):
        for ln in lines:
            self.doc.add(ln)

    def _dur(self, text: str) -> float:
        words = len(text.split())
        return words / self.wps + self.r.uniform(0.3, 1.4)

    @staticmethod
    def _dedupe(text: str) -> str:
        """Drop a sentence repeated verbatim inside one turn (phrase-bank collisions)."""
        parts = re.split(r"(?<=[.?!])\s+", text)
        seen, out = set(), []
        for s in parts:
            k = s.strip().casefold()
            if len(s.split()) > 4 and k in seen:
                continue
            seen.add(k)
            out.append(s)
        return " ".join(out)

    def say(self, key: str, text: str, fact: dict | list | None = None, gap: float | None = None) -> int:
        label = self.sp[key]["label"]
        if not fact:
            text = self._dedupe(text)
        line = f"[{fmt_ts(self.t)}] {label}: {text}"
        n = self.doc.add(line)
        self.speech_lines.append(n)
        for f in ([fact] if isinstance(fact, dict) else (fact or [])):
            self.doc.fact(n, **f)
        self.t += self._dur(text) if gap is None else len(text.split()) / self.wps + gap
        self.prev, self.last = self.last, key
        self.turns += 1
        return n

    def note(self, text: str) -> int:
        """Non-speech line inside the transcript body (e.g. a recording note)."""
        return self.doc.add(f"[{fmt_ts(self.t)}] {text}")

    def wait_until(self, sec: float) -> None:
        if self.t < sec:
            self.t = sec

    def at(self, mm: int, ss: int | None = None, hh: int = 0) -> float:
        if ss is None:
            ss = self.r.randint(3, 40)
        return hh * 3600 + mm * 60 + ss

    # -------------------------------------------------------------------------- text helpers
    def first(self, key: str) -> str:
        return self.sp[key]["first"]

    def _others(self, exclude=()) -> list[str]:
        return [k for k in self.sp if k not in exclude and not self.sp[k].get("silent")]

    def pick_speaker(self, topic: Topic, exclude=()) -> str:
        pool, weights = [], []
        for k in self._others(exclude):
            if k == self.last and len(self._others(exclude)) > 1:
                continue
            w = self.sp[k].get("weight", 1.0)
            if k in topic.leads:
                w *= 3.0
            if k == self.chair:
                w *= 1.3
            pool.append(k)
            weights.append(w)
        return self.r.choices(pool, weights=weights)[0]

    def _fill_template(self, tpl: str, s: str, n: str = "") -> str:
        if is_plural(s):
            # only where the subject placeholder is the grammatical subject (not "the thing about {s} is")
            tpl = re.sub(r"(?<!\bon )(?<!\bwith )(?<!\bof )(?<!\babout )(?<!\bfor )(\{[sS]\}) (\S+)",
                         lambda mo: f"{mo.group(1)} {PLURAL_VERB.get(mo.group(2), mo.group(2))}", tpl)
            tpl = (tpl.replace("Is {s}", "Are {s}").replace("is {s}", "are {s}").replace("does {s}", "do {s}")
                   .replace("or is that coming", "or are they coming"))
        return tpl.replace("{s}", s).replace("{S}", cap(s)).replace("{n}", n)

    def _fresh(self, bank: list, s: str, n: str = "", tries: int = 14):
        out = None
        for _ in range(tries):
            tpl = self.r.choice(bank)
            if isinstance(tpl, tuple):
                txt = self._fill_template(tpl[0], s, n)
                out = (txt, tpl[1])
                key = txt
            else:
                out = self._fill_template(tpl, s, n)
                key = out
            if key not in self.used:
                self.used.add(key)
                return out
        return out

    def _answer(self, cat: str) -> str:
        pool = self.answers.get(cat)
        if not pool:
            pool = list(P.ANSWERS[cat])
            self.r.shuffle(pool)
            self.answers[cat] = pool
        return pool.pop()

    def _decorate(self, sent: str) -> str:
        r = self.r
        x = r.random()
        if x < 0.20:
            m = r.choice(P.MARKERS)
            sent = m + (sent if m.endswith(". ") else lower_first(sent))
        if r.random() < 0.08 and sent.endswith("."):
            sent = sent[:-1] + r.choice(P.TAGS) + "."
        if r.random() < 0.03:
            words = sent.split(" ")
            if len(words) > 8:
                i = r.randint(3, len(words) - 3)
                if words[i].isalpha():
                    words[i] = "[inaudible]"
                    sent = " ".join(words)
        return sent

    def _disfluent(self, text: str) -> str:
        r = self.r
        x = r.random()
        if x < 0.07:
            return r.choice(["Um, ", "Uh, ", "So, um, ", "Yeah, um, "]) + lower_first(text)
        if x < 0.11:
            words = text.split(" ")
            for i, w in enumerate(words[:8]):
                if w in ("the", "I", "we", "it's", "that", "a"):
                    words.insert(i, w + ",")
                    return " ".join(words)
        return text

    def _statement(self, topic: Topic, s: str | None = None) -> str:
        s = s or self.r.choice(topic.subjects)
        bank = P.STATEMENTS
        if topic.domain and self.r.random() < 0.4:
            bank = P.DOMAIN[topic.domain]
        return self._decorate(self._fresh(bank, s))

    def _topic_line(self, topic: Topic, key: str) -> str | None:
        for i, (who, text) in enumerate(topic.lines):
            if who is None or who == key:
                topic.lines.pop(i)
                return text
        return None

    def _event_ok(self, kind: str, pool: list) -> bool:
        return (self.budget[kind] > 0 and pool and self.t > 180
                and self.t - self.last_event[kind] >= self.spacing[kind])

    # -------------------------------------------------------------------------- filler blocks
    def _block(self, topic: Topic) -> list[tuple[str, str]]:
        r = self.r
        x = r.random()
        if topic.qa and x < 0.08:
            asker, q, answerer, a = topic.qa.pop(0)
            asker = asker or self.pick_speaker(topic)
            answerer = answerer or self.pick_speaker(topic, exclude=(asker,))
            q = q.replace("{nB}", self.first(answerer))
            return [(asker, q), (answerer, a)]
        if x < 0.32:
            a = self.pick_speaker(topic)
            text = self._topic_line(topic, a)
            if text:
                if r.random() < 0.6:
                    text += " " + self._statement(topic)
                out = [(a, text)]
                if r.random() < 0.2:
                    out.append((self.pick_speaker(topic, exclude=(a,)), r.choice(P.ACKS)))
                return out
        if x < 0.48:
            a = self.pick_speaker(topic)
            b = self.pick_speaker(topic, exclude=(a,))
            s = r.choice(topic.subjects)
            q, cat = self._fresh(P.QUESTIONS, s, self.first(b))
            ans = self._answer(cat)
            if r.random() < 0.8:
                ans += " " + self._statement(topic, s)
            out = [(a, q), (b, ans)]
            if r.random() < 0.15:
                out.append((a, r.choice(P.ACKS)))
            return out
        if x < 0.55 and self.last:
            a = self.pick_speaker(topic)
            lead = r.choice(P.BUILDS + P.SOFT_DISAGREE[:3])
            lead = lead.replace("{n}", self.first(self.last) if self.last != a else "everyone")
            st = self._statement(topic)
            if not lead.endswith(". ") and not lead.endswith("? "):
                st = lower_first(st)
            if r.random() < 0.5:
                st += " " + self._statement(topic)
            return [(a, lead + st)]
        for kind, pool in (("meta", self.meta), ("dig", self.dig), ("cross", self.cross)):
            if self._event_ok(kind, pool) and r.random() < {"meta": 0.12, "dig": 0.05, "cross": 0.06}[kind]:
                return self._seq(pool.pop(), topic, kind)
        if x < 0.58:
            return [(self.chair, r.choice(P.PROCESS))]
        a = self.pick_speaker(topic)
        n = r.choices([1, 2, 3, 4], weights=[1, 4, 5, 3])[0]
        sents, subj = [], r.choice(topic.subjects)
        for i in range(n):
            if i and r.random() < 0.25:
                tl = self._topic_line(topic, a)
                if tl:
                    sents.append(tl)
                    continue
            sents.append(self._statement(topic, subj if i == 0 or r.random() < 0.5 else None))
        out = [(a, self._disfluent(" ".join(sents)))]
        if r.random() < 0.12:
            out.append((self.pick_speaker(topic, exclude=(a,)), r.choice(P.ACKS)))
        return out

    def _seq(self, seq, topic: Topic, kind: str):
        self.budget[kind] -= 1
        self.last_event[kind] = self.t
        a = self.pick_speaker(topic)
        b = self.pick_speaker(topic, exclude=(a,))
        c = self.chair if self.chair not in (a, b) else self.pick_speaker(topic, exclude=(a, b))
        roles = {"A": a, "B": b, "C": c}
        out = []
        for role, text in seq:
            text = text.replace("{nA}", self.first(a)).replace("{nB}", self.first(b))
            out.append((roles[role], text))
        return out

    def fill(self, until: float, topic: Topic, min_gap: float = 8.0) -> None:
        guard = 0
        while until - self.t > min_gap and guard < 3000:
            guard += 1
            remaining = until - self.t
            block = self._block(topic)
            est = sum(len(t.split()) / self.wps + 1.0 for _, t in block)
            if est > remaining:
                if remaining > 12:
                    k = self.pick_speaker(topic)
                    st = self._statement(topic)
                    if len(st.split()) / self.wps + 1.0 <= remaining:
                        self.say(k, st)
                        continue
                if remaining > 4:
                    self.say(self.pick_speaker(topic), self.r.choice(P.ACKS))
                break
            for k, t in block:
                self.say(k, t)
        self.wait_until(until)

    def script(self, at_sec: float, topic: Topic, turns: list) -> list[int]:
        """Fill with talk until at_sec, then emit scripted turns: (key, text) or (key, text, fact)."""
        self.fill(at_sec, topic)
        out = []
        for tr in turns:
            out.append(self.say(*tr))
        return out

    def words(self) -> int:
        n = 0
        for i in self.speech_lines:
            ln = self.doc.lines[i - 1]
            body = re.sub(r"^\[\d\d:\d\d:\d\d\] [^:]+: ", "", ln)
            n += len(body.split())
        return n
