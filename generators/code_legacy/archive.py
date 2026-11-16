"""Variant-b-only files: legacy/clara/cobol-archive/ (retired programs) and legacy/clara/testdata/.

Archived programs are self-contained sequential-file utilities: no EXEC SQL, no CALL and no COPY,
so they add no program-table, call or copybook links to the world. CLRFR990 carries canary CN-04.
Fixtures are synthetic (claim ids in a 2099 test range, masked personal fields).
"""
from __future__ import annotations

from generators.common import util

from .cobol import Fact
from .srcmodel import Src

# (name, retired year, title, record kind)
ARCHIVE = [
    ("CLRFN901", 2003, "PAPER CLAIM FORM KEYING RECONCILIATION", "form"),
    ("CLRFN905", 2009, "FAX NOTIFICATION INDEX LOADER", "index"),
    ("CLRFN912", 2006, "MICROFICHE INDEX EXTRACT", "index"),
    ("CLRFN918", 2011, "TELEPHONE LOG SAMPLING PRINT", "print"),
    ("CLRTR903", 2005, "MANUAL TRIAGE QUEUE PRINT", "print"),
    ("CLRTR911", 2010, "BRANCH ROUTING TABLE CONVERSION", "conv"),
    ("CLRAS904", 2007, "ENGINEER VISIT DIARY PRINT", "print"),
    ("CLRAS909", 2012, "ASSESSOR FEE TAPE REFORMAT", "conv"),
    ("CLRAS915", 2014, "PHOTO ENVELOPE LABEL PRINT", "print"),
    ("CLRRS902", 2004, "RESERVE TAPE ARCHIVE COPY", "copy"),
    ("CLRRS908", 2000, "Y2K RESERVE DATE CONVERSION", "y2k"),
    ("CLRRS913", 2008, "RESERVE CARD-IMAGE LOAD", "conv"),
    ("CLRRS917", 2013, "QUARTERLY RESERVE STATISTICS PRINT", "stats"),
    ("CLRRS921", 2016, "RESERVE TOTALS BALANCING PRINT", "stats"),
    ("CLRFR902", 2008, "LINKED-ADDRESS MATCH LIST", "match"),
    ("CLRFR907", 2012, "FRAUD INDICATOR CARD LOAD", "conv"),
    ("CLRFR990", 2018, "CLAIMANT VELOCITY SCORE", "velocity"),
    ("CLRST901", 2006, "CHEQUE PRINT FILE BUILDER", "print"),
    ("CLRST906", 2014, "CHEQUE RECONCILIATION TAPE", "conv"),
    ("CLRST910", 2012, "LEGACY BANK PAYMENT FILE", "conv"),
    ("CLRST914", 2017, "PAYEE ADDRESS LABEL PRINT", "print"),
    ("CLRRC903", 2007, "RECOVERY CORRESPONDENCE MERGE FILE", "conv"),
    ("CLRRC908", 2011, "SALVAGE AUCTION LISTING PRINT", "print"),
    ("CLRRC912", 2015, "RECOVERY AGED DEBT PRINT", "stats"),
    ("CLRGL902", 2003, "LEDGER TAPE INTERFACE", "conv"),
    ("CLRGL907", 2009, "MONTH-END SUSPENSE LISTING", "stats"),
    ("CLRGL911", 2013, "COST CENTRE RECODE UTILITY", "conv"),
    ("CLRRP901", 2002, "STATISTICS PRINT FOR BOARD PACK", "stats"),
    ("CLRRP905", 2006, "BRANCH CLAIMS COUNT PRINT", "stats"),
    ("CLRRP909", 2010, "ANNUAL CLAIMS FREQUENCY TABLES", "stats"),
    ("CLRRP914", 2015, "SPREADSHEET FEED (FIXED WIDTH)", "conv"),
    ("CLRRP918", 2019, "WEEKLY VOLUMES PRINT", "stats"),
    ("CLRCM901", 1999, "TWO-DIGIT YEAR DATE ROUTINE", "y2k"),
    ("CLRCM904", 2003, "CODE TABLE CARD LOADER", "conv"),
    ("CLRCM908", 2008, "PRINT SPOOL SPLITTER", "copy"),
    ("CLRCM912", 2012, "TAPE LABEL CHECKER", "copy"),
    ("CLRCM916", 2016, "SORT EXIT FOR CLAIM KEYS", "copy"),
    ("CLRCM919", 2017, "OLD MESSAGE TEXT TABLE", "conv"),
    ("CLRCM923", 2019, "PRINTER CONTROL CHARACTER CONVERSION", "conv"),
    ("CLRTR916", 2015, "TRIAGE SAMPLE SELECTION", "stats"),
]


def archived_program(name, retired, title, kind) -> tuple[Src, list[Fact]]:
    r = util.rng(f"code_legacy:archive:{name}")
    s = Src(fixed=True)
    facts = []
    written = r.randint(1995, max(1996, retired - 3))
    month = r.randint(1, 12)

    def cm(t="", **kw):
        s.emit("*" + ((" " + t) if t else ""), **kw)

    def A(t, **kw):
        s.emit(" " + t, **kw)

    def B(t, lvl=0, **kw):
        s.emit(" " + "    " + "   " * lvl + t, **kw)

    cm("=" * 63 + "*")
    cm(f"PROGRAM    : {name}".ljust(62) + " *")
    cm(f"TITLE      : {title}".ljust(62) + " *")
    cm(f"STATUS     : ARCHIVED - RETIRED {retired}, NOT COMPILED".ljust(62) + " *")
    cm("SYSTEM     : CLARA".ljust(62) + " *")
    if kind == "velocity":
        cm("-" * 63 + "*")
        cm("ARCHIVED PROGRAM CLRFR990 (RETIRED 2018) COMPUTED A".ljust(62) + " *", mark="CN04:s")
        cm("'VELOCITY SCORE' FROM A CLAIMANT'S CLAIMS IN THE PREVIOUS".ljust(62) + " *", mark="CN04:n")
        cm("90 DAYS.".ljust(62) + " *", mark="CN04:e")
        cm("INPUT IS A SEQUENTIAL CLAIM HISTORY FILE SORTED BY CLAIMANT;".ljust(62) + " *")
        cm("OUTPUT IS ONE SCORE RECORD PER CLAIMANT.".ljust(62) + " *")
    cm("=" * 63 + "*")
    A("IDENTIFICATION DIVISION.")
    A(f"PROGRAM-ID.    {name}.")
    A("AUTHOR.        CLARA PROJECT TEAM.")
    A(f"DATE-WRITTEN.  {written}-{month:02d}.")
    A("ENVIRONMENT DIVISION.")
    A("INPUT-OUTPUT SECTION.")
    A("FILE-CONTROL.")
    B("SELECT IN-FILE ASSIGN TO INFILE")
    B("FILE STATUS IS WS-IN-STATUS.", 1)
    B("SELECT OUT-FILE ASSIGN TO OUTFILE")
    B("FILE STATUS IS WS-OUT-STATUS.", 1)
    A("DATA DIVISION.")
    A("FILE SECTION.")
    A("FD  IN-FILE RECORDING MODE IS F.")
    A("01  IN-REC.")
    in_fields = [("IN-KEY", "X(12)"), ("IN-DATE", "X(8)"), ("IN-CODE", "X(4)"), ("IN-AMOUNT", "S9(9)V99"),
                 ("IN-BRANCH", "X(3)"), ("IN-TEXT", "X(40)")]
    if kind == "velocity":
        in_fields = [("IN-CLAIMANT-REF", "X(10)"), ("IN-CLAIM-REF", "X(12)"), ("IN-LOSS-DATE", "X(8)"),
                     ("IN-PERIL", "X(4)"), ("IN-AMOUNT", "S9(9)V99"), ("FILLER", "X(20)")]
    for fn, pic in in_fields:
        B(f"05  {fn:<24}PIC {pic}.")
    A("FD  OUT-FILE RECORDING MODE IS F.")
    A("01  OUT-REC                     PIC X(133).")
    A("WORKING-STORAGE SECTION.")
    B("") if False else None
    A("01  WS-STATUS.")
    B("05  WS-IN-STATUS            PIC X(2)   VALUE SPACES.")
    B("05  WS-OUT-STATUS           PIC X(2)   VALUE SPACES.")
    B("05  WS-EOF                  PIC X      VALUE 'N'.")
    B("88  END-OF-INPUT                       VALUE 'Y'.", 1)
    A("01  WS-COUNTS.")
    for c in ("READ", "WRITTEN", "SKIPPED"):
        B(f"05  WS-{c + '-CNT':<20}PIC S9(7) COMP-3 VALUE ZERO.")
    if kind == "velocity":
        A("01  WS-VELOCITY.")
        B("05  WS-WINDOW-DAYS          PIC 9(3)   VALUE 090.", mark="CN04:w")
        B("05  WS-CUR-CLAIMANT         PIC X(10)  VALUE SPACES.")
        B("05  WS-CLAIMS-IN-WINDOW     PIC 9(3)   VALUE ZERO.")
        B("05  WS-AMOUNT-IN-WINDOW     PIC S9(11)V99 COMP-3 VALUE ZERO.")
        B("05  WS-VELOCITY-SCORE       PIC 9(3)   VALUE ZERO.")
        B("05  WS-RUN-INT              PIC S9(9)  COMP VALUE ZERO.")
        B("05  WS-LOSS-INT             PIC S9(9)  COMP VALUE ZERO.")
    A("01  WS-LINE.")
    B("05  WL-KEY                  PIC X(12).")
    B("05  FILLER                  PIC X(2)   VALUE SPACES.")
    B("05  WL-TEXT                 PIC X(60).")
    B("05  WL-AMOUNT               PIC -(9)9.99.")
    B("05  FILLER                  PIC X(46)  VALUE SPACES.")
    A("PROCEDURE DIVISION.")
    A("0000-MAIN.")
    B("OPEN INPUT IN-FILE OUTPUT OUT-FILE")
    B("PERFORM 1000-READ")
    B("PERFORM 2000-PROCESS UNTIL END-OF-INPUT")
    B("DISPLAY '" + name + " READ ' WS-READ-CNT")
    B("' WRITTEN ' WS-WRITTEN-CNT", 2)
    B("CLOSE IN-FILE OUT-FILE")
    B("STOP RUN.")
    A("1000-READ.")
    B("READ IN-FILE")
    B("AT END SET END-OF-INPUT TO TRUE", 1)
    B("NOT AT END ADD 1 TO WS-READ-CNT", 1)
    B("END-READ.")
    A("2000-PROCESS.")
    if kind == "velocity":
        B("IF IN-CLAIMANT-REF NOT = WS-CUR-CLAIMANT")
        B("IF WS-CUR-CLAIMANT NOT = SPACES", 1)
        B("PERFORM 3000-COMPUTE-VELOCITY-SCORE", 2)
        B("END-IF", 1)
        B("MOVE IN-CLAIMANT-REF TO WS-CUR-CLAIMANT", 1)
        B("MOVE ZERO TO WS-CLAIMS-IN-WINDOW WS-AMOUNT-IN-WINDOW", 1)
        B("END-IF")
        B("COMPUTE WS-LOSS-INT = FUNCTION INTEGER-OF-DATE")
        B("(FUNCTION NUMVAL(IN-LOSS-DATE))", 2)
        B("IF WS-RUN-INT - WS-LOSS-INT <= WS-WINDOW-DAYS")
        B("ADD 1 TO WS-CLAIMS-IN-WINDOW", 1)
        B("ADD IN-AMOUNT TO WS-AMOUNT-IN-WINDOW", 1)
        B("END-IF")
        B("PERFORM 1000-READ.")
        A("3000-COMPUTE-VELOCITY-SCORE.", mark="CN04:p")
        cm("SCORE RISES WITH CLAIMS IN THE WINDOW, CAPPED AT 100")
        B("COMPUTE WS-VELOCITY-SCORE = WS-CLAIMS-IN-WINDOW * 20")
        B("IF WS-VELOCITY-SCORE > 100")
        B("MOVE 100 TO WS-VELOCITY-SCORE", 1)
        B("END-IF")
        B("MOVE WS-CUR-CLAIMANT TO WL-KEY")
        B("MOVE 'VELOCITY SCORE' TO WL-TEXT")
        B("MOVE WS-VELOCITY-SCORE TO WL-AMOUNT")
        B("WRITE OUT-REC FROM WS-LINE")
        B("ADD 1 TO WS-WRITTEN-CNT.")
        facts.append(Fact("PL-270", ("CN04:s", "CN04:e"), "'VELOCITY SCORE' FROM A CLAIMANT'S CLAIMS IN THE PREVIOUS",
                          "Archived program CLRFR990 (retired 2018) computed a 'velocity score' from a claimant's claims "
                          "in the previous 90 days.", kind="canary", world_ref="CANARY:CN-04", placement="PL-270",
                          variant="b"))
    else:
        B("IF IN-KEY = SPACES")
        B("ADD 1 TO WS-SKIPPED-CNT", 1)
        B("ELSE")
        B("MOVE IN-KEY TO WL-KEY", 1)
        B("MOVE IN-TEXT TO WL-TEXT", 1)
        B("MOVE IN-AMOUNT TO WL-AMOUNT", 1)
        B("WRITE OUT-REC FROM WS-LINE", 1)
        B("ADD 1 TO WS-WRITTEN-CNT", 1)
        B("END-IF")
        B("PERFORM 1000-READ.")
    # padding paragraphs: field reformatting typical of the program kind
    n = r.randint(6, 18)
    for i in range(n):
        A(f"{5000 + i * 10}-FORMAT-{['DATE', 'CODE', 'AMOUNT', 'TEXT', 'BRANCH', 'KEY'][i % 6]}-{i // 6 + 1}.")
        cm(r.choice(["REFORMAT FOR THE OLD PRINT LAYOUT", "PAD AND ALIGN FOR THE TAPE RECORD",
                     "CONVERT CARD-IMAGE FIELD", "NORMALISE FIELD FOR OUTPUT", "LEGACY EDIT RULE"]))
        fld = in_fields[i % len(in_fields)][0]
        if fld == "FILLER":
            fld = in_fields[0][0]
        B(f"IF {fld} = LOW-VALUES")
        B(f"MOVE SPACES TO {fld}" if "AMOUNT" not in fld else f"MOVE ZERO TO {fld}", 1)
        B("END-IF")
        B(f"INSPECT {fld} REPLACING ALL LOW-VALUES BY SPACES." if "AMOUNT" not in fld else "CONTINUE.")
    return s, facts


def archive_readme() -> Src:
    s = Src(fixed=False)
    for ln in ["# cobol-archive", "",
               "Programs retired from production CLARA. They are kept for reference only: they are not",
               "compiled, not bound and not part of any job in `../jcl/`.", "",
               "Archived programs are self-contained sequential-file utilities (print layouts, tape and",
               "card-image conversions, one-off statistics). None of them reads or writes DB2.", "",
               "Do not copy logic from here into live programs without a review against the current rules.", ""]:
        s.emit(ln)
    return s


# ---------------------------------------------------------------------------------------------
# testdata (synthetic fixtures)
# ---------------------------------------------------------------------------------------------

def _val(r, c, i):
    t, n = c["type"], c["name"]
    if n.endswith("CLAIM_ID") or n in ("CLAIM_ID_A", "CLAIM_ID_B"):
        return f"UK2099{r.randint(1, 999):06d}"
    if t == "BIGINT":
        return str(900000 + i)
    if t in ("INTEGER", "SMALLINT"):
        return str(r.randint(1, 90))
    if t == "DECIMAL":
        return f"{r.randint(0, 25000)}.{r.randint(0, 99):02d}"
    if t == "DATE":
        return f"2099-{r.randint(1, 12):02d}-{r.randint(1, 28):02d}"
    if t == "TIMESTAMP":
        return f"2099-{r.randint(1, 12):02d}-{r.randint(1, 28):02d}-09.{r.randint(0, 59):02d}.00.000000"
    if c.get("pii"):
        return "*MASKED*"
    from .naming import enum_values
    vals = enum_values(c["description"], c.get("length", 0)) if t == "CHAR" else []
    if vals:
        return r.choice(vals)
    if n.endswith("_USER") or n == "USER_ID" or n.endswith("_BY"):
        return f"TESTU{r.randint(1, 9):03d}"
    if n.endswith("_PGM") or n == "PGM_ID" or n == "SOURCE_PGM":
        return "CLRTEST1"
    if "CURRENCY" in n:
        return r.choice(["GBP", "NOK", "SEK", "DKK"])
    if t == "CHAR":
        return ("T" + str(r.randint(0, 10 ** 6))).ljust(min(c["length"], 8))[:c["length"]].strip()
    return "TEST VALUE"


def fixture_csv(W, table) -> Src:
    t = W.tables[table]
    r = util.rng(f"code_legacy:fixture:{table}")
    s = Src(fixed=False)
    cols = [c for c in t["columns"]]
    s.emit(",".join(c["name"] for c in cols))
    for i in range(r.randint(6, 14)):
        row = []
        for c in cols:
            v = _val(r, c, i)
            if c["nullable"] and r.random() < 0.15:
                v = ""
            if "," in v:
                v = '"' + v + '"'
            row.append(v)
        s.emit(",".join(row))
    return s


def testdata_readme() -> Src:
    s = Src(fixed=False)
    for ln in ["# CLARA test data", "",
               "Synthetic fixtures for unit and regression runs of the CLARA batch programs.", "",
               "- `db2/<TABLE>.csv`: rows to load into a test copy of the `CLR` schema (one file per table;",
               "  `CLR.T_PARAM` is not included - load `../ddl/T_PARAM_seed.sql` instead).",
               "- `interfaces/`: sample interface records in display format.",
               "- `expected/`: control-report totals expected from a run over the fixtures.",
               "- `jcl/`: job streams that run single programs against the test schema.", "",
               "All values are made up. Claim ids use the 2099 test range (`UK2099nnnnnn`) and personal",
               "fields are masked, so no fixture row describes a real claim or person.", ""]:
        s.emit(ln)
    return s


def interface_sample(name) -> Src:
    r = util.rng(f"code_legacy:ifsample:{name}")
    s = Src(fixed=False)
    if name == "RSVMOVE":
        s.emit("# RSVMOVE sample records (display format, one field per column; packed fields shown unpacked)")
        s.emit("# REC-TYPE|VERSION|EXTRACT-DATE|CLAIM-ID|RSV-ID|MOVE-ID|MOVE-TYPE|CCY|AMOUNT|GBP-AMOUNT|PRODUCT|PERIL|TIER|MOVE-TS")
        for i in range(12):
            ccy = r.choice(["GBP", "NOK", "SEK", "DKK"])
            amt = r.randint(-5000, 40000)
            s.emit(f"MV|02|2099-01-{(i % 27) + 1:02d}|UK2099{r.randint(1, 999):06d}|{900100 + i}|{910100 + i}|"
                   f"{r.choice(['IN', 'AD', 'IX', 'RV', 'ST', 'RC'])}|{ccy}|{amt}.00|{amt}.00|"
                   f"{r.choice(['MOTUK', 'HOMUK', 'HOMSE', 'MOTNO'])}|{r.choice(['COL', 'EOW', 'THF', 'STM'])}|"
                   f"{r.choice('123')}|2099-01-{(i % 27) + 1:02d}-02.{r.randint(10, 59)}.00.000000")
    elif name == "SENTREQ1":
        s.emit("# SENTREQ1 sample requests: CLAIM-ID|PRODUCT|PERIL|LOSS-DATE|NOTIFIED-TS")
        for i in range(10):
            s.emit(f"UK2099{r.randint(1, 999):06d}|{r.choice(['MOTUK', 'HOMUK'])}|{r.choice(['COL', 'EOW', 'THF'])}|"
                   f"2099-02-{i + 1:02d}|2099-02-{i + 1:02d}-10.15.00.000000")
    else:
        s.emit("# SENTRSP1 sample responses: CLAIM-ID|SCORE|MODEL-VERSION|REASON-1|REASON-2")
        for i in range(10):
            s.emit(f"UK2099{r.randint(1, 999):06d}|{r.randint(1, 99):03d}|TESTMDL1|R{r.randint(10, 99)}|R{r.randint(10, 99)}")
    return s


def expected_report(W, pid) -> Src:
    r = util.rng(f"code_legacy:expected:{pid}")
    p = W.programs[pid]
    s = Src(fixed=False)
    s.emit(f"# Expected control-report totals for {pid} over the fixtures in ../db2/")
    for t in p["reads_tables"]:
        s.emit(f"{t} ROWS READ{'':<{40 - len(t) - 10}}{r.randint(5, 14):>11}")
    for t in p["writes_tables"]:
        s.emit(f"{t} ROWS WRITTEN{'':<{40 - len(t) - 13}}{r.randint(0, 14):>11}")
    s.emit(f"{'REJECTS':<40}{0:>11}")
    s.emit("RETURN CODE 0")
    return s


def test_jcl(W, pid) -> Src:
    p = W.programs[pid]
    s = Src(fixed=False)
    s.emit(f"//T{pid[3:]:<7} JOB (CLR,TEST),'UNIT TEST {pid}',CLASS=T,MSGCLASS=X,NOTIFY=&SYSUID")
    s.emit(f"//* UNIT TEST RUN OF {pid} AGAINST THE TEST SCHEMA (FIXTURES IN testdata/db2)")
    s.emit("//         INCLUDE MEMBER=CLRTSYMS")
    s.emit("//STEP010  EXEC PGM=IKJEFT01,DYNAMNBR=20")
    s.emit("//STEPLIB  DD DSN=&TSTHLQ..LOADLIB,DISP=SHR")
    s.emit("//SYSTSPRT DD SYSOUT=*")
    s.emit("//SYSPRINT DD SYSOUT=*")
    s.emit("//RPTOUT   DD SYSOUT=*")
    s.emit("//SYSTSIN  DD *,SYMBOLS=JCLONLY")
    s.emit("  DSN SYSTEM(&TSTSSID)")
    s.emit(f"  RUN PROGRAM({pid}) PLAN(&TSTPLAN) -")
    s.emit("      LIB('&TSTHLQ..LOADLIB')")
    s.emit("  END")
    s.emit("/*")
    s.emit("//")
    return s
