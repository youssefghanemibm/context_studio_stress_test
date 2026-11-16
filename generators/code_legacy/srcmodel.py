"""History-aware source model.

Every generated file is a list of ``Line`` objects. A line may carry ``add`` (the commit that
introduced it; ``None`` = present when the file was created) and ``rm`` (the commit that removed
it). Rendering a file "as of" a set of applied commits gives that version's text, so the final
content, every earlier version and the before/after snippets in history.yaml all come from the
same source and cannot drift apart.

Fixed-format files (COBOL programs and copybooks) get sequence numbers in columns 1-6: lines
present at creation are numbered in steps of 100; lines added later get intermediate numbers,
the way ISPF numbers inserted lines; a 1:1 replacement keeps the number of the line it replaces.
"""
from __future__ import annotations

import contextlib
import difflib
import re
import unicodedata
from dataclasses import dataclass, field

COBOL_TEXT_WIDTH = 66          # columns 7..72


@dataclass
class Line:
    text: str
    add: str | None = None
    rm: str | None = None
    keep_seq: bool = False
    tag: str = ""                # columns 73-80 (fixed format only)
    marks: list = field(default_factory=list)


_ASCII_MAP = {"–": "-", "—": "-", "≥": ">=", "≤": "<=", "±": "+/-", "’": "'", "‘": "'", "“": '"',
              "”": '"', "×": "x", "→": "->", "£": "GBP ", "ø": "o", "Ø": "O", "å": "a", "Å": "A",
              "æ": "ae", "Æ": "AE", "ö": "o", "Ö": "O", "ä": "a", "Ä": "A", "é": "e", "ó": "o",
              "≈": "~", "…": "..."}


def ascii_text(s: str) -> str:
    out = []
    for ch in str(s):
        if ord(ch) < 128:
            out.append(ch)
        elif ch in _ASCII_MAP:
            out.append(_ASCII_MAP[ch])
        else:
            d = unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode()
            out.append(d)
    return re.sub(r"GBP\s+(?=\d)", "GBP ", "".join(out))


class Src:
    """An append-only list of lines plus a stack of 'current commit' tags."""

    def __init__(self, fixed: bool = False):
        self.fixed = fixed
        self.lines: list[Line] = []
        self._add: list[str | None] = [None]
        self._rm: list[str | None] = [None]
        self._tag: list[str] = [""]
        self._pending_marks: list[str] = []

    # -- emission ----------------------------------------------------------------------------
    def emit(self, text: str, *, add: str | None = None, rm: str | None = None, keep_seq=False,
             tag: str | None = None, mark: str | list | None = None) -> Line:
        text = text.rstrip()
        if self.fixed:
            if len(text) > COBOL_TEXT_WIDTH:
                raise ValueError(f"fixed-format line too long ({len(text)}): {text!r}")
        ln = Line(text=text,
                  add=add if add is not None else self._add[-1],
                  rm=rm if rm is not None else self._rm[-1],
                  keep_seq=keep_seq,
                  tag=tag if tag is not None else self._tag[-1])
        if self._pending_marks:
            ln.marks.extend(self._pending_marks)
            self._pending_marks = []
        if mark:
            ln.marks.extend([mark] if isinstance(mark, str) else list(mark))
        self.lines.append(ln)
        return ln

    def mark_next(self, name: str) -> None:
        self._pending_marks.append(name)

    def mark_last(self, name: str) -> None:
        self.lines[-1].marks.append(name)

    def extend(self, other: "Src") -> None:
        for ln in other.lines:
            self.lines.append(Line(ln.text, ln.add if ln.add is not None else self._add[-1],
                                   ln.rm if ln.rm is not None else self._rm[-1], ln.keep_seq,
                                   ln.tag or self._tag[-1], list(ln.marks)))

    @contextlib.contextmanager
    def added(self, commit: str | None, tag: str = ""):
        if commit is None:
            yield
            return
        self._add.append(commit)
        self._tag.append(tag)
        try:
            yield
        finally:
            self._add.pop()
            self._tag.pop()

    @contextlib.contextmanager
    def removed(self, commit: str | None):
        if commit is None:
            yield
            return
        self._rm.append(commit)
        try:
            yield
        finally:
            self._rm.pop()

    def replace(self, old: str, new: str, commit: str, tag: str = "", mark=None) -> None:
        """Emit ``old`` (removed by ``commit``) and ``new`` (added by it, same sequence number)."""
        self.emit(old, rm=commit)
        self.emit(new, add=commit, keep_seq=True, tag=tag, mark=mark)

    # -- rendering ---------------------------------------------------------------------------
    def commits(self) -> list[str]:
        out = []
        for ln in self.lines:
            for c in (ln.add, ln.rm):
                if c and c not in out:
                    out.append(c)
        return out

    def _seq_numbers(self) -> list[int]:
        seqs: list[int | None] = [None] * len(self.lines)
        base = [i for i, ln in enumerate(self.lines) if ln.add is None]
        for n, i in enumerate(base, 1):
            seqs[i] = n * 100
        # lines added later: intermediate numbers between the surrounding base lines
        i = 0
        L = len(self.lines)
        while i < L:
            if seqs[i] is not None:
                i += 1
                continue
            j = i
            while j < L and seqs[j] is None:
                j += 1
            prev = seqs[i - 1] if i > 0 else 0
            group = list(range(i, j))
            free = [k for k in group if not self.lines[k].keep_seq]
            nxt = seqs[j] if j < L else prev + 100
            gap = nxt - prev
            if len(free) >= gap:
                raise ValueError(f"too many inserted lines ({len(free)}) between {prev} and {nxt}")
            step = max(1, gap // (len(free) + 1))
            if step >= 10:
                step = (step // 10) * 10
            cur = prev
            for k in group:
                if self.lines[k].keep_seq and k > 0:
                    seqs[k] = seqs[k - 1] if seqs[k - 1] is not None else cur
                else:
                    cur += step
                    seqs[k] = cur
            i = j
        for k, ln in enumerate(self.lines):       # base lines may also keep_seq (rare)
            if ln.keep_seq and ln.add is None and k > 0:
                seqs[k] = seqs[k - 1]
        return [int(s) for s in seqs]

    def render(self, applied: set[str] | frozenset) -> tuple[str, list[int]]:
        """(text, index_of_rendered_lines) for the version with ``applied`` commits."""
        seqs = self._seq_numbers() if self.fixed else None
        out, idx = [], []
        for k, ln in enumerate(self.lines):
            if ln.add is not None and ln.add not in applied:
                continue
            if ln.rm is not None and ln.rm in applied:
                continue
            if self.fixed:
                body = f"{seqs[k]:06d}" + ln.text
                if ln.tag:
                    body = body.ljust(72) + ln.tag[:8]
                out.append(body.rstrip())
            else:
                out.append(ln.text)
            idx.append(k)
        return "".join(s + "\n" for s in out), idx

    def mark_lines(self, applied) -> dict[str, list[int]]:
        """mark -> sorted 1-based line numbers in the rendered version."""
        _, idx = self.render(applied)
        pos = {k: n for n, k in enumerate(idx, 1)}
        out: dict[str, list[int]] = {}
        for k, ln in enumerate(self.lines):
            if k in pos:
                for m in ln.marks:
                    out.setdefault(m, []).append(pos[k])
        return out


# ---------------------------------------------------------------------------------------------
# before/after hunks for history.yaml
# ---------------------------------------------------------------------------------------------

def _join(lines: list[str]) -> str:
    return "".join(s + "\n" for s in lines)


def hunks(before: str, after: str, min_context: int = 1) -> list[tuple[str, str]]:
    """Minimal (before, after) snippet pairs that turn ``before`` into ``after``.

    Each pair carries enough context lines that ``after`` occurs exactly once in the after-text
    and ``before`` exactly once in the before-text. Overlapping hunks are merged.
    """
    a = before.splitlines()
    b = after.splitlines()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
    if not ops:
        return []
    # (a_start, a_end, b_start, b_end) with context, then grow until unique, then merge
    spans = [[i1, i2, j1, j2] for _, i1, i2, j1, j2 in ops]

    def grow(s, c):
        i1, i2, j1, j2 = s
        lo = min(c, i1, j1)
        hi = min(c, len(a) - i2, len(b) - j2)
        return [i1 - lo, i2 + hi, j1 - lo, j2 + hi]

    out_spans = []
    for s in spans:
        c = min_context
        while True:
            g = grow(s, c)
            bs, as_ = _join(a[g[0]:g[1]]), _join(b[g[2]:g[3]])
            ok_b = bs == "" or before.count(bs) == 1
            ok_a = as_ == "" or after.count(as_) == 1
            if (ok_a and ok_b and bs and as_) or (g[0] == 0 and g[1] == len(a) and g[2] == 0 and g[3] == len(b)):
                break
            c += 1
            if c > 400:
                raise RuntimeError("could not make hunk unique")
        out_spans.append(g)
    merged = [out_spans[0]]
    for g in out_spans[1:]:
        m = merged[-1]
        if g[0] <= m[1] or g[2] <= m[3]:
            m[1] = max(m[1], g[1])
            m[3] = max(m[3], g[3])
        else:
            merged.append(g)
    res = []
    for g in merged:
        res.append((_join(a[g[0]:g[1]]), _join(b[g[2]:g[3]])))
    return res
