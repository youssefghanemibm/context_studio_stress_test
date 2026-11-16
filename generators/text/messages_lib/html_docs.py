"""TX073 (NISA letter), TX074 (staff newsletter, September 2025), TX075 (Sentinel calibration notes).

Facts carry html_xpath locators of the form //*[@id='...'] on the element that holds the text.
"""
from __future__ import annotations

import html as _h

from generators.common import util

from .core import W, FactSink, person, pick, short_date, long_date


def esc(s: str) -> str:
    return _h.escape(s, quote=True)


class HtmlDoc(FactSink):
    def __init__(self, fid: str, title: str, css: str, lang: str = "en-GB"):
        super().__init__(fid, W.anchor(fid)["filename"])
        self.title = title
        self.css = css
        self.lang = lang
        self.body: list[str] = []
        self.k = 0
        self.meta: list[tuple[str, str]] = []

    def nid(self) -> str:
        self.k += 1
        return f"{self.fid.lower()}-e{self.k:03d}"

    def raw(self, s: str):
        self.body.append(s)

    def el(self, tag: str, text: str, cls: str | None = None, facts=(), inner_html: str | None = None,
           eid: str | None = None) -> str:
        eid = eid or self.nid()
        c = f' class="{cls}"' if cls else ""
        content = inner_html if inner_html is not None else esc(text)
        self.body.append(f'<{tag} id="{eid}"{c}>{content}</{tag}>')
        for f in facts:
            self.record(eid, *f) if isinstance(f, tuple) else None
        return eid

    def record(self, eid: str, needle: str, statement: str = None, kind: str = "general", world_ref: str = None,
               key: str = None, notes: str = None):
        loc = {"kind": "html_xpath", "xpath": f"//*[@id='{eid}']"}
        if key:
            pf = self.placement_fields(key)
            if statement:
                pf["statement"] = statement
            self.add_fact(loc, needle, notes=notes, **pf)
        else:
            self.add_fact(loc, needle, statement, kind=kind, world_ref=world_ref, notes=notes)

    def html(self) -> str:
        metas = "\n".join(f'<meta name="{esc(k)}" content="{esc(v)}">' for k, v in self.meta)
        return ("<!DOCTYPE html>\n"
                f'<html lang="{self.lang}">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                f"{metas}\n<title>{esc(self.title)}</title>\n<style>\n{self.css}\n</style>\n</head>\n<body>\n"
                + "\n".join(self.body) + "\n</body>\n</html>\n")


# =============================================================================================
# TX073 – NISA letter on FR1 due dates (2026-04-08)
# =============================================================================================

LETTER_CSS = """body { font-family: Georgia, 'Times New Roman', serif; color: #1a1a1a; background: #ffffff; margin: 0; }
.page { max-width: 760px; margin: 32px auto; padding: 48px 56px; border: 1px solid #d0d0d0; }
.letterhead { border-bottom: 3px solid #123c69; padding-bottom: 12px; margin-bottom: 28px; }
.letterhead .org { font-size: 22px; font-weight: bold; color: #123c69; letter-spacing: 0.5px; }
.letterhead .addr { font-size: 12px; color: #444; }
.refs { font-size: 13px; margin-bottom: 20px; }
.refs td { padding: 2px 12px 2px 0; vertical-align: top; }
.addressee { margin-bottom: 24px; font-size: 14px; }
h1.subject { font-size: 15px; font-weight: bold; margin: 20px 0; }
p { font-size: 14px; line-height: 1.55; }
.sig { margin-top: 36px; }
.footer { margin-top: 40px; border-top: 1px solid #ccc; font-size: 11px; color: #555; padding-top: 8px; }
.mark { text-transform: uppercase; font-size: 11px; letter-spacing: 1px; color: #7a1f1f; }"""


def tx073():
    fid = "TX073"
    d = W.anchor(fid)["date"]
    it, ro, pu = person("P055", d), person("P037", d), person("P056", d)
    doc = HtmlDoc(fid, "NISA – NISA-FR1 submission dates – Corvane Mutual", LETTER_CSS)
    doc.meta += [("author", it.name), ("date", d), ("description", "Letter from NISA to Corvane Mutual on NISA-FR1 due dates")]
    doc.raw('<div class="page">')
    doc.raw('<div class="letterhead">')
    doc.el("div", "National Insurance Supervisory Authority", "org")
    doc.el("div", "1 Regent Quay, London E14 9ZZ  ·  Supervision – Insurance Conduct  ·  nisa.example", "addr")
    doc.raw("</div>")
    doc.el("div", "NISA – OFFICIAL", "mark")
    rid = doc.nid()
    doc.raw(f'<table class="refs" id="{rid}"><tbody>'
            "<tr><td>Our reference</td><td>SUP/INS/40417/2026/031</td></tr>"
            "<tr><td>Firm reference</td><td>NISA-FRN 40417</td></tr>"
            f"<tr><td>Date</td><td>{esc(short_date(d))}</td></tr>"
            "</tbody></table>")
    doc.record(rid, "NISA-FRN 40417", "Corvane Mutual's NISA firm reference is NISA-FRN 40417.", "general",
               "ORG:company#nisa_firm_reference")
    doc.el("div", "", "addressee", inner_html=(
        f"{esc(ro.name)}<br>{esc(ro.title)}<br>Corvane Mutual Insurance Society Limited<br>"
        "Corvane House<br>14 Tallowgate<br>London EC3N 9ZZ"))
    doc.el("p", "By email and post")
    doc.el("p", "Dear Ms Okafor,")
    doc.el("h1", "NISA Circular 2026/04 – Quarterly Fraud Referral Return (NISA-FR1): submission dates", "subject")
    e = doc.el("p", "I am writing to confirm the submission arrangements for the quarterly NISA-FR1 fraud referral "
                    "return introduced by paragraph 3.4 of NISA Circular 2026/04, Fair Treatment in Fraud Referral, "
                    "which took effect on 1 April 2026.")
    doc.record(e, "paragraph 3.4 of NISA Circular 2026/04", "The NISA-FR1 return is required by NISA Circular 2026/04 §3.4.",
               "general", "CIRCULAR:CIRC-2026-04#requirements")
    e = doc.el("p", "The return is due within 30 calendar days after the end of each calendar quarter. Your firm's "
                    "first return covers the quarter from 1 April to 30 June 2026 (2026Q2) and is due by 30 July 2026.")
    doc.record(e, "Your firm's first return covers the quarter from 1 April to 30 June 2026 (2026Q2) and is due by 30 July 2026",
               key="tx73_letter")
    doc.record(e, "due within 30 calendar days after the end of each calendar quarter",
               "NISA-FR1 is due within 30 calendar days after each quarter end.", "needle", "REPORT:NISA-FR1#due")
    e = doc.el("p", "The following return, for 2026Q3, will be due by 30 October 2026. Returns should be submitted "
                    "through the NISA reporting portal in the published XML format.")
    doc.record(e, "for 2026Q3, will be due by 30 October 2026", "The 2026Q3 NISA-FR1 return is due by 2026-10-30.",
               "general", "REPORT:NISA-FR1#submissions.2026Q3.due")
    e = doc.el("p", "We note that the return will be signed by the firm's Compliance Manager – Conduct & "
                    "Counter-Fraud, and that you will be the named signatory for Corvane Mutual.")
    doc.record(e, "signed by the firm's Compliance Manager – Conduct & Counter-Fraud",
               "NISA-FR1 is signed by the Compliance Manager – Conduct & Counter-Fraud (Ruth Okafor at Corvane).",
               "general", "REPORT:NISA-FR1#signed_by_role")
    e = doc.el("p", "Please also note that paragraph 3.5 of the Circular requires referral records to be retained "
                    "for 7 years, and that the data in each return should be reconcilable to those records.")
    doc.record(e, "referral records to be retained for 7 years", "Circular 2026/04 §3.5: retain referral records for 7 years.",
               "general", "CIRCULAR:CIRC-2026-04#requirements")
    doc.el("p", "If you expect any difficulty in meeting a submission date, please contact me before the due date "
                "so that we can discuss it. Questions on the policy intent of the Circular may be directed to my "
                "colleague Petter Ulvestad, who is copied.")
    doc.el("p", "Yours sincerely,")
    doc.raw('<div class="sig">')
    e = doc.el("p", "", inner_html=f"<strong>{esc(it.name)}</strong><br>{esc(it.title)}<br>National Insurance Supervisory Authority")
    doc.record(e, f"{it.name} {it.title}", f"The NISA letter on FR1 due dates was signed by {it.name}, {it.title}.",
               "general", "PERSON:P055#titles")
    doc.raw("</div>")
    doc.el("p", f"cc: {pu.name}, {pu.title}, NISA")
    doc.el("div", "National Insurance Supervisory Authority, 1 Regent Quay, London E14 9ZZ. This letter is "
                  "addressed to the named firm only.", "footer")
    doc.raw("</div>")
    return doc


# =============================================================================================
# TX074 – staff newsletter, September 2025
# =============================================================================================

NEWS_CSS = """body { font-family: Arial, Helvetica, sans-serif; background: #f2f4f7; color: #222; margin: 0; }
header.mast { background: #0b4f6c; color: #fff; padding: 18px 28px; }
header.mast .name { font-size: 28px; font-weight: bold; letter-spacing: 1px; }
header.mast .issue { font-size: 13px; opacity: 0.9; }
nav { background: #e3eaf0; padding: 8px 28px; font-size: 13px; }
nav a { color: #0b4f6c; margin-right: 14px; text-decoration: none; }
.wrap { display: flex; gap: 24px; max-width: 1080px; margin: 20px auto; padding: 0 16px; }
main { flex: 3; }
aside { flex: 1; background: #fff; padding: 14px 16px; border-top: 4px solid #f0a500; align-self: flex-start; }
article { background: #fff; padding: 18px 22px; margin-bottom: 18px; border-left: 4px solid #0b4f6c; }
article h2 { margin-top: 0; font-size: 20px; color: #0b4f6c; }
.byline { font-size: 12px; color: #666; margin-bottom: 10px; }
table.moves { border-collapse: collapse; width: 100%; font-size: 13px; }
table.moves th, table.moves td { border: 1px solid #ccd6dd; padding: 6px 8px; text-align: left; }
table.moves th { background: #eef3f6; }
footer { text-align: center; font-size: 11px; color: #666; padding: 18px; }"""


def tx074():
    fid = "TX074"
    d = W.anchor(fid)["date"]
    df = person("P004", d)
    doc = HtmlDoc(fid, "Corvane Connect – Staff Newsletter – September 2025", NEWS_CSS)
    doc.meta += [("author", df.name), ("date", d), ("description", "Corvane Connect staff newsletter, September 2025 issue")]
    doc.raw('<header class="mast">')
    doc.el("div", "Corvane Connect", "name")
    doc.el("div", "Staff newsletter · September 2025 · Issue 9", "issue")
    doc.raw("</header>")
    doc.raw('<nav><a href="#art1">Re-organisation</a><a href="#art2">Assessor Portal</a><a href="#art3">New CFO</a>'
            '<a href="#art4">Programme Skerry</a><a href="#art5">Limits</a><a href="#art6">Around the offices</a></nav>')
    doc.raw('<div class="wrap"><main>')

    # ---- article 1: re-organisation (placement PL-234)
    doc.raw('<article id="art1">')
    doc.el("h2", "A new shape for Claims, Risk and Finance")
    doc.el("div", f"By {df.name}, {df.title}", "byline")
    e = doc.el("p", "The re-organisation of our Claims, Risk & Compliance and Finance functions took effect on "
                    "Monday 1 September 2025. Here is what changed and who is now leading what.")
    doc.record(e, "took effect on Monday 1 September 2025", "The Corvane re-organisation took effect on 2025-09-01.",
               "general", "EVENT:EV-018")
    e = doc.el("p", "Recoveries & Subrogation becomes a Group function, led by Freya Lindahl as Head of Recoveries & "
                    "Subrogation. Freya reports to the Claims Director, Ingrid Ashby (née Sørensen), and owns the "
                    "recovery and subrogation process for every region from 1 September.")
    doc.record(e, "Ingrid Ashby (née Sørensen)", key="tx74_nee")
    doc.record(e, "led by Freya Lindahl as Head of Recoveries & Subrogation",
               "From 2025-09-01 Freya Lindahl is Head of Recoveries & Subrogation (Group) and owns the subrogation process.",
               "temporal", "PERSON:P013#titles")
    e = doc.el("p", "Our Special Investigations Unit becomes Counter-Fraud & SIU and moves from Claims into Risk & "
                    "Compliance. Niall Brannigan becomes Head of Counter-Fraud & SIU, reporting to Karin Holmberg, "
                    "Chief Risk Officer.")
    doc.record(e, "Niall Brannigan becomes Head of Counter-Fraud & SIU, reporting to Karin Holmberg",
               "From 2025-09-01 Niall Brannigan is Head of Counter-Fraud & SIU reporting to the CRO, Karin Holmberg; SIU "
               "moved into Risk & Compliance.", "temporal", "PERSON:P008#reports_to")
    e = doc.el("p", "Siobhan Quill, who has led Recoveries as Acting Recoveries Manager since January, becomes "
                    "Recoveries Team Leader – UK, reporting to Freya. Thank you, Siobhan, for steering the team "
                    "through the year.")
    doc.record(e, "Acting Recoveries Manager since January",
               "Siobhan Quill was Acting Recoveries Manager from 2025-01-01 to 2025-08-31, then Recoveries Team Leader – UK.",
               "temporal", "PERSON:P014#titles")
    doc.el("p", "Other leadership changes from 1 September:")
    moves = []
    for pid in ["P009", "P011", "P012", "P016", "P017"]:
        before = person(pid, "2025-08-31")
        after = person(pid, "2025-09-01")
        mgr = W.manager_of(pid, "2025-09-01")
        moves.append((after.name, before.title, after.title, person(mgr, "2025-09-01").name if mgr else "–"))
    tid = doc.nid()
    rows = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(m)}</td></tr>" for a, b, c, m in moves)
    doc.raw(f'<table class="moves" id="{tid}"><thead><tr><th>Name</th><th>Previous role</th><th>New role</th>'
            f"<th>Reports to</th></tr></thead><tbody>{rows}</tbody></table>")
    doc.record(tid, "Head of Reserving", "From 2025-09-01 Lena Kristiansen is Head of Reserving, reporting to the CFO.",
               "temporal", "PERSON:P009#titles")
    doc.record(tid, "Head of Legacy Claims Platforms",
               "From 2025-09-01 Graham Pocock is Head of Legacy Claims Platforms, reporting to Neil Haworth.",
               "temporal", "PERSON:P016#titles")
    e = doc.el("p", "The Claims Hub Product team moves from Technology into Claims, and Claims Operations UK is now "
                    "Claims Operations (Group). Lena Kristiansen also takes over as chair of the Reserving Committee.")
    doc.record(e, "Lena Kristiansen also takes over as chair of the Reserving Committee",
               "Lena Kristiansen chairs the Reserving Committee from 2025-09-01.", "temporal", "COMMITTEE:COM-01#chair_history")
    doc.raw("</article>")

    # ---- article 2: Assessor Portal
    doc.raw('<article id="art2">')
    doc.el("h2", "Adjuster Extranet is now Assessor Portal")
    doc.el("div", "Claims Assessment UK", "byline")
    e = doc.el("p", "From 1 September 2025 the Adjuster Extranet is called Assessor Portal, so that the system name "
                    "matches the role we now use everywhere: Claims Assessor. Nothing changes for vendor assessors "
                    "beyond the name on screen; the change was delivered under CHUB-157.")
    doc.record(e, "From 1 September 2025 the Adjuster Extranet is called Assessor Portal",
               "Adjuster Extranet was renamed Assessor Portal on 2025-09-01 (CHUB-157).", "alias_use",
               "SYSTEM:SYS17#renames")
    doc.el("p", "Questions to Imran Talwar's team in Claims Assessment UK.")
    doc.raw("</article>")

    # ---- article 3: new CFO
    doc.raw('<article id="art3">')
    doc.el("h2", "Welcome to our new CFO")
    doc.el("div", "Executive Office", "byline")
    e = doc.el("p", "Priya Raman joined Corvane as Chief Financial Officer on 1 July 2025, succeeding Gareth "
                    "Whitcombe, who left at the end of June after six years as CFO. Priya leads finance, reserving, "
                    "actuarial, treasury and payments.")
    doc.record(e, "Priya Raman joined Corvane as Chief Financial Officer on 1 July 2025, succeeding Gareth Whitcombe",
               "Priya Raman became CFO on 2025-07-01, succeeding Gareth Whitcombe (CFO until 2025-06-30).",
               "temporal", "PERSON:P001#role_aliases")
    doc.raw("</article>")

    # ---- article 4: programme
    doc.raw('<article id="art4">')
    doc.el("h2", "Programme Skerry: Claims Hub MVP on track for November")
    doc.el("div", "Programme Skerry team", "byline")
    e = doc.el("p", "The first release of Claims Hub – first notice of loss and triage for our digital channels – is "
                    "planned to go live on 3 November 2025. Claims Hub will replace CLARA in waves, with CLARA "
                    "remaining the system of record for claims that have not yet moved.")
    doc.record(e, "planned to go live on 3 November 2025", "The Claims Hub MVP (FNOL and triage, digital channels) went live on 2025-11-03.",
               "general", "EVENT:EV-020")
    doc.el("p", "Look out for demo sessions in Leeds, Glasgow and London over the coming weeks.")
    doc.raw("</article>")

    # ---- article 5: limits and thresholds
    doc.raw('<article id="art5">')
    doc.el("h2", "New authority limits and recovery threshold from 1 September")
    doc.el("div", "Claims Standards", "byline")
    e = doc.el("p", "Revised reserve and payment authority limits (BR-RSV-003 v3 and BR-STL-002 v3) apply from "
                    "1 September 2025. For example, a Claims Handler can now authorise payments up to £15,000 and a "
                    "Team Leader up to £75,000.")
    doc.record(e, "a Claims Handler can now authorise payments up to £15,000 and a Team Leader up to £75,000",
               "BR-STL-002 v3 (from 2025-09-01): payment authority Claims Handler £15,000, Team Leader £75,000.",
               "temporal", "RULE:BR-STL-002@v3#parameters.team_leader")
    e = doc.el("p", "The subrogation pursuit threshold also rises: from 1 September we pursue subrogation where the "
                    "recoverable amount is £1,000 or more (BR-REC-003 v3).")
    doc.record(e, "from 1 September we pursue subrogation where the recoverable amount is £1,000 or more",
               "BR-REC-003 v3: from 2025-09-01 subrogation is pursued at £1,000 or more (previously £750).",
               "temporal", "RULE:BR-REC-003@v3#parameters.min_gbp")
    doc.raw("</article>")

    # ---- article 6: colour
    doc.raw('<article id="art6">')
    doc.el("h2", "Around the offices")
    doc.el("p", "Leeds: the Aire Point charity bake sale returns at the end of the month – bakers please sign up "
                "with the facilities desk.")
    doc.el("p", "Oslo: thank you to everyone who joined the summer gathering at Fjordporten.")
    doc.el("p", "Glasgow: the Clydeview House quiz team kept its title for a second year.")
    doc.raw("</article>")
    doc.raw("</main>")

    doc.raw("<aside>")
    doc.el("h3", "Dates for your diary")
    doc.raw("<ul>")
    doc.el("li", "1 September – re-organisation and new authority limits take effect")
    doc.el("li", "3 November – planned Claims Hub MVP go-live")
    doc.el("li", "Monthly – Programme Skerry Steering Committee updates on the intranet")
    doc.raw("</ul>")
    doc.el("h3", "Contact")
    doc.el("p", "Internal Communications, Executive Office, Corvane House")
    doc.raw("</aside></div>")
    doc.el("footer", f"Corvane Connect is published by the office of the {df.title}. Corvane Mutual Insurance "
                     "Society Limited, Corvane House, 14 Tallowgate, London EC3N 9ZZ.")
    return doc


# =============================================================================================
# TX075 – Sentinel calibration meeting notes (2026-03-18)
# =============================================================================================

NOTES_CSS = """body { font-family: 'Segoe UI', Arial, sans-serif; margin: 24px auto; max-width: 900px; color: #202124; background: #fff; }
h1 { font-size: 24px; border-bottom: 2px solid #3c6e47; padding-bottom: 6px; }
h2 { font-size: 17px; color: #3c6e47; margin-top: 26px; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 14px; }
th, td { border: 1px solid #c8d3cb; padding: 6px 9px; text-align: left; vertical-align: top; }
th { background: #eaf2ec; }
.meta td:first-child { font-weight: bold; width: 160px; }
.note { font-size: 12px; color: #5f6368; }"""


def tx075():
    fid = "TX075"
    d = W.anchor(fid)["date"]
    ol = person("P027", d)
    doc = HtmlDoc(fid, "Meeting Notes – Sentinel Calibration (SNT-4.2)", NOTES_CSS)
    doc.meta += [("author", ol.name), ("date", d)]
    doc.el("h1", "Meeting Notes – Sentinel Calibration (SNT-4.2)")
    mid = doc.nid()
    attendees = ["P027", "P008", "P037", "P028", "P042"]
    att = "; ".join(f"{person(p, d).name} ({person(p, d).title})" for p in attendees)
    doc.raw(f'<table class="meta" id="{mid}"><tbody>'
            f"<tr><td>Date</td><td>{esc(long_date(d))}, 10:00–11:00</td></tr>"
            "<tr><td>Location</td><td>Stockholm office and video</td></tr>"
            f"<tr><td>Attendees</td><td>{esc(att)}</td></tr>"
            f"<tr><td>Notes by</td><td>{esc(ol.name)}, Sentinel model owner</td></tr>"
            "</tbody></table>")
    doc.record(mid, "Sentinel model owner", "Oskar Lindgren is the Sentinel model owner (model SNT-4.2).", "general",
               "PERSON:P027#responsibilities")
    doc.el("h2", "Purpose")
    e = doc.el("p", "Review the calibration of Sentinel model SNT-4.2, completed on 16 March 2026, ahead of the change "
                    "of referral threshold to 65 on 1 April 2026 (BR-FRD-031 v1), and agree the evidence needed for "
                    "paragraph 3.3 of NISA Circular 2026/04.")
    doc.record(e, "Sentinel model SNT-4.2, completed on 16 March 2026",
               "Sentinel model SNT-4.2 was calibrated on 2026-03-16.", "general", "SYSTEM:SYS03#model_calibrated")
    doc.el("h2", "Background")
    e = doc.el("p", "Sentinel scores every claim at FNOL and triage on a scale from 0 to 100. The current model, "
                    "SNT-4.2, is a gradient-boosted model supplied with the licensed scoring engine; Oskar Lindgren is "
                    "the model owner and Niall Brannigan the business owner of Sentinel.")
    doc.record(e, "Sentinel scores every claim at FNOL and triage on a scale from 0 to 100",
               "Sentinel scores every claim at FNOL/triage on a 0-100 scale (model SNT-4.2).", "general",
               "SYSTEM:SYS03#description")
    doc.el("p", "From 1 April 2026 NISA Circular 2026/04 requires score-based cut-offs to be calibrated and documented. "
                "The calibration reviewed today is the evidence for the 65 cut-off that replaces the current 70.")
    doc.el("h2", "Method")
    doc.raw("<ol>")
    doc.el("li", "Score the calibration sample with SNT-4.2 as deployed in production.")
    doc.el("li", "Compare the share of scored claims that would be referred at the current and the new threshold.")
    doc.el("li", "Check the outcome against SIU triage capacity and the requirements of the Circular.")
    doc.el("li", "Record the result and the sign-offs in the model documentation.")
    doc.raw("</ol>")
    doc.el("h2", "Calibration results")
    tid = doc.nid()
    doc.raw(f'<table id="{tid}"><thead><tr><th>Threshold (Sentinel score)</th><th>Rule</th><th>Period</th>'
            "<th>Share of scored claims referred</th></tr></thead><tbody>"
            "<tr><td>70</td><td>BR-FRD-012 v2</td><td>Current, until 31 March 2026</td>"
            "<td>as reported in the quarterly claims KPI dashboard</td></tr>"
            "<tr><td>65</td><td>BR-FRD-031 v1</td><td>From 1 April 2026</td>"
            "<td>2.9% of scored claims (expected under SNT-4.2)</td></tr>"
            "</tbody></table>")
    doc.record(tid, "2.9% of scored claims", key="tx75_share",
               notes="The row for 70 points to the quarterly KPI dashboard instead of stating the observed share (PL-103 is exclusive to VS013).")
    doc.el("p", "Scores run from 0 to 100. The calibration uses the model as deployed; no other thresholds were "
                "assessed in this session.", "note")
    doc.el("h2", "Discussion")
    doc.raw("<ul>")
    e = doc.el("li", "Ruth Okafor confirmed that paragraph 3.3 requires score-based cut-offs to be calibrated and "
                     "documented, and that on a 0–100 scale the cut-off must not exceed 65; these notes and the "
                     "calibration pack form part of that evidence.")
    doc.record(e, "on a 0–100 scale the cut-off must not exceed 65",
               "Circular 2026/04 §3.3: score-based cut-offs must be calibrated and documented and must not exceed 65 "
               "on a 0–100 scale.", "general", "CIRCULAR:CIRC-2026-04#requirements")
    e = doc.el("li", "Rachel Dunmore noted that from 1 April SIU must triage new referrals within 3 business days "
                     "(BR-FRD-035 v2) and asked for weekly referral volumes in the first month.")
    doc.record(e, "triage new referrals within 3 business days",
               "BR-FRD-035 v2 (from 2026-04-01): SIU triage within 3 business days.", "general",
               "RULE:BR-FRD-035@v2#parameters.business_days")
    e = doc.el("li", "Independent validation of the model by Risk is booked for Friday 20 March 2026.")
    doc.record(e, "Independent validation of the model by Risk is booked for Friday 20 March 2026",
               "Independent validation of SNT-4.2 by Risk took place on 2026-03-20.", "general",
               "SYSTEM:SYS03#model_validation")
    doc.el("li", "Linnea Sjöberg confirmed the threshold is a configuration value in fraud-referral-svc and will be "
                 "set for 1 April in line with CLARA.")
    doc.el("li", "Niall Brannigan asked that the calibration pack is filed with the model documentation before go-live.")
    doc.raw("</ul>")
    doc.el("h2", "Actions")
    aid = doc.nid()
    acts = [
        ("Finalise the calibration pack and file it with the model documentation", ol.name, "27 Mar 2026"),
        ("Compliance review of the calibration evidence against §3.3", person("P037", d).name, "27 Mar 2026"),
        ("Set the referral threshold to 65 in fraud-referral-svc for 1 April", person("P042", d).name, "31 Mar 2026"),
        ("Weekly referral volumes to SIU for April", ol.name, "Weekly from 6 Apr 2026"),
    ]
    rows = "".join(f"<tr><td>{i}</td><td>{esc(a)}</td><td>{esc(o)}</td><td>{esc(du)}</td></tr>"
                   for i, (a, o, du) in enumerate(acts, 1))
    doc.raw(f'<table id="{aid}"><thead><tr><th>#</th><th>Action</th><th>Owner</th><th>Due</th></tr></thead>'
            f"<tbody>{rows}</tbody></table>")
    doc.el("p", "Next review: after the first month of referrals at the new threshold.", "note")
    return doc


HTML_DOCS = {"TX073": tx073, "TX074": tx074, "TX075": tx075}
