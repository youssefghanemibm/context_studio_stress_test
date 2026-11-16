"""LD012 — Claims Handling Manual v6.1 (approved 2023-05-15, superseded by v7.2 on 2026-06-30).

Older structure and numbering, 'case handler' / 'FRAUDNET score' / 'loss adjuster' terminology,
and only facts true on 2023-05-15. Holds the old values planted by contradiction placements.
"""
from __future__ import annotations

import pathlib
import re

import yaml

from generators.common import util
from . import figures
from .common_content import rule_p
from .prose import STYLE_V61
from .spec import Spec, long_date, money

FID = "LD012"
DOC_DATE = "2023-05-15"
AS_OF = "2023-05-15"
HEADER = "Claims Handling Manual v6.1 — Approved 15 May 2023 — Owner: Ingrid Sørensen, Claims Director"
FOOTER = "CS-MAN-006 rev 6.1   |   Classification: Internal"

# tokens that must never appear in a 2023 document
ANACHRONISMS = ["Sentinel", "Claims Hub", "reserve-engine", "reserve-svc", "Wave ", "Evidence Vault", "MyCorvane",
                "Assessor Portal", "Counter-Fraud & SIU", "Programme Skerry", "2024", "2025", "2026", "2027", "Ashby",
                "Recoveries & Subrogation", "Head of Recoveries", "CS-MAN-007", "second Tuesday"]


def scrub(t: str) -> str:
    t = t.replace(" (FRAUDNET before 2025-03-01)", "")
    t = t.replace("FRAUDNET/Sentinel", "FRAUDNET").replace("Sentinel", "FRAUDNET")
    t = re.sub(r"\s*\(CLRGL090; reserve-engine revaluation runs from Wave 2\)", " (CLRGL090)", t)
    t = re.sub(r"\s*Withdrawn from 2026-04-01:.*$", "", t)
    t = t.replace("external Claims Assessor (loss adjuster)", "external loss adjuster")
    t = t.replace("Claims Assessor reports", "Loss adjuster reports").replace("Claims Assessor", "loss adjuster")
    t = t.replace("Claims Handlers", "case handlers").replace("Claims Handler", "case handler")
    t = t.replace(" (pre-2026)", "").replace("(NISA Circular 2026/04)", "").strip()
    return t[:1].upper() + t[1:]


def _rp(S, rid, **kw):
    v = S.rv(rid)
    return rule_p(S, rid, text=scrub(v["text"]), **kw)


# chapter plan: (title, span pages, topic)
CHAPTERS = [
    ("Glossary of terms", 10, "governance"), ("Roles, responsibilities and authorities", 9, "governance"),
    ("Treating claimants fairly", 7, "customer"), ("Notification of loss", 13, "fnol"),
    ("Claim set-up and data capture", 7, "data"), ("Claim tiering and allocation", 12, "triage"),
    ("Fast-track settlement", 6, "fasttrack"), ("Loss adjusters and assessment", 13, "assessment"),
    ("Inspection and desk review", 9, "assessment"), ("Motor claims", 10, "motor"),
    ("Household claims", 10, "property"), ("Commercial and liability claims", 11, "commercial"),
    ("Nordic branch procedures", 10, "nordic"), ("Initial and default reserves", 6, "reserving"),
    ("Reserving standards", 10, "reserving"), ("Reserve authority limits", 5, "authority"),
    ("Reinsurance notification and large losses", 7, "largeloss"), ("Reserve review and monitoring", 8, "reviews"),
    ("Litigation management", 7, "litigation"), ("Settlement and offers", 10, "settlement"),
    ("Payments and authorities", 8, "payments"), ("Sanctions screening", 4, "sanctions"),
    ("Fraud awareness", 12, "fraud"), ("Fraud indicators and FRAUDNET", 14, "fraud"),
    ("The Special Investigations Unit", 8, "siu"), ("Surveillance and investigation standards", 6, "siu"),
    ("Fraud referral", 10, "fraud"), ("Recoveries and subrogation", 15, "recoveries"),
    ("Salvage", 5, "salvage"), ("Complaints", 6, "customer"), ("Closure and reopening", 6, "closure"),
    ("Records management and retention", 8, "records"), ("Appendices", 12, "governance"),
]
TOTAL = 300


def build(W, fig_dir: pathlib.Path) -> Spec:
    S = Spec(W, FID, AS_OF, STYLE_V61, "LD012:v61", v61=True)
    S.doc_date = DOC_DATE
    PL = {p["placement_id"]: p for p in W.placements_for(FID)}
    S.PL = PL
    d = DOC_DATE
    nm = lambda pid: W.name_of(pid, d)
    tt = lambda pid: W.title_of(pid, d)
    starts = {}
    pg = 7
    for i, (title, span, topic) in enumerate(CHAPTERS, start=2):
        starts[i] = pg
        pg += span
    assert pg - 1 == TOTAL, pg
    figs = _figures(fig_dir)

    def ch(n):
        t, _, topic = CHAPTERS[n - 2]
        return S.h1(n, t, starts[n], topic)

    # ---------------------------------------------------------------- title + chapter 1
    S.new_seg("title", ("first",), 1, fill=False)
    S.blocks.append({"t": "title_page", "top_space": 170, "gap": 18, "lines": [
        ("CORVANE MUTUAL INSURANCE SOCIETY LIMITED", 14, True), ("CLAIMS HANDLING MANUAL", 28, True),
        ("Issue 6.1", 18, False), ("Approved 15 May 2023", 13, False),
        (f"Manual owner: {nm('P005')}, {tt('P005')}", 13, False),
        ("Claims Operations UK  ·  Claims Operations Nordics  ·  Special Investigations Unit  ·  Recoveries", 11, False)]})
    S.h1(1, "Introduction", 2, "governance")
    S.p("This manual sets the standards for handling claims made under policies issued by the Society. It applies to every "
        "case handler, Team Leader and Claims Manager, and to loss adjusters instructed by the Society when they act on our behalf.")
    S.table(["Field", "Value"], [
        ["Document", "Claims Handling Manual"], ["Issue", "6.1"], ["Approved", "15 May 2023"],
        ["Manual owner", f"{nm('P005')}, {tt('P005')}"], ["Issued by", "Claims Operations UK"],
        ["Reference", "See page footer"]], caption="Control sheet", widths=[4.5, 11.5],
        facts=[S.fact("temporal", "Manual v6.1 owner shown as Ingrid Sørensen, Claims Director (2023).", nm("P005"),
                      world_ref="PERSON:P005#name_history", row=4, col=1)])
    S.table(["Issue", "Date", "Notes"], [
        ["6.0", "—", "Draft for consultation; not issued."],
        ["6.1", "15 May 2023", "Fraud referral standard revised (FRAUDNET score); reserve and payment authority limits restated; "
                               "inspection timescales updated."]], caption="Issue history", widths=[2, 3, 11])
    rows = [[nm(p), tt(p)] for p in ["P005", "P011", "P012", "P010", "P009", "P008", "P015", "P033", "P037"]]
    S.table(["Signatory", "Role"], rows, caption="Sign-off", widths=[6, 10],
            facts=[S.fact("temporal", "In May 2023 Martin Calloway was the Recoveries Manager and signed off manual v6.1.",
                          "Martin Calloway", world_ref="PERSON:P015#titles", row=7, col=0)])
    S.new_seg("toc", ("text", "Contents"), 4, fill=False)
    S.blocks.append({"t": "pagebreak"})
    S.blocks.append({"t": "toc", "title": "Contents"})
    S.h2("1.1", "Purpose", seg_id="c1s", target=None)
    S.segs[-1]["elastic"] = True
    S.prose_p((3, 4))
    S.h2("1.2", "Layout of the manual")
    S.p("Chapters follow the order in which a claim is normally handled. Standards are identified by their reference "
        "(for example BR-FNOL-002). Where a standard has changed since the previous issue, the new wording applies from its effective date.")
    S.h2("1.3", "Status of guidance notes")
    S.prose_p((2, 3))

    # ---------------------------------------------------------------- 2 glossary
    ch(2)
    S.h2("2.1", "General")
    S.prose_p()
    S.h2("2.2", "Terms used in this manual")
    terms = [
        ("Case handler", "The member of staff responsible for the day-to-day handling of a claim."),
        ("Loss adjuster", "A person who inspects or desk-reviews a loss and reports an estimate and a view on cover. "
                          "Panel firms and the Society's own staff may act as loss adjusters."),
        ("Claimant", "The person making the claim, usually the policyholder (a member of the Society)."),
        ("FRAUDNET score", "The fraud risk score from 0 to 100 produced by FRAUDNET for every new claim."),
        ("Peril", "The cause of loss under which the claim is made, recorded as a peril code."),
        ("Case reserve", "The estimated outstanding cost of the claim, held by reserve type."),
        ("Special Investigations Unit (SIU)", "The team that investigates claims referred because of fraud concerns."),
        ("Recoveries", "Recovery of the Society's outlay from a responsible third party or its insurer, including subrogation."),
    ]
    for term, defi in terms:
        S.p(runs=[{"text": term + ". ", "bold": True}, {"text": defi}],
            facts=[S.fact("terminology", f"Manual v6.1 defines '{term}': {defi}", defi[:55].rstrip(" ,.;"), world_ref="GLOSSARY:G-007" if term == "Case handler" else None)] if term in ("Case handler", "FRAUDNET score") else None)
    S.h2("2.3", "Claim tiers")
    v = S.rv("BR-TRI-003")
    S.p(runs=[{"text": "Tier-3. ", "bold": True},
              {"text": "A claim is Tier-3 where the estimated incurred is £40,000 or more (NOK 500,000 / SEK 500,000 / DKK 340,000) or "
                       "the claim involves any bodily injury. Tier-2 covers £5,000 to £39,999 or any third-party involvement; all other claims are Tier-1 (BR-TRI-003)."}],
        facts=[S.fact("temporal", "Manual v6.1 (2023): Tier-3 threshold £40,000 (BR-TRI-003 v2, 2022-01-01 to 2024-12-31).",
                      "estimated incurred is £40,000 or more", world_ref="RULE:BR-TRI-003@v2#parameters",
                      notes="Superseded by BR-TRI-003 v3 (£50,000) from 2025-01-01.")])
    S.rule_sections["BR-TRI-003"] = "2.3"
    S.h2("2.4", "Abbreviations")
    S.table(["Abbreviation", "Meaning"], [["CLARA", "Claims Ledger And Reserve Application"], ["FNOL", "First notification of loss"],
                                          ["SIU", "Special Investigations Unit"], ["T3", "Tier-3 claim"], ["EOW", "Escape of water"],
                                          ["BI", "Bodily injury"], ["NISA", "National Insurance Supervisory Authority"],
                                          ["RSNC", "Reserve reason code list"]], caption="Abbreviations", widths=[4, 12])

    # ---------------------------------------------------------------- 3 roles
    ch(3)
    S.h2("3.1", "Responsibilities")
    S.prose_ps(2)
    S.h2("3.2", "Process owners")
    rows = []
    for sid, st in W.stages.items():
        own = W.owner_of_process(sid, d)
        rows.append([st["name"], nm(own), tt(own)])
    S.table(["Stage", "Owner", "Title"], rows, caption="Process owners", widths=[5, 5, 6],
            facts=[S.fact("temporal", "In 2023 the Recovery & Subrogation stage was owned by Martin Calloway (Recoveries Manager).",
                          "Recoveries Manager", world_ref="PROCESS:S7#owner_history", row=7, col=2,
                          notes="Owner from 2025-09-01 is Freya Lindahl; this 2023 manual is superseded.")])
    S.h2("3.3", "Teams")
    rows = []
    for t_ in ["T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10", "T11", "T12"]:
        lead = W.team_lead(t_, d)
        rows.append([W.team_name(t_, d), nm(lead) if lead else "—"])
    S.table(["Team", "Lead"], rows, caption="Claims teams", widths=[8, 8])
    S.h2("3.4", "Override of authority")
    _rp(S, "BR-GEN-001")
    _rp(S, "BR-GEN-007")

    # ---------------------------------------------------------------- 4 treating claimants fairly
    ch(4)
    S.h2("4.1", "Standards of service")
    S.prose_ps(2)
    S.h2("4.2", "Interpreters and language")
    _rp(S, "BR-GEN-009")
    _rp(S, "BR-FNOL-013")
    S.h2("4.3", "Claimants needing extra support")
    S.prose_ps(2)

    # ---------------------------------------------------------------- 5 notification of loss
    ch(5)
    S.h2("5.1", "Receiving the notification")
    S.prose_p()
    _rp(S, "BR-FNOL-002", needle="before a claim number is issued")
    S.h2("5.2", "Acknowledgement")
    _rp(S, "BR-FNOL-001", kind="temporal", needle="within 5 business days",
        notes="v1 (2012-01-01 to 2024-09-30). Superseded by v2 (2 business days, NISA Circular 2024/07) and v3 (1/2 business days).")
    S.h2("5.3", "Theft and third parties")
    _rp(S, "BR-FNOL-007")
    _rp(S, "BR-FNOL-008")
    S.h2("5.4", "Duplicate claims")
    _rp(S, "BR-FNOL-004", needle="within ±3 days")
    S.h2("5.5", "Late notification")
    _rp(S, "BR-FNOL-003", needle="more than 30 days after the date of loss")
    S.h2("5.6", "Brokers")
    _rp(S, "BR-FNOL-010")
    S.h2("5.7", "Emergency work")
    _rp(S, "BR-FNOL-019", needle="up to £500 at FNOL")
    S.h2("5.8", "Telematics alerts and online notification")
    _rp(S, "BR-FNOL-009")
    _rp(S, "BR-FNOL-011")
    S.p(f"Online notifications are received through {W.system_name('SYS04', d)}.",
        facts=[S.fact("alias_use", "In 2023 the customer portal was ClaimLine Web.", W.system_name("SYS04", d), world_ref="SYSTEM:SYS04#renames")])
    S.h2("5.9", "Storm events")
    _rp(S, "BR-FNOL-020")
    S.figure(figs["notify"], "Notification of loss",
             "Notification of loss: receive notification, check policy, create claim and default reserve, acknowledge within 5 business days.",
             alt_facts=[S.fact("alt_text", "v6.1 alt text (2023): acknowledge within 5 business days.", "acknowledge within 5 business days",
                               world_ref="RULE:BR-FNOL-001@v1", notes="Temporal: BR-FNOL-001 v1, superseded from 2024-10-01.")])

    # ---------------------------------------------------------------- 6 set-up
    ch(6)
    S.h2("6.1", "Mandatory information")
    S.prose_p()
    _rp(S, "BR-FNOL-006")
    _rp(S, "BR-FNOL-015")
    _rp(S, "BR-FNOL-018")
    S.h2("6.2", "Locations and personal numbers")
    _rp(S, "BR-FNOL-016")
    _rp(S, "BR-FNOL-017")
    S.h2("6.3", "The FNOL screen")
    bm = W.bms_maps["CLRM010"]
    S.p(f"FNOL is keyed on CLARA transaction {bm['transaction']} (map {bm['map']}).")
    S.prose_p()

    # ---------------------------------------------------------------- 7 tiering
    ch(7)
    S.h2("7.1", "Purpose")
    S.prose_p()
    S.h2("7.2", "FRAUDNET pre-screen")
    _rp(S, "BR-TRI-007", needle="within 15 minutes of FNOL")
    S.h2("7.3", "Tiering")
    S.p("Claims are tiered using the definitions in section 2.3.")
    _rp(S, "BR-TRI-009", kind="temporal", needle="Team Leader approval within 14 hours")
    S.h2("7.4", "Allocation")
    for rid in ["BR-TRI-004", "BR-TRI-001", "BR-TRI-002", "BR-TRI-005", "BR-TRI-016", "BR-TRI-017", "BR-TRI-018", "BR-TRI-011"]:
        _rp(S, rid)
    S.h2("7.5", "Storm surge")
    _rp(S, "BR-TRI-012")

    # ---------------------------------------------------------------- 8 fast-track
    ch(8)
    S.h2("8.1", "Eligibility")
    _rp(S, "BR-TRI-006", kind="temporal", needle="FRAUDNET score below 25 and no injury; cap £1,000")
    S.h2("8.2", "Payment without referral")
    _rp(S, "BR-STL-009")
    S.h2("8.3", "Checks")
    S.prose_p()

    # ---------------------------------------------------------------- 9 loss adjusters
    ch(9)
    S.h2("9.1", "When a loss adjuster is instructed")
    _rp(S, "BR-ASM-002", needle="above £10,000 require an external loss adjuster")
    S.h2("9.2", "Panel allocation")
    _rp(S, "BR-ASM-015")
    rows = []
    for vid in ["VEN-01", "VEN-02", "VEN-04", "VEN-06"]:
        ven = W.vendors[vid]
        rows.append([ven["name"], ven["location"]])
    S.table(["Firm", "Location"], rows, caption="Panel firms (assessment and repair)", widths=[9, 7])
    S.h2("9.3", "Nordic instructions")
    _rp(S, "BR-ASM-016")
    S.h2("9.4", "Conflicts")
    _rp(S, "BR-ASM-010")
    S.h2("9.5", "Instructions")
    S.p(f"Instructions and reports are exchanged through the {W.system_name('SYS17', d)}.",
        facts=[S.fact("alias_use", "In 2023 the assessor extranet was called the Adjuster Extranet.", W.system_name("SYS17", d),
                      world_ref="SYSTEM:SYS17#renames")])
    S.prose_p()

    # ---------------------------------------------------------------- 10 inspection
    ch(10)
    S.h2("10.1", "Method")
    _rp(S, "BR-ASM-001")
    _rp(S, "BR-ASM-003", kind="temporal", needle="below £4500")
    S.h2("10.2", "Timescales")
    _rp(S, "BR-ASM-005", kind="temporal", needle="Tier-3: 72 hours")
    S.h2("10.3", "Reports")
    _rp(S, "BR-ASM-004", kind="temporal", needle="at least 4 photos")
    S.h2("10.4", "Contents")
    _rp(S, "BR-ASM-018")
    S.h2("10.5", "Nordic takst")
    _rp(S, "BR-ASM-009")

    # ---------------------------------------------------------------- 11 motor
    ch(11)
    S.h2("11.1", "Repairs")
    _rp(S, "BR-ASM-007")
    S.h2("11.2", "Total loss")
    _rp(S, "BR-ASM-017", kind="temporal", needle="exceeds 48% of market value")
    _rp(S, "BR-REC-007")
    S.h2("11.3", "Collisions")
    _rp(S, "BR-REC-002")
    S.h2("11.4", "Glass")
    S.prose_p()

    # ---------------------------------------------------------------- 12 household
    ch(12)
    S.h2("12.1", "Escape of water")
    _rp(S, "BR-RSV-002")
    _rp(S, "BR-REC-016")
    S.h2("12.2", "Cash settlement of contents")
    _rp(S, "BR-STL-008", kind="temporal", needle="56% of replacement cost")
    S.h2("12.3", "Subsidence and flood")
    S.prose_ps(2)

    # ---------------------------------------------------------------- 13 commercial & liability
    ch(13)
    S.h2("13.1", "Commercial property")
    _rp(S, "BR-RSV-005")
    _rp(S, "BR-RSV-021")
    S.h2("13.2", "Liability and bodily injury")
    _rp(S, "BR-RSV-006")
    S.h2("13.3", "Interim payments")
    _rp(S, "BR-STL-010")

    # ---------------------------------------------------------------- 14 Nordic
    ch(14)
    S.h2("14.1", "Application of this manual")
    S.prose_p()
    S.h2("14.2", "Excess")
    for rid in ["BR-STL-016", "BR-STL-017", "BR-STL-018", "BR-STL-019", "BR-STL-020"]:
        _rp(S, rid)
    S.h2("14.3", "Currency")
    _rp(S, "BR-RSV-012", needle="Group Ledger month-end rate")
    S.h2("14.4", "Regress and correspondence")
    _rp(S, "BR-REC-008")
    _rp(S, "BR-REC-017")

    # ---------------------------------------------------------------- 15 initial reserves
    ch(15)
    S.h2("15.1", "Default reserve")
    _rp(S, "BR-FNOL-005")
    S.h2("15.2", "Initial reserve")
    _rp(S, "BR-RSV-001")

    # ---------------------------------------------------------------- 16 reserving standards
    ch(16)
    S.h2("16.1", "General standards")
    S.prose_ps(2)
    for rid in ["BR-RSV-015", "BR-RSV-008", "BR-RSV-013", "BR-RSV-016", "BR-RSV-020", "BR-RSV-023"]:
        _rp(S, rid)
    S.h2("16.2", "Bodily-injury indexation")
    _rp(S, "BR-RSV-009", kind="temporal", needle="2.5% per annum", notes="BR-RSV-009 v1 (2019-2023); later versions changed the rate.")
    S.h2("16.3", "Ceded reserves")
    _rp(S, "BR-RSV-024")

    # ---------------------------------------------------------------- 17 reserve authority
    ch(17)
    S.h2("17.1", "Limits")
    _rp(S, "BR-RSV-003", kind="temporal", needle="Team Leader £75,000; Claims Manager £400,000",
        notes="BR-RSV-003 v2 (2023-01-01 to 2025-08-31); v3 limits apply from 2025-09-01.")
    S.p("A case handler must not enter a reserve above their own authority.")

    # ---------------------------------------------------------------- 18 reinsurance
    ch(18)
    S.h2("18.1", "Large reserve movements")
    _rp(S, "BR-RSV-011", kind="temporal", needle="within 48 hours of any reserve movement of £200,000 or more",
        notes="BR-RSV-011 v1 (2018-2023); replaced by the LLNT rule (v2) from 2024-01-01.")
    S.h2("18.2", "Major losses")
    S.prose_p()

    # ---------------------------------------------------------------- 19 reserve review (PL-038)
    ch(19)
    S.h2("19.1", "Purpose")
    S.prose_p()
    S.h2("19.2", "Litigated claims")
    _rp(S, "BR-RSV-022")
    S.h2("19.3", "Reopened claims")
    _rp(S, "BR-RSV-017")
    S.h2("19.4", "Tier-3 reserve review")
    pl = S.PL["PL-038"]
    S.p(runs=[{"text": "Standard BR-RSV-007: ", "bold": True},
              {"text": "Reserves on Tier-3 claims must be reviewed at least every 30 days. The case handler records the review "
                       "on the file notes and sets the next diary date."}],
        facts=[S.placement_fact(pl, "Manual v6.1: reserves on Tier-3 claims must be reviewed at least every 30 days (BR-RSV-007 v1).",
                                "reviewed at least every 30 days",
                                notes="Superseded: 21 days from 2024-01-01 (v2) and 14 days from 2026-07-01 (v3, LD001 §19.4). See C04.")])
    S.rule_sections["BR-RSV-007"] = "19.4"
    S.h2("19.5", "Nil reserves")
    _rp(S, "BR-RSV-010")

    # ---------------------------------------------------------------- 20 litigation
    ch(20)
    S.h2("20.1", "Instructing solicitors")
    S.prose_p()
    S.h2("20.2", "Court timetable")
    S.prose_p()

    # ---------------------------------------------------------------- 21 settlement
    ch(21)
    S.h2("21.1", "Offers")
    _rp(S, "BR-STL-004")
    S.h2("21.2", "Letters")
    _rp(S, "BR-STL-006")
    S.h2("21.3", "Interest")
    _rp(S, "BR-STL-014")
    S.h2("21.4", "Closing the reserve")
    _rp(S, "BR-RSV-014")

    # ---------------------------------------------------------------- 22 payments
    ch(22)
    S.h2("22.1", "Payment authority")
    _rp(S, "BR-STL-002", kind="temporal", needle="Team Leader £50,000; Claims Manager £250,000",
        notes="BR-STL-002 v2 (2023-01-01 to 2025-08-31); Team Leader £75,000 from 2025-09-01 (v3).")
    S.h2("22.2", "Payees")
    _rp(S, "BR-STL-005")
    _rp(S, "BR-STL-012")
    S.h2("22.3", "Vendor invoices")
    _rp(S, "BR-STL-011")

    # ---------------------------------------------------------------- 23 sanctions
    ch(23)
    S.h2("23.1", "Screening")
    _rp(S, "BR-STL-007")

    # ---------------------------------------------------------------- 24 fraud awareness
    ch(24)
    S.h2("24.1", "Why fraud matters")
    S.prose_ps(2)
    S.h2("24.2", "Behaviour of case handlers")
    S.prose_ps(2)
    S.h2("24.3", "Feedback")
    _rp(S, "BR-FRD-017")

    # ---------------------------------------------------------------- 25 indicators
    ch(25)
    S.h2("25.1", "FRAUDNET")
    S.p("Every new claim is scored by FRAUDNET. The score is a risk indicator and is reviewed with the other information on the file.")
    S.h2("25.2", "Pre-screen indicators")
    rows = []
    for rid in ["BR-FRD-002", "BR-FRD-004", "BR-FRD-007", "BR-FRD-008", "BR-FRD-014", "BR-FRD-015"]:
        vv = S.rv(rid)
        rows.append([rid, W.rules[rid]["title"].replace("Indicator: ", ""), scrub(vv["text"])])
        S.rule_sections.setdefault(rid, "25.2")
    S.table(["Standard", "Indicator", "Points"], rows, caption="Pre-screen indicators", widths=[3, 5, 8])
    S.h2("25.3", "Linked claims")
    _rp(S, "BR-FRD-005", kind="temporal", needle="2 or more claims in 12 months")

    # ---------------------------------------------------------------- 26 SIU
    ch(26)
    S.h2("26.1", "Role of the SIU")
    S.p(f"The Special Investigations Unit is led by the {tt('P008')}, {nm('P008')}.")
    S.h2("26.2", "Triage of referrals")
    _rp(S, "BR-FRD-035", kind="temporal", needle="within 5 business days",
        notes="BR-FRD-035 v1; v2 (2026-04-01) reduced this to 3 business days.")
    S.h2("26.3", "Outcomes")
    _rp(S, "BR-FRD-011")
    _rp(S, "BR-FRD-013")

    # ---------------------------------------------------------------- 27 surveillance
    ch(27)
    S.h2("27.1", "Authorisation")
    _rp(S, "BR-FRD-010")
    S.h2("27.2", "Investigation standards")
    S.prose_ps(2)

    # ---------------------------------------------------------------- 28 fraud referral (PL-040)
    ch(28)
    S.h2("28.1", "When to refer")
    S.prose_ps(2)
    S.h2("28.2", "How to refer")
    S.p("Referrals are made on CLARA transaction FR03 (map CLRM410) and are passed to the SIU the same day.")
    S.h2("28.3", "Referral threshold")
    pl = S.PL["PL-040"]
    S.p(runs=[{"text": "Standard BR-FRD-012: ", "bold": True},
              {"text": "Refer a claim to the SIU when the FRAUDNET score is 70 or more. The threshold was lowered from 75 with effect from 1 April 2023."}],
        facts=[S.placement_fact(pl, "Manual v6.1: refer to SIU when the FRAUDNET score is 70 or more (BR-FRD-012 v2, from 2023-04-01).",
                                "FRAUDNET score is 70 or more",
                                notes="Superseded by BR-FRD-031 (Sentinel score 65, from 2026-04-01); Tier-3 at 60 from 2026-10-01.")])
    S.rule_sections["BR-FRD-012"] = "28.3"
    S.h2("28.4", "Automatic decline")
    _rp(S, "BR-FRD-019", kind="temporal", needle="FRAUDNET score is 90 or more",
        notes="BR-FRD-019 v2 was withdrawn from 2026-04-01 (NISA Circular 2026/04 §3.1 prohibits adverse decisions on a score alone).")
    S.figure(figs["referral"], "Fraud referral",
             "Fraud referral: a FRAUDNET score of 70 or more is referred to the SIU; a score of 90 or more leads to automatic decline.",
             facts=[S.fact("image_text", "v6.1 referral diagram (2023): FRAUDNET score of 70 or more is referred to SIU.", "Refer to SIU",
                           world_ref="RULE:BR-FRD-012@v2", notes="Temporal: superseded by BR-FRD-031 from 2026-04-01.")])

    # ---------------------------------------------------------------- 29 recoveries
    ch(29)
    S.h2("29.1", "Responsibility")
    S.p(f"Recoveries are managed by the Recoveries team, led by the {tt('P015')}, {nm('P015')}.")
    S.h2("29.2", "Identifying recoveries")
    _rp(S, "BR-REC-001")
    S.h2("29.3", "Pursuit threshold")
    _rp(S, "BR-REC-003", kind="temporal", needle="£750 or more",
        notes="BR-REC-003 v2 (2022-07-01 to 2025-08-31); £1,000 from 2025-09-01.")
    S.h2("29.4", "Solicitors")
    _rp(S, "BR-REC-005", kind="temporal", needle="£15,000 or more")
    S.h2("29.5", "Tracing and limitation")
    _rp(S, "BR-REC-006")
    _rp(S, "BR-REC-009")
    S.h2("29.6", "Write-offs and excess refunds")
    _rp(S, "BR-REC-011", kind="temporal", needle="above £5,000 require approval by the Recoveries Manager")
    _rp(S, "BR-REC-004")
    _rp(S, "BR-REC-013")
    _rp(S, "BR-REC-014")
    S.p(f"Subrogation cases are recorded in the {W.system_name('SYS24', d)}.")

    # ---------------------------------------------------------------- 30 salvage
    ch(30)
    S.h2("30.1", "Disposal")
    _rp(S, "BR-REC-015")
    S.prose_p()

    # ---------------------------------------------------------------- 31 complaints
    ch(31)
    S.h2("31.1", "Acknowledging complaints")
    _rp(S, "BR-GEN-003")
    S.h2("31.2", "Resolving complaints")
    S.prose_ps(2)

    # ---------------------------------------------------------------- 32 closure
    ch(32)
    S.h2("32.1", "Closure")
    S.prose_p()
    S.h2("32.2", "Reopening")
    S.prose_p()

    # ---------------------------------------------------------------- 33 records
    ch(33)
    S.h2("33.1", "Retention")
    _rp(S, "BR-GEN-004", kind="temporal", needle="7 years after closure")
    _rp(S, "BR-GEN-010")
    S.h2("33.2", "Access requests")
    _rp(S, "BR-GEN-002")

    # ---------------------------------------------------------------- 34 appendices
    ch(34)
    S.h2("34.1", "Appendix 1 — Standards in force")
    rows = []
    for rid in sorted(W.rules):
        vv = W.rule_version(rid, AS_OF)
        if not vv or not S.may(f"RULE:{rid}@v{vv['version']}", "text"):
            continue
        rows.append([rid, scrub(W.rules[rid]["title"]), f"v{vv['version']}", long_date(vv["effective_from"]),
                     S.rule_sections.get(rid, "—")])
    S.table(["Standard", "Title", "Issue", "Effective", "Section"], rows, caption="Standards in force at 15 May 2023",
            widths=[2.8, 7, 1.2, 3.2, 1.8], size=8)
    S.h2("34.2", "Appendix 2 — CLARA transactions")
    rows = [[m["transaction"], m["map"], m["title"]] for m in W.bms_maps.values()
            if W.programs[m["program"]]["since"] <= AS_OF]
    S.table(["Transaction", "Map", "Function"], rows, caption="CLARA transactions", widths=[3, 3, 10])
    S.h2("34.3", "Appendix 3 — File review checklist")
    S.table(["Item", "Checked"], [[x, "☐"] for x in [
        "Claim tiered and allocated", "FRAUDNET score reviewed", "Loss adjuster instructed where required",
        "Case reserve set and reason-coded", "Tier-3 review diary set", "Recovery potential considered"]],
        caption="File review checklist", widths=[13, 3])
    S.finish(TOTAL)
    return S


def _figures(fig_dir: pathlib.Path) -> dict:
    specs = {
        "notify": {"title": "Notification of loss", "cols": 4, "rows": 1, "nodes": {
            "a": (0, 0, "Receive notification", "box"), "b": (1, 0, "Check policy", "box"),
            "c": (2, 0, "Create claim and default reserve", "box"), "d": (3, 0, "Acknowledge claimant", "end")},
            "edges": [("a", "b", ""), ("b", "c", ""), ("c", "d", "5 business days")]},
        "referral": {"title": "Fraud referral (FRAUDNET)", "cols": 3, "rows": 2, "nodes": {
            "a": (0, 0, "FRAUDNET score", "box"), "b": (1, 0, "Score 70 or more?", "decision"),
            "c": (2, 0, "Refer to SIU", "end"), "d": (1, 1, "Continue handling", "box"), "e": (2, 1, "Score 90 or more: decline", "ext")},
            "edges": [("a", "b", ""), ("b", "c", "Yes"), ("b", "d", "No"), ("c", "e", "")]},
    }
    return {k: figures.render(sp, fig_dir / f"ld012_{k}.png") for k, sp in specs.items()}
