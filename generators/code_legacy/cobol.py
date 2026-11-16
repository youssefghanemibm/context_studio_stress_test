"""CLARA COBOL program generator (fixed format, DB2 / CICS).

One ``ProgramGen`` per program in programs.yaml. The generator is data-driven:

* EXEC SQL statements touch exactly the tables in ``reads_tables`` (SELECT / cursors) and
  ``writes_tables`` (INSERT / UPDATE / DELETE). Where a writer needs a value back from a table it
  does not read, it uses a DB2 data-change table reference (SELECT ... FROM OLD/FINAL TABLE
  (UPDATE ...)), so no SELECT ever names a write-only table.
* CALL statements are exactly ``calls_programs``; COPY statements exactly ``copybooks``.
* Programs with placements get named paragraphs (see SPECIAL_*), everything else gets a generic
  but varied structure, and filler paragraphs (field edits, report formatting) bring the source
  to its target length (150-900 lines).
* Lines introduced or removed by later commits are tagged so history.yaml can be derived.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from generators.common import util

from . import naming
from .srcmodel import Src, ascii_text

AUDIT_COLS = {"LAST_UPD_TS", "LAST_UPD_PGM", "LAST_UPD_USER"}
TS_NOW_COLS = {"LAST_UPD_TS", "CREATED_TS", "MOVE_TS", "AUDIT_TS", "RUN_TS", "REF_TS", "SCORE_TS",
               "TRIAGE_TS", "RECEIVED_TS", "NOTE_TS", "APPOINTED_TS", "BOOKED_TS"}

# table -> write verb (defaults) and per-program overrides
DEFAULT_OP = {"CLR.T_CLAIM": "UPDATE", "CLR.T_RESERVE": "UPDATE", "CLR.T_GL_PERIOD": "UPDATE",
              "CLR.T_CODE_LOOKUP": "UPDATE"}
OP_OVERRIDE = {
    ("CLRFN030", "CLR.T_CLAIM"): "INSERT", ("CLRFN030", "CLR.T_RESERVE"): "INSERT",
    ("CLRRS010", "CLR.T_RESERVE"): "INSERT", ("CLRFN070", "CLR.T_FNOL_EVENT"): "UPDATE",
    ("CLRRC040", "CLR.T_SUBROGATION_CASE"): "UPDATE", ("CLRST110", "CLR.T_VENDOR_INVOICE"): "UPDATE",
    ("CLRST040", "CLR.T_SETTLEMENT"): "UPDATE", ("CLRST050", "CLR.T_PAYMENT"): "UPDATE",
    ("CLRST070", "CLR.T_PAYMENT"): "UPDATE", ("CLRST090", "CLR.T_PAYMENT"): "UPDATE",
    ("CLRST030", "CLR.T_PAYMENT"): "UPDATE", ("CLRFR050", "CLR.T_FRAUD_REFERRAL"): "UPDATE",
    ("CLRFR060", "CLR.T_FRAUD_REFERRAL"): "UPDATE", ("CLRFR120", "CLR.T_FRAUD_NOTIFICATION"): "UPDATE",
    ("CLRAS080", "CLR.T_ASSESSMENT"): "UPDATE", ("CLRRS040", "CLR.T_RESERVE_AUTHORITY"): "UPDATE",
    ("CLRST060", "CLR.T_PAYEE"): "UPDATE", ("CLRCM140", "CLR.T_CLAIM"): "DELETE",
    ("CLRCM140", "CLR.T_NOTE"): "DELETE", ("CLRCM140", "CLR.T_DOCUMENT_REF"): "DELETE",
    ("CLRCM130", "CLR.T_INTERFACE_LOG"): "DELETE", ("CLRRS170", "CLR.T_RESERVE_MOVEMENT"): "UPDATE",
    ("CLRFR110", "CLR.T_FRAUD_SCORE"): "INSERT", ("CLRCM020", "CLR.T_AUDIT"): "INSERT",
}
# preferred SET columns for UPDATEs (pid, table) -> [(col, value-expr or None for host var)]
UPDATE_SET = {
    ("CLRFN090", "CLR.T_CLAIM"): [("LOSS_DT", None), ("LOSS_DESC", None), ("CLAIM_STATUS", "'RO'")],
    ("CLRRC010", "CLR.T_CLAIM"): [("RECOVERY_FLAG", "'Y'")],
    ("CLRTR020", "CLR.T_CLAIM"): [("TIER_CD", None)],
    ("CLRFR140", "CLR.T_CLAIM"): [("CLAIM_STATUS", None), ("CLOSED_DT", "CURRENT DATE")],
    ("CLRST040", "CLR.T_CLAIM"): [("CLAIM_STATUS", "'CS'"), ("CLOSED_DT", "CURRENT DATE")],
    ("CLRST040", "CLR.T_SETTLEMENT"): [("FINAL_FLAG", "'Y'"), ("ACCEPTED_DT", None)],
    ("CLRFN070", "CLR.T_FNOL_EVENT"): [("ACK_SENT_TS", "CURRENT TIMESTAMP")],
    ("CLRRC040", "CLR.T_SUBROGATION_CASE"): [("CASE_STATUS", None), ("SUBTRAK_REF", None)],
    ("CLRST110", "CLR.T_VENDOR_INVOICE"): [("MATCHED_FLAG", "'Y'")],
    ("CLRST050", "CLR.T_PAYMENT"): [("PAY_STATUS", "'CF'")],
    ("CLRST070", "CLR.T_PAYMENT"): [("SANCTIONS_RESULT", None), ("PAY_STATUS", "'SC'")],
    ("CLRST090", "CLR.T_PAYMENT"): [("PAY_STATUS", "'CX'"), ("COMMENT_TXT", None)],
    ("CLRST030", "CLR.T_PAYMENT"): [("PAY_STATUS", "'SN'")],
    ("CLRFR050", "CLR.T_FRAUD_REFERRAL"): [("OUTCOME_CD", None), ("OUTCOME_DT", "CURRENT DATE"),
                                           ("REF_STATUS", "'CL'")],
    ("CLRAS080", "CLR.T_ASSESSMENT"): [("COVER_DECISION_CD", None)],
    ("CLRRS040", "CLR.T_RESERVE_AUTHORITY"): [("APPROVER_USER", None), ("DECISION_CD", None)],
    ("CLRST060", "CLR.T_PAYEE"): [("PAYEE_NAME", None), ("IBAN", None), ("SORT_CODE", None)],
    ("CLRGL020", "CLR.T_GL_PERIOD"): [("PERIOD_STATUS", "'C'"), ("CLOSED_TS", "CURRENT TIMESTAMP"),
                                      ("CLOSED_BY", None)],
    ("CLRRS200", "CLR.T_CODE_LOOKUP"): [("CODE_DESC_EN", None), ("CODE_DESC_LOCAL", None),
                                        ("ACTIVE_FLAG", None)],
    ("CLRTR020", "CLR.T_CLAIM_TIER"): [],
}
DRIVE_WHERE = {
    "CLR.T_CLAIM": ["CLAIM_STATUS IN ('OP', 'RO', 'RC')"],
    "CLR.T_RESERVE": ["RSV_STATUS = 'O'"],
    "CLR.T_RESERVE_MOVEMENT": ["EXTRACTED_FLAG = 'N'"],
    "CLR.T_PAYMENT": ["PAY_STATUS = :WS-SELECT-STATUS"],
    "CLR.T_FRAUD_SCORE": ["SCORE_TS >= :WS-LAST-RUN-TS"],
    "CLR.T_FNOL_EVENT": ["RECEIVED_TS >= :WS-LAST-RUN-TS"],
    "CLR.T_CLAIM_TIER": ["TIER_CD = '3'"],
    "CLR.T_SUBROGATION_CASE": ["CASE_STATUS <> 'WO'"],
    "CLR.T_RECOVERY": ["RCV_STATUS IN ('OP', 'PT')"],
    "CLR.T_GL_PERIOD": ["PERIOD_STATUS = 'O'"],
    "CLR.T_CURRENCY_RATE": ["RATE_DT = :WS-RATE-DT"],
}
LOOKUP_ONLY = {"CLR.T_PARAM", "CLR.T_CODE_LOOKUP", "CLR.T_USER", "CLR.T_CURRENCY_RATE"}

CALL_PURPOSE = {
    "CLRCM010": "BUSINESS-DAY / DATE ARITHMETIC", "CLRCM020": "AUDIT TRAIL ENTRY",
    "CLRCM030": "CURRENCY CONVERSION TO GBP", "CLRCM040": "PARAMETER READ (CLR.T_PARAM)",
    "CLRCM050": "ERROR HANDLER", "CLRCM060": "CODE LOOKUP", "CLRCM070": "USER AUTHORITY CHECK",
    "CLRCM080": "CLAIM NOTE", "CLRCM090": "DIARY ENTRY", "CLRCM100": "DOCUMENT REFERENCE",
    "CLRCM110": "MQ PUT", "CLRCM120": "MQ GET", "CLRRS015": "RESERVE AUTHORITY CHECK",
}


def _cols(W, table):
    return W.tables[table]["columns"]


def is_identity(W, table, col) -> bool:
    t = W.tables[table]
    pk = t["primary_key"]
    c = next(c for c in t["columns"] if c["name"] == col)
    return len(pk) == 1 and pk[0] == col and c["type"] == "BIGINT"


def pack(items: list[str], first: str, cont: str, width: int, sep: str = ", ") -> list[str]:
    """Pack items into lines: first line starts with ``first``, continuation lines with ``cont``."""
    lines, cur = [], first
    for i, it in enumerate(items):
        piece = it if i == 0 else sep.strip() + " " + it if cur.strip() == "" else sep + it
        if i == 0:
            piece = it
        if len(cur) + len(piece) > width and cur.strip() not in ("", first.strip()):
            lines.append(cur.rstrip())
            cur = cont + sep.strip() + " " + it
        else:
            cur = cur + (piece if i == 0 else sep + it)
    lines.append(cur.rstrip())
    return lines


@dataclass
class Para:
    name: str
    body: callable
    add: str | None = None
    comment: str = ""
    rm: str | None = None


@dataclass
class Fact:
    fid_suffix: str
    marks: tuple            # (start_mark, end_mark)
    needle: str
    statement: str
    kind: str = "code_fact"
    world_ref: str | None = None
    placement: str | None = None
    variant: str = "a"
    extra: dict = field(default_factory=dict)


class ProgramGen:
    def __init__(self, W, pid: str, ctx: dict):
        self.W = W
        self.pid = pid
        self.p = W.programs[pid]
        self.ctx = ctx                      # shared: commits info, late features, etc.
        self.r = util.rng(f"code_legacy:cobol:{pid}")
        self.src = Src(fixed=True)
        self.kind = "sub" if self.p["subprogram"] else ("online" if self.p["type"] == "online" else "batch")
        self.reads = list(self.p["reads_tables"])
        self.writes = list(self.p["writes_tables"])
        self.calls = list(self.p["calls_programs"])
        self.cpys = list(self.p["copybooks"])
        self.late = ctx.get("late", {}).get(pid, {})           # {'tables': {t: commit}, 'cpys': {c: commit}}
        self.c_change = pid == "CLRFR040"                        # CM-09 rewrite in variant c
        self.facts: list[Fact] = []
        self.files = naming.batch_files(self.p) if self.kind == "batch" else []
        if pid == "CLRRS150":
            self.files.append({"dd": "IMPIN", "dir": "in", "lrecl": 200, "desc": "MOVEMENT CORRECTION REQUESTS"})
        self.bms = self._bms()
        self.old_style = self.p["since"] < "2001-01-01" and self.r.random() < 0.55
        self.ind = 4 if self.r.random() < 0.6 else 3
        self.boxed_paras = self.r.random() < 0.5
        self.commit_freq = self.r.choice([100, 200, 250, 500, 1000])
        self.hv = self._host_vars()
        self.para_no = {}
        self.target = self._target_lines()
        self.msgs: list[str] = []

    # ------------------------------------------------------------------ basics
    def _target_lines(self) -> int:
        loc = self.p["loc"]
        t = 150 + (loc - 171) * 720 / (4161 - 171)
        t *= 1 + self.r.uniform(-0.04, 0.04)
        return int(max(160, min(880, t)))

    def _bms(self):
        m = self.p.get("bms_map")
        return self.W.bms_maps[m] if m else None

    def _host_vars(self):
        """table -> {col: host field}; plus ambiguity set."""
        out, seen, dup = {}, {}, set()
        for cp in self.cpys:
            c = self.W.copybooks[cp]
            for f in c["fields"][1:]:
                if f["name"] in seen and seen[f["name"]] != cp:
                    dup.add(f["name"])
                seen.setdefault(f["name"], cp)
            if c["table"]:
                t = self.W.tables[c["table"]]
                fields = [f["name"] for f in c["fields"][1:]]
                cols = [x["name"] for x in t["columns"]]
                pre = fields[0][: -len(cols[0].replace("_", "-")) - 1]
                out[c["table"]] = {col: pre + "-" + col.replace("_", "-") for col in cols}
                out[c["table"]]["__rec"] = c["fields"][0]["name"]
        self.dup = dup
        return out

    def hv_ref(self, table, col, sql=True) -> str:
        f = self.hv[table][col]
        if f in self.dup:
            rec = self.hv[table]["__rec"]
            return f":{rec}.{f}" if sql else f"{f} OF {rec}"
        return f":{f}" if sql else f

    # ------------------------------------------------------------------ emission helpers
    def c(self, text: str = "", **kw):
        if len(text) > 64:
            rest = {k: v for k, v in kw.items() if k not in ("mark", "keep_seq")}
            for i, piece in enumerate(self._wrap(text, 64)):
                self.src.emit("* " + piece, **(kw if i == 0 else rest))
            return
        self.src.emit("*" + ((" " + text) if text else ""), **kw)

    def a(self, text: str, **kw):
        self.src.emit(" " + text, **kw)

    def b(self, text: str, lvl: int = 0, **kw):
        line = " " + "    " + " " * (self.ind * lvl) + text
        if len(line) > 66:
            self.bw(text, lvl, **kw)
        else:
            self.src.emit(line, **kw)

    def bw(self, text: str, lvl: int = 0, **kw):
        """Area-B statement, wrapped at spaces outside literals."""
        lead = len(text) - len(text.lstrip())
        pre = " " + "    " + " " * (self.ind * lvl) + " " * min(lead, 16)
        text = text.lstrip()
        width = 66
        if len(pre + text) <= width:
            self.src.emit(pre + text, **kw)
            return
        rest_kw = {k: v for k, v in kw.items() if k not in ("mark", "keep_seq")}
        toks = re.findall(r"'[^']*'\S*|\S+", text)
        cur = pre
        first = True
        cont = pre + "    "
        for t in toks:
            if cur.strip() and len(cur) + 1 + len(t) > width:
                self.src.emit(cur, **(kw if first else rest_kw))
                first = False
                cur = cont + t
            else:
                cur = cur + ("" if cur == pre or cur == cont else " ") + t
        self.src.emit(cur, **(kw if first else rest_kw))

    def box(self, lines: list[str], ch: str = "-", **kw):
        self.c(ch * 63 + "*", **kw)
        for ln in lines:
            for piece in self._wrap(ln, 62):
                self.c(piece.ljust(62) + " *", **kw)
        self.c(ch * 63 + "*", **kw)

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        if len(text) <= width:
            return [text]
        ind = " " * (len(text) - len(text.lstrip()))
        words = text.split()
        out, cur = [], ind
        for w in words:
            if len(cur) + len(w) + 1 > width and cur.strip():
                out.append(cur)
                cur = ind + "  " + w
            else:
                cur = (cur + " " + w) if cur.strip() else ind + w
        out.append(cur)
        return out or [""]

    def sql(self, lines: list, lvl: int = 0, mark=None, **kw):
        """EXEC SQL block. ``lines`` items are str or (str, mark); ``mark`` goes on the statement line."""
        self.b("EXEC SQL", lvl, **kw)
        for i, ln in enumerate(lines):
            m = None
            if isinstance(ln, tuple):
                ln, m = ln
            if i == 0 and mark:
                m = [mark] + ([m] if m else [])
            self.b("    " + ln, lvl, mark=m, **kw)
        self.b("END-EXEC", lvl, **kw)

    # ------------------------------------------------------------------ descriptions
    def desc(self, when_commit_applied=True) -> str:
        return ascii_text(self.p["description"]).upper()

    # ------------------------------------------------------------------ header
    def maintenance_entries(self) -> list[tuple]:
        """[(date, by, ref, text, add_commit, rm_commit)]"""
        p, r = self.p, self.r
        ents = []
        since = p["since"]
        owner = p["owner_person"]

        def tag_for(pid, d):
            if pid in naming.AUTHOR_FROM and d >= naming.AUTHOR_FROM[pid] and d <= naming.AUTHOR_TO.get(pid, "9999"):
                return naming.AUTHOR_TAG[pid]
            return None

        creator = tag_for(owner, since) or (tag_for("P023", since) if since >= "1996-03-11" else None) or "CLRPROJ"
        first = "INITIAL VERSION" if since > "1994-10-03" else "INITIAL VERSION - CLARA GO-LIVE"
        if self.pid in self.ctx["created_by"] and self.ctx["created_by"][self.pid] != "CM-01":
            pass
        ents.append((since, creator, self.ctx.get("create_ref", {}).get(self.pid, ""), first, None, None))
        # generic historical maintenance (pre-import only)
        bank = [
            ("1998-06-01", "1999-11-30", "Y2K: 4-DIGIT YEARS IN DATE WORK AREAS"),
            ("1998-09-01", "1999-10-31", "Y2K REMEDIATION - DATE WINDOWING REMOVED"),
            ("2002-03-01", "2004-12-31", "SQLCODE HANDLING ROUTED THROUGH CLRERR01"),
            ("2005-01-01", "2008-12-31", "RECOMPILED - COBOL FOR Z/OS UPGRADE"),
            ("2009-02-01", "2012-12-31", "DATE ARITHMETIC MOVED TO CLRCM010"),
            ("2010-01-01", "2014-12-31", "DB2 VERSION MIGRATION - REBIND, NO LOGIC CHANGE"),
            ("2011-01-01", "2016-12-31", "COMMIT FREQUENCY TUNED FOR BATCH WINDOW"),
            ("2013-01-01", "2017-12-31", "ERROR MESSAGES STANDARDISED"),
            ("2015-01-01", "2019-12-31", "PERFORMANCE: CURSOR WITH HOLD, FEWER COMMITS"),
            ("2017-01-01", "2020-12-31", "RECOMPILED UNDER ENTERPRISE COBOL V6"),
            ("2019-01-01", "2023-06-30", "REMOVED DEAD CODE AFTER REVIEW"),
            ("2021-02-01", "2024-11-30", "NORDIC CURRENCY CODES VALIDATED"),
            ("2022-01-01", "2024-12-31", "REPORT HEADINGS REALIGNED"),
            ("2023-01-01", "2024-12-20", "SQL WARNINGS LOGGED, NOT TREATED AS ERRORS"),
        ]
        if self.kind == "online":
            bank += [("2006-01-01", "2012-12-31", "PF12 CANCEL HANDLING ADDED"),
                     ("2014-01-01", "2020-12-31", "CURSOR POSITIONING ON VALIDATION ERRORS")]
        if self.kind == "sub":
            bank += [("2016-01-01", "2023-12-31", "LINKAGE CHECKS ON MANDATORY PARAMETERS")]
        n = r.randint(1, 5)
        picks = r.sample(bank, min(n, len(bank)))
        for lo, hi, text in picks:
            lo = max(lo, since)
            if lo >= hi or lo >= "2025-02-20":
                continue
            d0 = util.rng(f"{self.pid}:{text}").randint(0, 3000)
            import datetime as _dt
            lo_d = _dt.date.fromisoformat(lo)
            hi_d = min(_dt.date.fromisoformat(hi), _dt.date(2025, 2, 14))
            if hi_d <= lo_d:
                continue
            dd = lo_d + _dt.timedelta(days=d0 % max(1, (hi_d - lo_d).days))
            ds = dd.isoformat()
            who = [pid for pid in ("P023", "P024", "P016", "P025") if tag_for(pid, ds)]
            if owner in who and r.random() < 0.7:
                by = naming.AUTHOR_TAG[owner]
            elif who:
                by = naming.AUTHOR_TAG[r.choice(who)]
            else:
                by = "CLRPROJ"
            ents.append((ds, by, "", text, None, None))
        if self.pid == "CLRFR040":
            ents.append(("2023-03-28", "PASHW01", "", "REFERRAL THRESHOLD 075 -> 070 (BR-FRD-012 V2)", None, None))
        rf = self.p.get("renamed_from")
        if rf and rf["date"] < "2025-02-21":
            ents.append((rf["date"], tag_for(owner, rf["date"]) or "KBARR01", "",
                         f"RENAMED FROM {rf['old_id']}", None, None))
        ents.extend(self.ctx.get("maint_extra", {}).get(self.pid, []))
        ents.sort(key=lambda e: e[0])
        # de-duplicate same date
        out, seen = [], set()
        for e in ents:
            k = (e[0], e[3])
            if k not in seen:
                seen.add(k)
                out.append(e)
        return out

    def header(self):
        p = self.p
        r = self.r
        right = self.r.random() < 0.65

        def hl(text="", **kw):
            pieces = [""]
            if text:
                m = re.match(r"^([A-Z /]+?\s*:\s)(.*)$", text)
                if m and len(text) > 62 and len(m.group(1)) <= 14:
                    lab = m.group(1).ljust(13)
                    body = self._wrap(m.group(2), 62 - len(lab))
                    pieces = [lab + body[0].strip()] + [" " * len(lab) + b.strip() for b in body[1:]]
                else:
                    pieces = self._wrap(text, 62)
            for i, piece in enumerate(pieces):
                kk = kw if i == 0 else {k: v for k, v in kw.items() if k not in ("mark", "keep_seq")}
                if right:
                    self.c(piece.ljust(62) + " *", **kk)
                else:
                    self.c(piece, **kk)

        self.c("=" * 63 + ("*" if right else "="))
        pid_line_new = f"PROGRAM    : {self.pid}"
        rf = p.get("renamed_from")
        if rf and rf["date"] >= "2025-02-21":
            old = f"PROGRAM    : {rf['old_id']}"
            self.src.emit("* " + (old.ljust(62) + " *" if right else old), rm="XC-01")
            self.src.emit("* " + (pid_line_new.ljust(62) + " *" if right else pid_line_new), add="XC-01", keep_seq=True)
        else:
            hl(pid_line_new)
        title = self.desc()
        if rf and rf["date"] >= "2025-02-21":
            old_title = title.replace("SENTINEL", "FRAUDNET")
            for piece_old, piece_new in zip(self._wrap("TITLE      : " + old_title, 62), self._wrap("TITLE      : " + title, 62)):
                o = piece_old.ljust(62) + " *" if right else piece_old
                n = piece_new.ljust(62) + " *" if right else piece_new
                if o != n:
                    self.src.emit("* " + o, rm="XC-01")
                    self.src.emit("* " + n, add="XC-01", keep_seq=True)
                else:
                    self.src.emit("* " + n)
        elif self.pid == "CLRFR140":
            base = title.split(" - DISABLED")[0].split(" – DISABLED")[0]
            base = re.sub(r"\s*-\s*DISABLED.*$", "", base)
            hl("TITLE      : " + base)
            with self.src.added("XC-06"):
                hl("STATUS     : DISABLED 2026-04-01 (BR-FRD-019 WITHDRAWN, CHUB-207)")
        elif self.pid == "CLRRS210":
            hl("TITLE      : " + title.replace(" (2026-03-02 TO 2026-08-28)", ""))
            hl("PERIOD     : PARALLEL RUN 2026-03-02 TO 2026-08-28")
            with self.src.added("XC-09"):
                hl("STATUS     : RETIRED - REMOVED FROM SCHEDULE AFTER THE PARALLEL")
                hl("             RUN ENDED ON 2026-08-28")
        else:
            hl("TITLE      : " + title)
        hl("SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION")
        hl(f"AREA       : {p['area']}")
        if self.kind == "batch":
            hl("TYPE       : BATCH / DB2")
            if p.get("jcl_job"):
                step = self.ctx["job_step"].get(self.pid, "")
                hl(f"JOB / STEP : {p['jcl_job']} / {step}")
        elif self.kind == "online":
            hl("TYPE       : CICS ONLINE / DB2")
            hl(f"TRANSACTION: {p['cics_transaction']}")
            if self.bms:
                hl(f"MAP        : {self.bms['map']} (MAPSET {self.bms['mapset']})")
        else:
            hl("TYPE       : CALLED SUBPROGRAM (STATIC CALL, NO CICS COMMANDS)")
        self.c("-" * 63 + ("*" if right else "-"))
        hl("PURPOSE")
        for ln in self.purpose_lines():
            hl("  " + ln)
        self.c("-" * 63 + ("*" if right else "-"))
        hl("DB2 TABLES")
        acc = {}
        for t in self.reads:
            acc.setdefault(t, []).append("READ")
        for t in self.writes:
            acc.setdefault(t, []).append(self.op_for(t))
        for t, ops in acc.items():
            lc = self.late.get("tables", {}).get(t)
            with self.src.added(lc):
                hl(f"  {t:<28}{' / '.join(ops)}")
        if self.c_change:
            pass
        # copybooks
        cpl = []
        for cp in self.cpys:
            cpl.append((cp, self.late.get("cpys", {}).get(cp)))
        self._list_lines(hl, "COPYBOOKS  : ", [c for c, lc in cpl if lc is None])
        for cp, lc in cpl:
            if lc:
                with self.src.added(lc):
                    hl(f"             {cp} (ADDED {self.ctx['commit_date'][lc]})")
        if self.c_change:
            with self.src.added("CM-09"):
                hl("             PARMREC1 (ADDED 2026-11-12)")
        if self.calls or self.c_change:
            self._list_lines(hl, "CALLS      : ", self.calls)
            if self.c_change:
                with self.src.added("CM-09"):
                    hl("             CLRCM040 (ADDED 2026-11-12)")
        else:
            hl("CALLS      : NONE")
        for f in self.files:
            hl(f"FILE       : {f['dd']:<8} {f['dir'].upper():<3} {f['desc']}")
        self.c("-" * 63 + ("*" if right else "-"))
        hl("MAINTENANCE HISTORY")
        hl("DATE       BY       REF        DESCRIPTION")
        hl("---------- -------- ---------- " + "-" * 31)
        for d, by, ref, text, addc, rmc in self.maintenance_entries():
            pieces = self._wrap(text, 31)
            with self.src.added(addc):
                with self.src.removed(rmc):
                    for i, pc in enumerate(pieces):
                        pc = pc.strip()
                        if i == 0:
                            hl(f"{d} {by:<8} {ref:<10} {pc}")
                        else:
                            hl(f"{'':31}{pc}")
        self.c("=" * 63 + ("*" if right else "="))

    def _list_lines(self, hl, label, items):
        cur = label
        lines = []
        for it in items:
            if len(cur) + len(it) + 1 > 62:
                lines.append(cur.rstrip())
                cur = " " * len(label)
            cur += it + " "
        lines.append(cur.rstrip())
        for ln in lines:
            hl(ln)

    def purpose_lines(self) -> list[str]:
        p, r = self.p, self.r
        d = self.desc()
        verbs = {"batch": ["BATCH PROGRAM:", "NIGHTLY/PERIODIC BATCH STEP:", "BATCH DB2 PROGRAM -"],
                 "online": ["ONLINE PROGRAM:", "CICS PSEUDO-CONVERSATIONAL PROGRAM -", "ONLINE TRANSACTION:"],
                 "sub": ["COMMON ROUTINE:", "SHARED SUBPROGRAM -", "UTILITY MODULE:"]}
        out = [f"{r.choice(verbs[self.kind])} {d.rstrip('.')}."]
        if self.kind == "batch":
            if p.get("jcl_job"):
                out.append(r.choice(["RUNS AS {s} OF JOB {j}.", "EXECUTED BY JOB {j}, {s}.",
                                     "SCHEDULED UNDER JOB {j} ({s})."]).format(
                    j=p["jcl_job"], s=self.ctx["job_step"].get(self.pid, "STEP010")))
            if self.writes:
                out.append(r.choice(["COMMITS EVERY {n} UNITS OF WORK.", "COMMIT INTERVAL: {n} ROWS.",
                                     "DB2 COMMIT AFTER EVERY {n} UPDATES."]).format(n=self.commit_freq))
            out.append(r.choice(["RETURN CODES: 0 OK, 4 WARNINGS, 16 SEVERE (SEE SYSOUT).",
                                 "RC 0 = NORMAL, RC 4 = REJECTS REPORTED, RC 16 = ABORTED.",
                                 "CONDITION CODES: 00 NORMAL / 04 WARNING / 16 FAILURE."]))
        elif self.kind == "online":
            out.append(r.choice(["PSEUDO-CONVERSATIONAL; STATE IS KEPT IN CLRCOMM1.",
                                 "STATE BETWEEN TASKS IS HELD IN THE COMMON COMMAREA.",
                                 "COMMAREA LAYOUT: CLRCOMM1."]))
            if not self.bms:
                out.append(r.choice(["NO SCREEN OF ITS OWN - DRIVEN THROUGH THE COMMAREA.",
                                     "INVOKED WITH A COMMAREA; RESULTS RETURNED IN CA-RETURN-CD/CA-MSG."]))
        else:
            out.append(r.choice(["SAFE FOR BOTH BATCH AND CICS CALLERS.", "NO CICS COMMANDS - CALLABLE FROM BATCH.",
                                 "STATIC CALL; CALLER OWNS THE UNIT OF WORK."]))
            out.append(r.choice(["RETURNS ERR-SQLCODE = 0 WHEN SUCCESSFUL.",
                                 "NON-ZERO ERR-SQLCODE MEANS THE REQUEST FAILED.",
                                 "ERRORS ARE RETURNED IN CLR-ERROR-BLOCK."]))
        notes = self.ctx.get("purpose_extra", {}).get(self.pid, [])
        out.extend(notes)
        return out

    # ------------------------------------------------------------------ ops
    def op_for(self, table) -> str:
        if (self.pid, table) in OP_OVERRIDE:
            return OP_OVERRIDE[(self.pid, table)]
        return DEFAULT_OP.get(table, "INSERT")

    # ------------------------------------------------------------------ ID / ENV / DATA
    def id_division(self):
        p = self.p
        self.a("IDENTIFICATION DIVISION.")
        rf = p.get("renamed_from")
        if rf and rf["date"] >= "2025-02-21":
            self.src.emit(" PROGRAM-ID.    " + rf["old_id"] + ".", rm="XC-01")
            self.src.emit(" PROGRAM-ID.    " + self.pid + ".", add="XC-01", keep_seq=True)
        else:
            self.a(f"PROGRAM-ID.    {self.pid}.", mark="PGMID")
        ents = self.maintenance_entries()
        creator = ents[0][1]
        author = {v: naming.AUTHOR_NAME.get(k, "") for k, v in naming.AUTHOR_TAG.items()}.get(creator) or "CLARA PROJECT TEAM"
        self.a(f"AUTHOR.        {author}.")
        self.a("INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.")
        self.a(f"DATE-WRITTEN.  {p['since']}.")
        self.a("DATE-COMPILED.")
        self.a("ENVIRONMENT DIVISION.")
        self.a("CONFIGURATION SECTION.")
        self.a("SOURCE-COMPUTER.  IBM-Z.")
        self.a("OBJECT-COMPUTER.  IBM-Z.")
        if self.files:
            self.a("INPUT-OUTPUT SECTION.")
            self.a("FILE-CONTROL.")
            for f in self.files:
                self.b(f"SELECT {self.fname(f)} ASSIGN TO {f['dd']}")
                self.b("ORGANIZATION IS SEQUENTIAL", 1)
                self.b(f"FILE STATUS IS WS-{f['dd']}-STATUS.", 1)

    @staticmethod
    def fname(f) -> str:
        return {"RPTOUT": "REPORT-FILE", "IMPIN": "INPUT-FILE", "EXTOUT": "EXTRACT-FILE",
                "RSVOUT": "RSVOUT-FILE"}.get(f["dd"], f["dd"] + "-FILE")

    def data_division(self, procedure_needs):
        self.a("DATA DIVISION.")
        if self.files:
            self.a("FILE SECTION.")
            for f in self.files:
                self.a(f"FD  {self.fname(f)}")
                self.b("RECORDING MODE IS F", 1)
                self.b("BLOCK CONTAINS 0 RECORDS.", 1)
                rec = self.fname(f).replace("-FILE", "-RECORD")
                self.a(f"01  {rec:<28}PIC X({f['lrecl']}).")
        self.a("WORKING-STORAGE SECTION.")
        self.c()
        self.a("01  WS-PROGRAM-INFO.")
        self.b(f"05  WS-PGM-ID               PIC X(8)   VALUE '{self.pid}'.")
        self.b("05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.")
        self.b("05  WS-RUN-TS               PIC X(26)  VALUE SPACES.")
        self.b("05  WS-USER-ID              PIC X(8)   VALUE SPACES.")
        if self.kind == "batch":
            self.b("05  WS-LAST-RUN-TS          PIC X(26)  VALUE SPACES.")
            self.b("05  WS-RUN-ID               PIC S9(9)  COMP VALUE ZERO.")
            if any(":WS-SELECT-STATUS" in w for t in self.reads for w in DRIVE_WHERE.get(t, [])):
                self.b("05  WS-SELECT-STATUS        PIC X(2)   VALUE SPACES.")
            if "CLR.T_CURRENCY_RATE" in self.reads:
                self.b("05  WS-RATE-DT              PIC X(10)  VALUE SPACES.")
        self.c()
        self.a("01  WS-SWITCHES.")
        self.b("05  WS-EOF-SW               PIC X      VALUE 'N'.")
        self.b("88  WS-END-OF-DATA                     VALUE 'Y'.", 1)
        self.b("05  WS-ERROR-SW             PIC X      VALUE 'N'.")
        self.b("88  WS-ERROR-FOUND                     VALUE 'Y'.", 1)
        self.b("88  WS-NO-ERROR                        VALUE 'N'.", 1)
        self.b("05  WS-FOUND-SW             PIC X      VALUE 'N'.")
        self.b("88  WS-ROW-FOUND                       VALUE 'Y'.", 1)
        self.b("88  WS-ROW-NOT-FOUND                   VALUE 'N'.", 1)
        for f in self.files:
            nm = f"WS-{f['dd']}-STATUS"
            self.b(f"05  {nm:<24}PIC X(2)   VALUE SPACES.")
        self.c()
        self.a("01  WS-COUNTERS.")
        for t in self.reads:
            nm = f"WS-{self.abbr(t)}-READ"
            self.b(f"05  {nm:<24}PIC S9(9)  COMP-3 VALUE ZERO." if len(nm) <= 24 else
                   f"05  {nm} PIC S9(9) COMP-3 VALUE ZERO.", add=self.late.get("tables", {}).get(t))
        for t in self.writes:
            nm = f"WS-{self.abbr(t)}-WRITTEN"
            self.b(f"05  {nm:<24}PIC S9(9)  COMP-3 VALUE ZERO." if len(nm) <= 24 else
                   f"05  {nm} PIC S9(9) COMP-3 VALUE ZERO.")
        self.b("05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.")
        if self.kind == "batch" and self.writes:
            self.b("05  WS-SINCE-COMMIT         PIC S9(9)  COMP-3 VALUE ZERO.")
            self.b(f"05  WS-COMMIT-FREQ          PIC S9(9)  COMP-3 VALUE +{self.commit_freq}.")
        self.c()
        self.a("01  WS-SQL-WORK.")
        self.b("05  WS-SQLCODE-DSP          PIC -9(9).")
        self.b("05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.")
        self.b("05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.")
        self.b("05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.")
        self.b("05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.")
        for ln in procedure_needs.get("ws", []):
            self._emit_ws(ln)
        self.c()
        self.b("EXEC SQL INCLUDE SQLCA END-EXEC.")
        self.c()
        self.c(self.r.choice(["APPLICATION COPYBOOKS", "CLARA RECORD LAYOUTS", "COPYBOOKS (HOST STRUCTURES AND WORK AREAS)"]))
        for cp in self.cpys:
            if cp == "CLRCOMM1" and self.kind != "online":
                pass
            lc = self.late.get("cpys", {}).get(cp)
            self.a(f"COPY {cp}.", add=lc, mark=f"COPY:{cp}")
        if self.c_change:
            self.a("COPY PARMREC1.", add="CM-09", mark="COPY:PARMREC1:c")
        # call parameter areas
        self.call_areas()
        # cursors
        for ln in procedure_needs.get("cursors", []):
            self._emit_ws(ln)
        if self.bms:
            self.symbolic_map()
        if self.kind == "online":
            self.c()
            self.a("01  WS-AID-VALUES.")
            self.b("05  AID-ENTER               PIC X      VALUE X'7D'.")
            self.b("05  AID-CLEAR               PIC X      VALUE X'6D'.")
            self.b("05  AID-PF3                 PIC X      VALUE X'F3'.")
            self.b("05  AID-PF7                 PIC X      VALUE X'F7'.")
            self.b("05  AID-PF8                 PIC X      VALUE X'F8'.")
            self.b("05  AID-PF12                PIC X      VALUE X'7C'.")
            self.b("05  WS-RESP                 PIC S9(8)  COMP VALUE ZERO.")
        if self.msgs:
            self.c()
            self.a("01  WS-MESSAGES.")
            for i, m in enumerate(self.msgs, 1):
                self.b(f"05  WS-MSG-{i:02d}               PIC X(40)  VALUE")
                self.b(f"'{m[:40]}'.", 2)
        if self.kind == "batch":
            self.report_layout()
        # linkage
        if self.kind == "online":
            self.a("LINKAGE SECTION.")
            self.a("01  DFHCOMMAREA                 PIC X(105).")
        elif self.kind == "sub":
            self.a("LINKAGE SECTION.")
            for ln in procedure_needs.get("linkage", []):
                self._emit_ws(ln)

    def _emit_ws(self, item):
        if isinstance(item, tuple):
            kind, text = item[0], item[1]
            kw = item[2] if len(item) > 2 else {}
            if kind == "a":
                self.a(text, **kw)
            elif kind == "c":
                self.c(text, **kw)
            else:
                self.b(text, kind if isinstance(kind, int) else 0, **kw)
        else:
            self.b(item)

    def abbr(self, table) -> str:
        """Table short name for data names (WS-<abbr>-WRITTEN <= 30 chars)."""
        name = table.split(".")[1].replace("T_", "", 1)
        if len(name) <= 19:
            return name.replace("_", "-")
        return "-".join(p[:5] for p in name.split("_"))[:19].rstrip("-")

    def pabbr(self, table) -> str:
        """Table short name for paragraph and cursor names."""
        name = table.split(".")[1].replace("T_", "", 1)
        if len(name) <= 13:
            return name.replace("_", "-")
        return "-".join(p[:4] for p in name.split("_"))[:13].rstrip("-")

    def cnt(self, table, what="WRITTEN") -> str:
        return f"WS-{self.abbr(table)}-{what}"

    def call_areas(self):
        calls = list(self.calls) + (["CLRCM040"] if self.c_change else [])
        need = set(calls)
        defs = []
        if "CLRCM020" in need:
            defs.append(("WS-AUDIT-PARMS", [("WS-AUD-TABLE", "X(18)"), ("WS-AUD-KEY", "X(30)"),
                                            ("WS-AUD-ACTION", "X(1)"), ("WS-AUD-USER", "X(8)"),
                                            ("WS-AUD-PGM", "X(8)")], None))
        if "CLRCM030" in need:
            defs.append(("WS-CCY-PARMS", [("WS-CCY-FROM", "X(3)"), ("WS-CCY-AMOUNT", "S9(11)V99 COMP-3"),
                                          ("WS-CCY-RATE-DT", "X(10)"), ("WS-CCY-GBP-AMOUNT", "S9(11)V99 COMP-3")], None))
        if "CLRCM070" in need:
            defs.append(("WS-AUTH-PARMS", [("WS-AUTH-USER", "X(8)"), ("WS-AUTH-FUNCTION", "X(8)"),
                                           ("WS-AUTH-ALLOWED", "X(1)")], None))
        if "CLRCM080" in need:
            defs.append(("WS-NOTE-PARMS", [("WS-NOTE-CLAIM-ID", "X(12)"), ("WS-NOTE-TYPE", "X(2)"),
                                           ("WS-NOTE-TEXT", "X(200)")], None))
        if "CLRCM090" in need:
            defs.append(("WS-DIARY-PARMS", [("WS-DIA-CLAIM-ID", "X(12)"), ("WS-DIA-TYPE", "X(4)"),
                                            ("WS-DIA-DUE-DT", "X(10)"), ("WS-DIA-OWNER", "X(8)")], None))
        if "CLRCM100" in need:
            defs.append(("WS-DOC-PARMS", [("WS-DOC-CLAIM-ID", "X(12)"), ("WS-DOC-OBJECT-ID", "X(36)"),
                                          ("WS-DOC-TYPE", "X(4)")], None))
        if "CLRCM110" in need or "CLRCM120" in need:
            defs.append(("WS-MQ-PARMS", [("WS-MQ-FUNCTION", "X(8)"), ("WS-MQ-BUFFER-LEN", "S9(9) COMP"),
                                         ("WS-MQ-BUFFER", "X(2000)")], None))
        if "CLRRS015" in need:
            defs.append(("WS-RSVAUTH-PARMS", [("WS-RA-USER", "X(8)"), ("WS-RA-CURRENCY", "X(3)"),
                                              ("WS-RA-AMOUNT", "S9(11)V99 COMP-3"), ("WS-RA-REQUIRED-LVL", "X(2)"),
                                              ("WS-RA-RESULT", "X(1)")], None))
        if "CLRCM010" in need and "CLRDATE1" not in self.cpys:
            defs.append(("WS-DATE-PARMS", [("WS-DT-IN-DATE", "X(10)"), ("WS-DT-CALENDAR", "X(2)"),
                                           ("WS-DT-BUS-DAYS", "S9(4) COMP"), ("WS-DT-OUT-DATE", "X(10)")], None))
        if not defs:
            return
        self.c()
        self.c(self.r.choice(["PARAMETER AREAS FOR CALLED MODULES", "CALL INTERFACES", "SUBPROGRAM PARAMETERS"]))
        for name, fields, add in defs:
            self.a(f"01  {name}.")
            for fn, pic in fields:
                self.b(f"05  {fn:<24}PIC {pic}.")

    def symbolic_map(self):
        m = self.bms
        used = set()
        self.c()
        self.c(f"SYMBOLIC MAP {m['map']} (MAPSET {m['mapset']}) - KEEP IN STEP WITH")
        self.c(f"BMS SOURCE legacy/clara/bms/{m['mapset']}.bms")
        self.a(f"01  {m['map']}I.")
        self.b("02  FILLER                  PIC X(12).")
        labels = []
        for f in m["fields"]:
            lab = naming.bms_label(f["name"], used)
            labels.append((lab, f))
            self.b(f"02  {lab + 'L':<24}PIC S9(4) COMP.")
            self.b(f"02  {lab + 'F':<24}PIC X.")
            self.b(f"02  FILLER REDEFINES {lab}F.")
            self.b(f"03  {lab + 'A':<20}PIC X.", 1)
            self.b(f"02  {lab + 'I':<24}PIC X({f['length']}).")
        self.b("02  MSGL                    PIC S9(4) COMP.")
        self.b("02  MSGF                    PIC X.")
        self.b("02  FILLER REDEFINES MSGF.")
        self.b("03  MSGA                PIC X.", 1)
        self.b("02  MSGI                    PIC X(79).")
        self.a(f"01  {m['map']}O REDEFINES {m['map']}I.")
        self.b("02  FILLER                  PIC X(12).")
        for lab, f in labels:
            self.b("02  FILLER                  PIC X(3).")
            self.b(f"02  {lab + 'O':<24}PIC X({f['length']}).")
        self.b("02  FILLER                  PIC X(3).")
        self.b("02  MSGO                    PIC X(79).")
        self.map_labels = labels

    def report_layout(self):
        r = self.r
        self.c()
        self.c("CONTROL REPORT LINES")
        self.a("01  WS-RPT-HEAD-1.")
        self.b("05  FILLER                  PIC X(1)   VALUE '1'.")
        self.b(f"05  FILLER                  PIC X(10)  VALUE '{self.pid}'.")
        t = ascii_text(self.p["description"]).upper().replace("'", "")
        if len(t) > 40:
            t = t[:40].rsplit(" ", 1)[0]
        self.b(f"05  FILLER                  PIC X(40)  VALUE")
        self.b(f"'{t}'.", 2)
        self.b("05  FILLER                  PIC X(10)  VALUE 'RUN DATE: '.")
        self.b("05  RH1-RUN-DATE            PIC X(10).")
        self.b("05  FILLER                  PIC X(62)  VALUE SPACES.")
        self.a("01  WS-RPT-DETAIL.")
        self.b("05  FILLER                  PIC X(1)   VALUE SPACE.")
        self.b("05  RD-LABEL                PIC X(40).")
        self.b("05  RD-VALUE                PIC X(60).")
        self.b("05  FILLER                  PIC X(32)  VALUE SPACES.")
        self.a("01  WS-RPT-TOTAL.")
        self.b("05  FILLER                  PIC X(1)   VALUE SPACE.")
        self.b("05  RT-LABEL                PIC X(40).")
        self.b("05  RT-COUNT                PIC ZZZ,ZZZ,ZZ9.")
        self.b("05  FILLER                  PIC X(81)  VALUE SPACES.")

    # ------------------------------------------------------------------ SQL builders
    def where_key(self, table, alias="", drive=None) -> list[str]:
        t = self.W.tables[table]
        cols = [c["name"] for c in t["columns"]]
        if table == "CLR.T_PARAM":
            return ["WHERE PARAM_KEY = :PARM-PARAM-KEY",
                    "  AND VALID_FROM <= CURRENT DATE",
                    "  AND (VALID_TO IS NULL OR VALID_TO >= CURRENT DATE)"]
        if table == "CLR.T_CURRENCY_RATE":
            return [f"WHERE CURRENCY_CD = {self.hv_ref(table, 'CURRENCY_CD')}",
                    f"  AND RATE_DT = {self.hv_ref(table, 'RATE_DT')}"]
        if drive and drive != table and "CLAIM_ID" in cols and "CLAIM_ID" in self.hv.get(drive, {}):
            return [f"WHERE CLAIM_ID = {self.hv_ref(drive, 'CLAIM_ID')}"]
        pk = t["primary_key"]
        out = []
        for i, k in enumerate(pk):
            out.append(("WHERE " if i == 0 else "  AND ") + f"{k} = {self.hv_ref(table, k)}")
        return out

    def select_into(self, table, cols, drive=None, lvl=0, mark=None, fetch_first=None):
        hv = [self.hv_ref(table, c) for c in cols]
        lines = pack(cols, "SELECT ", "       ", 52)
        lines += pack(hv, "  INTO ", "       ", 52)
        lines.append((f"  FROM {table}", f"R:{table}"))
        wk = self.where_key(table, drive=drive)
        lines += [" " + w if not w.startswith("WHERE") else " " + w for w in wk]
        if fetch_first or (drive and wk and wk[0].startswith("WHERE CLAIM_ID") and
                           self.W.tables[table]["primary_key"] != ["CLAIM_ID"]):
            lines.append(" FETCH FIRST 1 ROW ONLY")
        self.sql(lines, lvl, mark=mark)

    def insert(self, table, lvl=0, mark=None, override=None, omit=()):
        override = override or {}
        cols, vals = [], []
        for c in self.W.tables[table]["columns"]:
            n = c["name"]
            if n in omit:
                continue
            if is_identity(self.W, table, n) and n not in override:
                continue
            cols.append(n)
            if n in override:
                vals.append(override[n])
            elif n == "LAST_UPD_PGM":
                vals.append(":WS-PGM-ID")
            elif n == "LAST_UPD_USER":
                vals.append(":WS-USER-ID")
            elif n in TS_NOW_COLS:
                vals.append("CURRENT TIMESTAMP")
            else:
                vals.append(self.hv_ref(table, n))
        lines = [(f"INSERT INTO {table}", f"W:INSERT:{table}")]
        lines += pack(cols, "     ( ", "     ", 54)
        lines[-1] += " )"
        lines.append("VALUES")
        lines += pack(vals, "     ( ", "     ", 54)
        lines[-1] += " )"
        self.sql(lines, lvl, mark=mark)

    def update(self, table, sets: list[tuple], where: list[str], lvl=0, mark=None, returning=None):
        """sets: [(col, expr|None)]; returning=(mode, cols, into) -> SELECT .. FROM mode TABLE (UPDATE)."""
        st = []
        for c, e in sets:
            st.append(f"{c} = {e if e is not None else self.hv_ref(table, c)}")
        for c in ("LAST_UPD_TS", "LAST_UPD_PGM", "LAST_UPD_USER"):
            if any(x["name"] == c for x in self.W.tables[table]["columns"]) and not any(s[0] == c for s in sets):
                st.append({"LAST_UPD_TS": "LAST_UPD_TS = CURRENT TIMESTAMP",
                           "LAST_UPD_PGM": "LAST_UPD_PGM = :WS-PGM-ID",
                           "LAST_UPD_USER": "LAST_UPD_USER = :WS-USER-ID"}[c])
        lines = []
        pre = ""
        if returning:
            mode, rcols, into = returning
            lines += pack(rcols, "SELECT ", "       ", 52)
            lines += pack(into, "  INTO ", "       ", 52)
            lines.append(f"  FROM {mode} TABLE (")
            pre = ""
        lines.append((f"{pre}UPDATE {table}", f"W:UPDATE:{table}"))
        for i, s in enumerate(st):
            lines.append(("   SET " if i == 0 else "     , ") + s)
        lines += [" " + w for w in where]
        if returning:
            last = lines[-1]
            lines[-1] = (last[0] + " )", last[1]) if isinstance(last, tuple) else last + " )"
        self.sql(lines, lvl, mark=mark)

    def delete(self, table, where, lvl=0, mark=None):
        lines = [(f"DELETE FROM {table}", f"W:DELETE:{table}")] + [" " + w for w in where]
        self.sql(lines, lvl, mark=mark)

    def sqlcheck(self, para_tag: str, lvl=0, notfound_ok=True, on_ok=None):
        self.b("EVALUATE SQLCODE", lvl)
        self.b("WHEN 0", lvl + 1)
        if on_ok:
            for ln in on_ok:
                self.bw(ln, lvl + 2)
        else:
            self.b("CONTINUE", lvl + 2)
        if notfound_ok:
            self.b("WHEN +100", lvl + 1)
            self.b("SET WS-ROW-NOT-FOUND TO TRUE", lvl + 2)
        self.b("WHEN OTHER", lvl + 1)
        self.bw(f"MOVE '{para_tag[:30]}' TO ERR-PARA", lvl + 2)
        self.b("PERFORM 8000-SQL-ERROR", lvl + 2)
        self.b("END-EVALUATE", lvl)

    # ------------------------------------------------------------------ CALL builders
    def call(self, callee, lvl=0, mark=None, add=None):
        args = {
            "CLRCM010": ["CLR-DATE-WORK" if "CLRDATE1" in self.cpys else "WS-DATE-PARMS", "CLR-ERROR-BLOCK"],
            "CLRCM020": ["WS-AUDIT-PARMS", "CLR-ERROR-BLOCK"],
            "CLRCM030": ["WS-CCY-PARMS", "CLR-ERROR-BLOCK"],
            "CLRCM040": ["PARMREC1-REC", "CLR-ERROR-BLOCK"],
            "CLRCM050": ["CLR-ERROR-BLOCK"],
            "CLRCM070": ["WS-AUTH-PARMS", "CLR-ERROR-BLOCK"],
            "CLRCM080": ["WS-NOTE-PARMS", "CLR-ERROR-BLOCK"],
            "CLRCM090": ["WS-DIARY-PARMS", "CLR-ERROR-BLOCK"],
            "CLRCM100": ["WS-DOC-PARMS", "CLR-ERROR-BLOCK"],
            "CLRCM110": ["CLR-MQ-AREA", "WS-MQ-PARMS", "CLR-ERROR-BLOCK"],
            "CLRCM120": ["CLR-MQ-AREA", "WS-MQ-PARMS", "CLR-ERROR-BLOCK"],
            "CLRRS015": ["WS-RSVAUTH-PARMS", "CLR-ERROR-BLOCK"],
        }.get(callee, ["DFHEIBLK", "DFHCOMMAREA"])
        with self.src.added(add):
            self.b(f"CALL '{callee}' USING {args[0]}", lvl, mark=[f"CALL:{callee}"] + ([mark] if mark else []))
            for a_ in args[1:]:
                self.b(f"{'':<{len(callee) + 9}}{a_}", lvl)
            if args[0] == "DFHEIBLK":
                self.b("MOVE DFHCOMMAREA TO CLR-COMMAREA", lvl)
                self.b("IF CA-RETURN-CD > 4", lvl)
                self.b("SET WS-ERROR-FOUND TO TRUE", lvl + 1)
                self.b("END-IF", lvl)
            elif callee != "CLRCM050":
                self.b("IF ERR-SQLCODE NOT = ZERO", lvl)
                if callee in ("CLRCM020",):
                    self.b("ADD 1 TO WS-REJECT-CNT", lvl + 1)
                else:
                    self.bw(f"MOVE 'CALL {callee}' TO ERR-PARA", lvl + 1)
                    self.b("PERFORM 8000-SQL-ERROR" if self.kind != "sub" else "GO TO 9000-RETURN", lvl + 1)
                self.b("END-IF", lvl)

    def prep_call(self, callee, lvl=0, key=None, add=None):
        """MOVEs that set up a call's parameters."""
        with self.src.added(add):
            if callee == "CLRCM020":
                tbl = (self.writes or self.reads or ["CLR.T_AUDIT"])[0]
                self.bw(f"MOVE '{tbl}' TO WS-AUD-TABLE", lvl)
                self.b(f"MOVE {key or 'SPACES'} TO WS-AUD-KEY", lvl)
                self.b(f"MOVE '{self.r.choice(['U', 'I', 'A'])}' TO WS-AUD-ACTION", lvl)
                self.b("MOVE WS-USER-ID TO WS-AUD-USER", lvl)
                self.b("MOVE WS-PGM-ID TO WS-AUD-PGM", lvl)
            elif callee == "CLRCM010":
                reg = self._first_field("REGION_CD") if self.drive_table or self.kind == "online" else None
                cal = reg or "'UK'"
                if "CLRDATE1" in self.cpys:
                    self.b("MOVE WS-RUN-DATE TO DW-IN-DATE", lvl)
                    self.b(f"MOVE {cal} TO DW-CALENDAR", lvl)
                    self.b("MOVE ZERO TO DW-BUS-DAYS", lvl)
                else:
                    self.b("MOVE WS-RUN-DATE TO WS-DT-IN-DATE", lvl)
                    self.b(f"MOVE {cal} TO WS-DT-CALENDAR", lvl)
                    self.b("MOVE ZERO TO WS-DT-BUS-DAYS", lvl)
            elif callee == "CLRCM070":
                self.b("MOVE WS-USER-ID TO WS-AUTH-USER", lvl)
                self.b(f"MOVE '{self.pid}' TO WS-AUTH-FUNCTION", lvl)
            elif callee == "CLRCM090":
                self.b(f"MOVE {key or 'SPACES'} TO WS-DIA-CLAIM-ID", lvl)
            elif callee == "CLRCM080":
                self.b(f"MOVE {key or 'SPACES'} TO WS-NOTE-CLAIM-ID", lvl)
            elif callee == "CLRCM100":
                self.b(f"MOVE {key or 'SPACES'} TO WS-DOC-CLAIM-ID", lvl)

    # ------------------------------------------------------------------ paragraphs
    def para(self, name, comment=None, add=None):
        with self.src.added(add):
            if comment and self.boxed_paras:
                self.box([name, comment])
            elif comment:
                self.c(f"--- {name}: {comment}"[:64])
            self.a(f"{name}.", mark=f"PARA:{name}")

    def para_end(self, name, add=None):
        """Close the paragraph's last sentence with a period, then the THRU exit (older style)."""
        last = next((ln for ln in reversed(self.src.lines) if not ln.text.startswith("*")), None)
        with self.src.added(add):
            if last is not None and not last.text.rstrip().endswith("."):
                self.b(".")
            if self.old_style:
                self.a(f"{name}-EXIT.")
                self.b("EXIT.")

    def perform(self, name, lvl=0, **kw):
        if self.old_style:
            self.bw(f"PERFORM {name} THRU {name}-EXIT", lvl, **kw)
        else:
            self.b(f"PERFORM {name}", lvl, **kw)

    def line_count(self) -> int:
        return len(self.src.lines)

    # ================================================================== procedure planning
    def claim_key(self) -> str | None:
        """COBOL data name that holds the current claim id."""
        if self.kind == "online":
            return "CA-CLAIM-ID"
        if self.drive_table and "CLAIM_ID" in self.hv.get(self.drive_table, {}):
            return self.hv_ref(self.drive_table, "CLAIM_ID", sql=False)
        for t in self.reads + self.writes:
            if "CLAIM_ID" in self.hv.get(t, {}):
                return self.hv_ref(t, "CLAIM_ID", sql=False)
        return None

    def choose_drive(self, special):
        if "drive" in special:
            return special["drive"]
        if self.kind != "batch":
            return None
        if any(f["dd"] == "IMPIN" for f in self.files):
            return "FILE"
        cands = [t for t in self.reads if t not in LOOKUP_ONLY and t not in self.late.get("tables", {})]
        return cands[0] if cands else None

    def generate(self, n_fill: int = 0) -> Src:
        self.r = util.rng(f"code_legacy:cobol:{self.pid}")
        # re-roll style knobs deterministically (same as __init__)
        self.old_style = self.p["since"] < "2001-01-01" and self.r.random() < 0.55
        self.ind = 4 if self.r.random() < 0.6 else 3
        self.boxed_paras = self.r.random() < 0.5
        self.commit_freq = self.r.choice([100, 200, 250, 500, 1000])
        self.facts = []
        self.msgs = []
        self.ws_needs = {"ws": [], "cursors": [], "linkage": []}
        self.drive_cols = None
        self.map_labels = self._labels() if self.bms else None
        special = SPECIAL.get(self.pid, lambda g: {})(self)
        self.special = special
        self.drive_table = self.choose_drive(special)
        self.drive_table = None if self.drive_table in ("FILE", None) else self.drive_table
        self.drive_file = special.get("drive") == "FILE" or (self.kind == "batch" and self.choose_drive(special) == "FILE")
        proc = Src(fixed=True)
        self.src = proc
        self.procedure(special, n_fill)
        main = Src(fixed=True)
        self.src = main
        self.header()
        self.id_division()
        self.data_division(self.ws_needs)
        main.extend(proc)
        self.src = main
        return main

    def build(self) -> Src:
        n = 0
        src = self.generate(0)
        while len(src.lines) < self.target - 8 and n < 60:
            n += 1
            src = self.generate(n)
        self.n_fill = n
        return src

    # ------------------------------------------------------------------ procedure division
    def procedure(self, sp, n_fill):
        handled_t = set(sp.get("handled_tables", ()))
        handled_c = set(sp.get("handled_calls", ()))
        late_t = self.late.get("tables", {})
        k = self.claim_key()
        init_steps, row_steps, term_steps = [], [], []

        # ---- parameter reads / init calls
        if "CLR.T_PARAM" in self.reads and "CLR.T_PARAM" not in handled_t:
            init_steps.append(("1200-CHECK-PARAMETERS", self.body_param_check, None, "PARAMETER TABLE SANITY CHECK"))
        if "CLRCM040" in self.calls and "CLRCM040" not in handled_c:
            init_steps.append(("1300-GET-PARAMETERS", self.body_get_params, None, "READ BUSINESS PARAMETERS VIA CLRCM040"))
        if "CLRCM010" in self.calls and "CLRCM010" not in handled_c:
            init_steps.append(("1400-GET-BUSINESS-DATE", lambda: self.body_call("CLRCM010"), None, "DETERMINE PROCESSING DATE"))
        if "CLRCM070" in self.calls and "CLRCM070" not in handled_c:
            init_steps.append(("1500-CHECK-AUTHORITY", self.body_authority, None, "CONFIRM THE USER MAY RUN THIS FUNCTION"))
        init_steps += sp.get("init_steps", [])

        row_steps += sp.get("pre_row_steps", [])
        # ---- lookups (reads that are not the driver)
        lk = 2300
        for t in self.reads:
            if t in handled_t or t == self.drive_table or t == "CLR.T_PARAM":
                continue
            name = f"{lk}-READ-{self.pabbr(t)}"
            row_steps.append((name, (lambda tt=t: self.body_lookup(tt)), late_t.get(t),
                              self.r.choice(["LOOK UP", "READ", "FETCH"]) + f" {t}"))
            lk += 20
        # ---- filler: field edits (before the business steps) and report formatting
        fill_steps = self.filler_steps(n_fill)
        row_steps += fill_steps.get("row", [])
        # ---- special business steps
        row_steps += sp.get("row_steps", [])
        # ---- calls in the row
        cs = 3100
        for callee in self.calls:
            if callee in handled_c or callee in ("CLRCM040", "CLRCM010", "CLRCM070", "CLRCM050", "CLRCM020"):
                continue
            name = f"{cs}-{self.call_para_name(callee)}"
            row_steps.append((name, (lambda cc=callee: self.body_call(cc)), None, CALL_PURPOSE.get(callee, "CALL " + callee)))
            cs += 20
        # ---- writes
        ws = 4100
        for t in self.writes:
            if t in handled_t:
                continue
            op = self.op_for(t)
            name = f"{ws}-{op}-{self.pabbr(t)}"
            row_steps.append((name, (lambda tt=t, oo=op: self.body_write(tt, oo)), late_t.get(t), f"{op} {t}"))
            ws += 20
        if "CLRCM020" in self.calls and "CLRCM020" not in handled_c:
            row_steps.append(("4900-WRITE-AUDIT", lambda: self.body_call("CLRCM020"), None, "AUDIT TRAIL VIA CLRCM020"))
        if any(f["dd"] == "EXTOUT" for f in self.files):
            row_steps.append(("5000-WRITE-EXTRACT", self.body_write_extract, None, "WRITE THE OUTBOUND RECORD"))
        term_steps += fill_steps.get("term", [])
        term_steps += sp.get("term_steps", [])

        self.a("PROCEDURE DIVISION." if self.kind != "sub" else
               f"PROCEDURE DIVISION USING {' '.join(sp.get('using', ['LS-PARMS', 'LS-ERROR-BLOCK']))}.")
        if self.kind == "batch":
            self.batch_main(init_steps, row_steps, term_steps, sp)
        elif self.kind == "online":
            self.online_main(init_steps, row_steps, term_steps, sp)
        else:
            self.sub_main(init_steps, row_steps, sp)
        self.emit_steps(sp.get("extra_paras", []))
        # error routines
        self.error_paras()

    def call_para_name(self, callee):
        return {"CLRCM030": "CONVERT-CURRENCY", "CLRCM080": "WRITE-NOTE", "CLRCM090": "WRITE-DIARY",
                "CLRCM100": "RECORD-DOCUMENT", "CLRCM110": "PUT-MESSAGE", "CLRCM120": "GET-MESSAGE",
                "CLRRS015": "CHECK-RESERVE-AUTHORITY", "CLRRS040": "REFER-FOR-APPROVAL",
                "CLRFN015": "POLICY-LOOKUP", "CLRFN030": "CREATE-CLAIM", "CLRFN060": "DUPLICATE-CHECK"
                }.get(callee, "CALL-" + callee)

    def run_steps(self, steps, lvl=1):
        for name, _body, add, _cm in steps:
            if add:
                self.perform(name, lvl, add=add)
            else:
                self.perform(name, lvl)

    def emit_steps(self, steps):
        for name, body, add, cm in steps:
            with self.src.added(add):
                self.para(name, cm)
                body()
                self.para_end(name)

    # ------------------------------------------------------------------ batch skeleton
    def batch_main(self, init_steps, row_steps, term_steps, sp):
        r = self.r
        P_PROC, P_FETCH, P_ROW = sp.get("loop_names", ("2000-PROCESS", "2100-FETCH-NEXT", "2200-PROCESS-ROW"))
        self.para("0000-MAINLINE", r.choice(["CONTROL FLOW", "MAIN CONTROL", "PROGRAM CONTROL"]))
        self.perform("1000-INITIALISE")
        if sp.get("main_override"):
            sp["main_override"]()
        elif self.drive_table or self.drive_file:
            self.perform(P_PROC)
        else:
            self.perform("2000-PROCESS-RUN")
        self.perform("9000-TERMINATE")
        self.b("GOBACK.")
        self.para_end("0000-MAINLINE")
        # init
        self.para("1000-INITIALISE", r.choice(["OPEN FILES AND SET UP THE RUN", "INITIALISATION", "START OF RUN"]))
        self.b("MOVE FUNCTION CURRENT-DATE(1:8) TO WS-RUN-TS")
        self.b("STRING WS-RUN-TS(1:4) '-' WS-RUN-TS(5:2) '-' WS-RUN-TS(7:2)")
        self.b("DELIMITED BY SIZE INTO WS-RUN-DATE", 1)
        self.b("MOVE 'CLRBATCH' TO WS-USER-ID")
        for f in self.files:
            mode = "INPUT" if f["dir"] == "in" else "OUTPUT"
            self.b(f"OPEN {mode} {self.fname(f)}")
            self.b(f"IF WS-{f['dd']}-STATUS NOT = '00'", 0)
            self.bw(f"DISPLAY '{self.pid} OPEN FAILED {f['dd']} ' WS-{f['dd']}-STATUS", 1)
            self.b("MOVE 16 TO RETURN-CODE", 1)
            self.b("GOBACK", 1)
            self.b("END-IF")
        if any(f["dd"] == "RPTOUT" for f in self.files):
            self.b("MOVE WS-RUN-DATE TO RH1-RUN-DATE")
            self.b("WRITE REPORT-RECORD FROM WS-RPT-HEAD-1")
        self.run_steps(init_steps, 0)
        self.para_end("1000-INITIALISE")
        self.emit_steps(init_steps)
        # main loop
        if self.drive_table or self.drive_file:
            self.para(P_PROC, r.choice(["MAIN PROCESSING LOOP", "READ AND PROCESS ALL INPUT", "PROCESS LOOP"]))
            if self.drive_table:
                cur = self.cursor_name()
                self.sql([f"OPEN {cur}"])
                self.sqlcheck(f"2000-OPEN-{cur}", notfound_ok=False)
                self.perform(P_FETCH)
                self.b("PERFORM UNTIL WS-END-OF-DATA") if not self.old_style else None
                if self.old_style:
                    self.b(f"PERFORM {P_ROW} THRU {P_ROW}-EXIT")
                    self.b("UNTIL WS-END-OF-DATA", 1)
                else:
                    self.b(f"PERFORM {P_ROW}", 1)
                    self.b(f"PERFORM {P_FETCH}", 1)
                    self.b("END-PERFORM")
                self.sql([f"CLOSE {cur}"])
            else:
                self.perform("2100-READ-INPUT")
                if self.old_style:
                    self.b(f"PERFORM {P_ROW} THRU {P_ROW}-EXIT")
                    self.b("UNTIL WS-END-OF-DATA", 1)
                else:
                    self.b("PERFORM UNTIL WS-END-OF-DATA")
                    self.b(f"PERFORM {P_ROW}", 1)
                    self.b("PERFORM 2100-READ-INPUT", 1)
                    self.b("END-PERFORM")
            self.para_end(P_PROC)
            if self.drive_table:
                self.para(P_FETCH, "FETCH THE NEXT DRIVING ROW")
                self.fetch_body()
                self.para_end(P_FETCH)
            else:
                self.para("2100-READ-INPUT", "READ THE NEXT INPUT RECORD")
                self.b("READ INPUT-FILE")
                self.b("AT END", 1)
                self.b("SET WS-END-OF-DATA TO TRUE", 2)
                self.b("NOT AT END", 1)
                self.b("ADD 1 TO WS-REJECT-CNT" if False else "CONTINUE", 2)
                self.b("END-READ")
                self.para_end("2100-READ-INPUT")
            self.para(P_ROW, r.choice(["PROCESS ONE ROW", "ONE UNIT OF WORK", "PER-RECORD PROCESSING"]))
            if self.old_style:
                self.b("IF WS-END-OF-DATA")
                self.b(f"GO TO {P_ROW}-EXIT", 1)
                self.b("END-IF")
            self.b("SET WS-NO-ERROR TO TRUE")
            if self.drive_file and self.drive_table is None:
                self.b("MOVE INPUT-RECORD TO WS-INPUT-AREA")
                self.ws_needs["ws"].append(("a", "01  WS-INPUT-AREA             PIC X(400)."))
            self.run_steps(row_steps, 0)
            if self.writes:
                self.perform("6000-COMMIT-CHECK")
            self.para_end(P_ROW)
            self.emit_steps(row_steps)
            if self.writes:
                self.para("6000-COMMIT-CHECK", "PERIODIC COMMIT")
                self.b("ADD 1 TO WS-SINCE-COMMIT")
                self.b("IF WS-SINCE-COMMIT >= WS-COMMIT-FREQ")
                self.sql(["COMMIT"], 1)
                self.b("MOVE ZERO TO WS-SINCE-COMMIT", 1)
                self.b("END-IF")
                self.para_end("6000-COMMIT-CHECK")
        else:
            self.para("2000-PROCESS-RUN", r.choice(["SINGLE-PASS PROCESSING", "SET-BASED PROCESSING", "RUN PROCESSING"]))
            self.run_steps(row_steps, 0)
            self.para_end("2000-PROCESS-RUN")
            self.emit_steps(row_steps)
        # terminate
        self.para("9000-TERMINATE", r.choice(["END OF RUN", "CLOSE DOWN", "TERMINATION AND TOTALS"]))
        self.run_steps(term_steps, 0)
        if self.writes:
            self.sql(["COMMIT"])
        if any(f["dd"] == "RPTOUT" for f in self.files):
            for t in self.reads:
                lc = self.late.get("tables", {}).get(t)
                with self.src.added(lc):
                    self.bw(f"MOVE '{t} ROWS READ' TO RT-LABEL")
                    self.b(f"MOVE WS-{self.abbr(t)}-READ TO RT-COUNT")
                    self.b("WRITE REPORT-RECORD FROM WS-RPT-TOTAL")
            for t in self.writes:
                self.bw(f"MOVE '{t} ROWS WRITTEN' TO RT-LABEL")
                self.b(f"MOVE WS-{self.abbr(t)}-WRITTEN TO RT-COUNT")
                self.b("WRITE REPORT-RECORD FROM WS-RPT-TOTAL")
        for f in self.files:
            self.b(f"CLOSE {self.fname(f)}")
        self.b("IF WS-REJECT-CNT > ZERO")
        self.b("MOVE 4 TO RETURN-CODE", 1)
        self.b("END-IF")
        self.para_end("9000-TERMINATE")
        self.emit_steps(term_steps)

    def cursor_name(self) -> str:
        return "C-" + self.pabbr(self.drive_table)

    def driver_cols(self, t):
        cols = [c["name"] for c in self.W.tables[t]["columns"] if c["name"] not in AUDIT_COLS]
        n = min(len(cols), self.r.randint(4, 7))
        keep = list(dict.fromkeys(self.W.tables[t]["primary_key"] + [c for c in cols if c == "CLAIM_ID"] + cols[:n]))
        return keep

    def declare_cursor(self):
        t = self.drive_table
        cur = self.cursor_name()
        cols = self.special.get("drive_cols") or self.driver_cols(t)
        self.drive_cols = cols
        where = self.special.get("drive_where") or DRIVE_WHERE.get(t, ["LAST_UPD_TS >= :WS-LAST-RUN-TS"])
        lines = [f"DECLARE {cur} CURSOR WITH HOLD FOR"]
        if self.special.get("drive_sql"):
            lines += self.special["drive_sql"]
        else:
            lines += pack(cols, "SELECT ", "       ", 52)
            lines.append((f"  FROM {t}", f"R:{t}"))
            lines += [(" WHERE " if i == 0 else "   AND ") + w for i, w in enumerate(where)]
            lines.append(" ORDER BY " + ", ".join(self.W.tables[t]["primary_key"]))
            lines.append(" FOR FETCH ONLY")
        out = [(0, "EXEC SQL")]
        for ln in lines:
            if isinstance(ln, tuple):
                out.append((0, "    " + ln[0], {"mark": ln[1]}))
            else:
                out.append((0, "    " + ln))
        out.append((0, "END-EXEC."))
        self.ws_needs["cursors"].insert(0, ("c", ""))
        self.ws_needs["cursors"].insert(1, ("c", f"DRIVING CURSOR ON {t}"))
        self.ws_needs["cursors"] += out

    def fetch_body(self):
        t = self.drive_table
        if self.drive_cols is None:
            self.declare_cursor()
        hv = self.special.get("fetch_into") or [self.hv_ref(t, c) for c in self.drive_cols]
        lines = [f"FETCH {self.cursor_name()}"] + pack(hv, " INTO ", "      ", 52)
        self.sql(lines)
        self.b("EVALUATE SQLCODE")
        self.b("WHEN 0", 1)
        self.b(f"ADD 1 TO WS-{self.abbr(t)}-READ", 2)
        self.b("WHEN +100", 1)
        self.b("SET WS-END-OF-DATA TO TRUE", 2)
        self.b("WHEN OTHER", 1)
        self.bw(f"MOVE '{self.special.get('loop_names', ('', '2100-FETCH-NEXT'))[1]}' TO ERR-PARA", 2)
        self.b("PERFORM 8000-SQL-ERROR", 2)
        self.b("END-EVALUATE")

    # ------------------------------------------------------------------ online skeleton
    def online_main(self, init_steps, row_steps, term_steps, sp):
        r = self.r
        tx = self.p["cics_transaction"]
        self.para("0000-MAIN", "PSEUDO-CONVERSATIONAL CONTROL")
        self.b("EXEC CICS ASSIGN USERID(WS-USER-ID) END-EXEC")
        self.b("IF EIBCALEN = ZERO")
        self.b("INITIALIZE CLR-COMMAREA", 1)
        self.bw(f"MOVE '{tx}' TO CA-TRANID", 1)
        if self.bms:
            self.perform("1000-FIRST-TIME", 1)
        else:
            self.b("MOVE 12 TO CA-RETURN-CD", 1)
            self.bw("MOVE 'NO COMMAREA SUPPLIED' TO CA-MSG", 1)
            self.perform("9000-RETURN", 1)
        self.b("ELSE")
        self.b("MOVE DFHCOMMAREA TO CLR-COMMAREA", 1)
        self.perform("2000-PROCESS-INPUT", 1)
        self.b("END-IF")
        self.perform("9000-RETURN")
        self.b("GOBACK.")
        self.para_end("0000-MAIN")
        if self.bms:
            m = self.bms
            self.para("1000-FIRST-TIME", "SEND THE EMPTY SCREEN")
            self.b(f"MOVE LOW-VALUES TO {m['map']}O")
            self.b(f"EXEC CICS SEND MAP('{m['map']}') MAPSET('{m['mapset']}')")
            self.b("ERASE FREEKB RESP(WS-RESP) END-EXEC", 1)
            self.para_end("1000-FIRST-TIME")
        self.para("2000-PROCESS-INPUT", r.choice(["HANDLE THE TERMINAL INPUT", "PROCESS THE REQUEST", "INPUT PROCESSING"]))
        if self.bms:
            m = self.bms
            self.b(f"EXEC CICS RECEIVE MAP('{m['map']}') MAPSET('{m['mapset']}')")
            self.b(f"INTO({m['map']}I) RESP(WS-RESP) END-EXEC", 1)
            self.b("EVALUATE TRUE")
            self.b("WHEN EIBAID = AID-PF3", 1)
            self.b("WHEN EIBAID = AID-CLEAR", 1)
            self.b("MOVE ZERO TO CA-RETURN-CD", 2)
            self.b("EXEC CICS RETURN END-EXEC", 2)
            self.b("WHEN EIBAID = AID-PF12", 1)
            self.perform("1000-FIRST-TIME", 2)
            self.b("WHEN EIBAID = AID-ENTER", 1)
            self.perform("2100-EDIT-INPUT", 2)
            self.b("IF WS-NO-ERROR", 2)
            self.perform("2200-APPLY", 3)
            self.b("END-IF", 2)
            self.b("WHEN OTHER", 1)
            self.bw("MOVE 'INVALID KEY PRESSED' TO MSGO", 2)
            self.b("END-EVALUATE")
            self.b(f"EXEC CICS SEND MAP('{m['map']}') MAPSET('{m['mapset']}')")
            self.b("DATAONLY FREEKB CURSOR RESP(WS-RESP) END-EXEC", 1)
        else:
            self.perform("2100-EDIT-INPUT")
            self.b("IF WS-NO-ERROR")
            self.perform("2200-APPLY", 1)
            self.b("END-IF")
        self.para_end("2000-PROCESS-INPUT")
        self.para("2100-EDIT-INPUT", "VALIDATE THE REQUEST")
        self.b("SET WS-NO-ERROR TO TRUE")
        if self.bms:
            labs = getattr(self, "map_labels", None) or self._labels()
            first = labs[0][0]
            self.b(f"IF {first}L = ZERO OR {first}I = SPACES")
            self.b("SET WS-ERROR-FOUND TO TRUE", 1)
            self.msgs.append(f"{labs[0][1]['name']} IS REQUIRED")
            self.b(f"MOVE WS-MSG-{len(self.msgs):02d} TO MSGO", 1)
            self.b(f"MOVE -1 TO {first}L", 1)
            self.b("ELSE")
            self.b(f"MOVE {first}I TO CA-CLAIM-ID" if "CLAIM" in labs[0][1]["name"] else f"CONTINUE", 1)
            self.b("END-IF")
        else:
            self.b("IF CA-CLAIM-ID = SPACES OR LOW-VALUES")
            self.b("SET WS-ERROR-FOUND TO TRUE", 1)
            self.b("MOVE 8 TO CA-RETURN-CD", 1)
            self.bw("MOVE 'CLAIM ID IS REQUIRED' TO CA-MSG", 1)
            self.b("END-IF")
        self.run_steps([s for s in init_steps], 0)
        self.para_end("2100-EDIT-INPUT")
        self.emit_steps(init_steps)
        self.para("2200-APPLY", r.choice(["APPLY THE CHANGE", "CARRY OUT THE REQUEST", "BUSINESS PROCESSING"]))
        self.run_steps(row_steps, 0)
        self.b("IF WS-NO-ERROR")
        if self.writes:
            self.sql(["SYNCPOINT"] if False else ["COMMIT"], 1) if False else None
            self.b("EXEC CICS SYNCPOINT END-EXEC", 1)
        self.b("MOVE ZERO TO CA-RETURN-CD", 1)
        self.b("END-IF")
        self.para_end("2200-APPLY")
        self.emit_steps(row_steps)
        self.emit_steps(term_steps)
        self.para("9000-RETURN", "RETURN TO CICS")
        if self.bms:
            self.bw(f"EXEC CICS RETURN TRANSID('{tx}') COMMAREA(CLR-COMMAREA)")
            self.b("LENGTH(LENGTH OF CLR-COMMAREA) END-EXEC", 1)
        else:
            self.b("MOVE CLR-COMMAREA TO DFHCOMMAREA")
            self.b("EXEC CICS RETURN END-EXEC")
        self.para_end("9000-RETURN")

    def _labels(self):
        used = set()
        return [(naming.bms_label(f["name"], used), f) for f in self.bms["fields"]]

    # ------------------------------------------------------------------ subprogram skeleton
    def sub_main(self, init_steps, row_steps, sp):
        self.para("0000-MAIN", "ENTRY")
        self.b("MOVE ZERO TO ERR-SQLCODE OF LS-ERROR-BLOCK" if False else "INITIALIZE CLR-ERROR-BLOCK")
        self.b(f"MOVE '{self.pid}' TO ERR-PGM")
        for ln in sp.get("entry_lines", []):
            self.bw(ln)
        self.run_steps(init_steps + row_steps, 0)
        self.perform("9000-RETURN")
        self.para_end("0000-MAIN")
        self.emit_steps(init_steps + row_steps)
        self.para("9000-RETURN", "COPY RESULTS BACK TO THE CALLER")
        self.b("MOVE CLR-ERROR-BLOCK TO LS-ERROR-BLOCK")
        for ln in sp.get("return_lines", []):
            self.bw(ln)
        self.b("GOBACK.")
        self.para_end("9000-RETURN")

    # ------------------------------------------------------------------ error routines
    def error_paras(self):
        self.para("8000-SQL-ERROR", self.r.choice(["DB2 ERROR HANDLING", "SEVERE ERROR - REPORT AND STOP",
                                                   "UNEXPECTED SQLCODE"]))
        self.b("MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP")
        self.b("MOVE WS-PGM-ID TO ERR-PGM")
        self.bw("STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO ERR-TEXT")
        if "CLRCM050" in self.calls:
            self.call("CLRCM050")
        else:
            self.bw("DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT")
        if self.kind == "batch":
            if self.writes:
                self.sql(["ROLLBACK"])
            self.b("MOVE 16 TO RETURN-CODE")
            for f in self.files:
                self.b(f"CLOSE {self.fname(f)}")
            self.b("GOBACK.")
        elif self.kind == "online":
            self.b("EXEC CICS SYNCPOINT ROLLBACK END-EXEC")
            self.b("MOVE 16 TO CA-RETURN-CD")
            self.b("MOVE ERR-TEXT TO CA-MSG")
            self.perform("9000-RETURN")
        else:
            self.b("GO TO 9000-RETURN.")
        self.para_end("8000-SQL-ERROR")

    # ------------------------------------------------------------------ generic bodies
    def body_param_check(self):
        pre = {"FRAUD": "FRD_%", "RESERVE": "RSV_%", "TRIAGE": "TRI_%", "RECOVER": "REC_%",
               "FNOL": "RSV_%", "SETTLE": "TRI_%", "COMMON": "%"}.get(self.p["area"], "%")
        self.ws_needs["ws"].append((0, "05  WS-PARM-ROWS            PIC S9(9)  COMP VALUE ZERO."))
        self.sql(["SELECT COUNT(*)", "  INTO :WS-PARM-ROWS", "  FROM CLR.T_PARAM",
                  f" WHERE PARAM_KEY LIKE '{pre}'", "   AND VALID_FROM <= CURRENT DATE",
                  "   AND (VALID_TO IS NULL OR VALID_TO >= CURRENT DATE)"])
        self.sqlcheck("1200-CHECK-PARAMETERS", notfound_ok=False)
        self.b("IF WS-PARM-ROWS = ZERO")
        self.bw(f"DISPLAY WS-PGM-ID ' NO CURRENT PARAMETERS FOUND'", 1)
        self.b("SET WS-ERROR-FOUND TO TRUE", 1)
        self.b("END-IF")

    def body_get_params(self, keys=None):
        keys = keys or self.special.get("param_keys") or []
        if not keys:
            self.b("MOVE SPACES TO PARM-PARAM-KEY")
            self.bw(f"MOVE '{self.special.get('generic_key', 'RSV_LLNT_GBP' if self.p['area'] == 'RESERVE' else 'TRI_T3_MIN_GBP')}' TO PARM-PARAM-KEY")
            self.call("CLRCM040")
            return
        for key, target in keys:
            self.bw(f"MOVE '{key}' TO PARM-PARAM-KEY")
            self.call("CLRCM040")
            if target:
                self.bw(f"MOVE FUNCTION NUMVAL(PARM-PARAM-VALUE) TO {target}")

    def body_authority(self):
        self.prep_call("CLRCM070")
        self.call("CLRCM070")
        self.b("IF WS-AUTH-ALLOWED NOT = 'Y'")
        self.b("SET WS-ERROR-FOUND TO TRUE", 1)
        if self.kind == "online":
            self.b("MOVE 8 TO CA-RETURN-CD", 1)
            self.bw("MOVE 'NOT AUTHORISED FOR THIS FUNCTION' TO CA-MSG", 1)
        self.b("END-IF")

    def body_call(self, callee):
        k = self.claim_key()
        self.prep_call(callee, key=k)
        if callee == "CLRCM110":
            self.b("MOVE 'MQPUT' TO WS-MQ-FUNCTION")
            q = self.special.get("queue")
            if q:
                self.bw(f"MOVE '{q}' TO MQ-QUEUE-NAME")
            self.b("MOVE LENGTH OF WS-MQ-BUFFER TO WS-MQ-BUFFER-LEN")
        if callee == "CLRCM120":
            self.b("MOVE 'MQGET' TO WS-MQ-FUNCTION")
        if callee == "CLRCM030":
            cur = self._first_field("CURRENCY_CD")
            if cur:
                self.b(f"MOVE {cur} TO WS-CCY-FROM")
            self.b("MOVE WS-RUN-DATE TO WS-CCY-RATE-DT")
        if callee == "CLRRS015":
            self.b("MOVE WS-USER-ID TO WS-RA-USER")
        self.call(callee)
        if callee == "CLRRS015":
            self.b("IF WS-RA-RESULT NOT = 'Y'")
            self.b("SET WS-ERROR-FOUND TO TRUE", 1)
            self.b("END-IF")

    def _first_field(self, col):
        for t in [self.drive_table] + self.reads + self.writes:
            if t and col in self.hv.get(t, {}):
                return self.hv_ref(t, col, sql=False)
        return None

    def body_lookup(self, t):
        cols = [c["name"] for c in self.W.tables[t]["columns"] if c["name"] not in AUDIT_COLS]
        pk = self.W.tables[t]["primary_key"]
        n = min(len(cols), self.r.randint(3, 6))
        sel = list(dict.fromkeys(pk + cols[:n]))
        # move keys
        drive = self.drive_table
        k = self.claim_key()
        wk = self.where_key(t, drive=drive)
        if t not in ("CLR.T_PARAM", "CLR.T_CURRENCY_RATE") and not (wk and wk[0].startswith("WHERE CLAIM_ID") and drive):
            for key in pk:
                if key == "CLAIM_ID" and k:
                    self.b(f"MOVE {k} TO {self.hv_ref(t, key, sql=False)}")
                elif key == "USER_ID":
                    self.b(f"MOVE WS-USER-ID TO {self.hv_ref(t, key, sql=False)}")
        if t == "CLR.T_CURRENCY_RATE":
            cur = None
            for tt in [drive] + self.reads + self.writes:
                if tt and tt != t and "CURRENCY_CD" in self.hv.get(tt, {}):
                    cur = self.hv_ref(tt, "CURRENCY_CD", sql=False)
                    break
            if cur:
                self.b(f"MOVE {cur} TO {self.hv_ref(t, 'CURRENCY_CD', sql=False)}")
            self.b(f"MOVE WS-RUN-DATE TO {self.hv_ref(t, 'RATE_DT', sql=False)}")
        self.b("SET WS-ROW-FOUND TO TRUE")
        self.select_into(t, sel, drive=drive)
        self.sqlcheck(f"READ {t}", on_ok=[f"ADD 1 TO WS-{self.abbr(t)}-READ"])

    def body_write(self, t, op, mark=None):
        k = self.claim_key()
        if op == "INSERT":
            tcols = [c["name"] for c in self.W.tables[t]["columns"]]
            if "CLAIM_ID" in tcols and k and self.hv_ref(t, "CLAIM_ID", sql=False) != k:
                self.b(f"MOVE {k} TO {self.hv_ref(t, 'CLAIM_ID', sql=False)}")
            for c in self.W.tables[t]["columns"]:
                vals = naming.enum_values(c["description"], c.get("length", 0)) if c["type"] == "CHAR" else []
                if vals and c["name"] not in AUDIT_COLS and self.r.random() < 0.5:
                    self.b(f"MOVE '{vals[0]}' TO {self.hv_ref(t, c['name'], sql=False)}")
                    break
            self.insert(t, mark=mark)
        elif op == "UPDATE":
            sets = UPDATE_SET.get((self.pid, t))
            if sets is None:
                cand = [c["name"] for c in self.W.tables[t]["columns"]
                        if c["name"] not in AUDIT_COLS and c["name"] not in self.W.tables[t]["primary_key"]
                        and c["name"] != "CLAIM_ID"]
                sets = [(c, None) for c in self.r.sample(cand, min(len(cand), self.r.randint(1, 3)))]
            if not sets:
                sets = [("LAST_UPD_TS", "CURRENT TIMESTAMP")]
            where = self.where_key(t, drive=self.drive_table)
            if t == "CLR.T_CLAIM" and k:
                where = [f"WHERE CLAIM_ID = :{k}" if ":" not in k else f"WHERE CLAIM_ID = {k}"]
            self.update(t, sets, where, mark=mark)
        else:
            where = self.where_key(t, drive=self.drive_table)
            if self.pid == "CLRCM140":
                where = ["WHERE CLAIM_ID = :WS-PURGE-CLAIM-ID"]
                if not any("WS-PURGE-CLAIM-ID" in str(x) for x in self.ws_needs["ws"]):
                    self.ws_needs["ws"].append((0, "05  WS-PURGE-CLAIM-ID       PIC X(12)  VALUE SPACES."))
            if self.pid == "CLRCM130":
                where = ["WHERE RUN_TS < :WS-PURGE-BEFORE-TS"]
                if not any("WS-PURGE-BEFORE-TS" in str(x) for x in self.ws_needs["ws"]):
                    self.ws_needs["ws"].append((0, "05  WS-PURGE-BEFORE-TS      PIC X(26)  VALUE SPACES."))
            self.delete(t, where, mark=mark)
        self.sqlcheck(f"{op} {t}", on_ok=[f"ADD 1 TO WS-{self.abbr(t)}-WRITTEN"])

    def body_write_extract(self):
        self.b("MOVE SPACES TO EXTRACT-RECORD")
        k = self.claim_key()
        if k:
            self.b(f"MOVE {k} TO EXTRACT-RECORD(1:12)")
        self.b("WRITE EXTRACT-RECORD")
        self.b("IF WS-EXTOUT-STATUS NOT = '00'")
        self.bw("DISPLAY WS-PGM-ID ' WRITE FAILED EXTOUT ' WS-EXTOUT-STATUS", 1)
        self.b("ADD 1 TO WS-REJECT-CNT", 1)
        self.b("END-IF")

    # ------------------------------------------------------------------ filler
    def filler_steps(self, n_fill):
        """Field-edit and formatting paragraphs (no SQL, no CALL, no new facts)."""
        out = {"row": [], "term": []}
        if n_fill <= 0:
            return out
        pool = []
        for pref in (True, False):
            for cp in self.cpys:
                c = self.W.copybooks[cp]
                if not c["table"] or c["table"] in self.late.get("tables", {}):
                    continue
                if (c["table"] in self.reads) == pref:
                    pool.append(c)
        self.r_f = util.rng(f"code_legacy:fill:{self.pid}")
        made = 0
        no = 2500
        i = 0
        while made < n_fill and pool:
            c = pool[i % len(pool)]
            chunk = i // len(pool)
            i += 1
            if chunk > 3:
                break
            ncols = len([x for x in self.W.tables[c["table"]]["columns"] if x["name"] not in AUDIT_COLS])
            if chunk * max(3, ncols // 2) >= ncols:
                continue
            name = f"{no}-EDIT-{self.pabbr(c['table'])}" + (f"-{chunk + 1}" if chunk else "")
            out["row"].append((name, (lambda cc=c, ch=chunk: self.body_edit(cc, ch)), None,
                               self.r_f.choice(["FIELD EDITS FOR", "VALIDATE", "CHECK MANDATORY FIELDS IN"]) + " " + c["table"]))
            no += 10
            made += 1
            if self.kind == "batch" and made < n_fill and any(f["dd"] == "RPTOUT" for f in self.files) and chunk == 0:
                name2 = f"{7000 + made * 10}-LIST-{self.pabbr(c['table'])}"
                out["term"].append((name2, (lambda cc=c: self.body_list(cc)), None, f"LIST {c['table']} FIELDS ON THE REPORT"))
                made += 1
        return out

    def body_edit(self, c, chunk):
        t = c["table"]
        cols = [x for x in self.W.tables[t]["columns"] if x["name"] not in AUDIT_COLS]
        per = max(3, len(cols) // 2)
        sub = cols[(chunk * per) % len(cols):][:per] or cols[:per]
        for col in sub:
            f = self.hv[t][col["name"]]
            if f in self.dup:
                continue
            vals = naming.enum_values(col["description"], col.get("length", 0)) if col["type"] == "CHAR" else []
            if vals:
                cond = " AND ".join(f"{f} NOT = '{v}'" for v in vals)
                self.bw(f"IF {cond}")
                self.b("ADD 1 TO WS-REJECT-CNT", 1)
                self.bw(f"MOVE '{col['name'][:18]} INVALID' TO ERR-TEXT", 1)
                self.b("END-IF")
            elif col["type"] in ("CHAR", "VARCHAR") and not col["nullable"]:
                self.b(f"IF {f} = SPACES OR LOW-VALUES")
                self.b("ADD 1 TO WS-REJECT-CNT", 1)
                self.bw(f"MOVE '{col['name'][:18]} MISSING' TO ERR-TEXT", 1)
                self.b("END-IF")
            elif col["type"] in ("DECIMAL", "SMALLINT", "INTEGER") and col["nullable"] is False:
                self.b(f"IF {f} NOT NUMERIC")
                self.b(f"MOVE ZERO TO {f}", 1)
                self.b("ADD 1 TO WS-REJECT-CNT", 1)
                self.b("END-IF")
            elif col["type"] == "DATE":
                self.b(f"IF {f} NOT = SPACES AND {f}(5:1) NOT = '-'")
                self.bw(f"MOVE '{col['name'][:18]} BAD DATE' TO ERR-TEXT", 1)
                self.b("ADD 1 TO WS-REJECT-CNT", 1)
                self.b("END-IF")

    def body_list(self, c):
        t = c["table"]
        self.bw(f"MOVE 'LAST {t} ROW' TO RD-LABEL")
        self.b("MOVE SPACES TO RD-VALUE")
        self.b("WRITE REPORT-RECORD FROM WS-RPT-DETAIL")
        for col in [x for x in self.W.tables[t]["columns"] if x["name"] not in AUDIT_COLS][:7]:
            f = self.hv[t][col["name"]]
            if f in self.dup or col["type"] not in ("CHAR", "VARCHAR", "DATE", "TIMESTAMP"):
                continue
            self.bw(f"MOVE '  {col['name'][:26]}' TO RD-LABEL")
            self.b(f"MOVE {f} TO RD-VALUE")
            self.b("WRITE REPORT-RECORD FROM WS-RPT-DETAIL")


from .cobol_special import SPECIAL  # noqa: E402  (circular-safe: defined after the class)
