"""LD026 – Reinsurance Treaty Summary 2026 (reportlab PDF, 2026-01-05, Per Øverland, final).

The exclusive programme terms (retention, limit, reinsurer shares) appear only in the page-3 summary table.
"""
from __future__ import annotations

from . import common as C
from .core import Ctx, Doc, F, PF, Style, W, long_date, short_date, util
from .prose import Prose

FID = "LD026"


def _rsv012(ctx, text: str) -> str:
    """BR-RSV-012 v1 mentions the reserve-engine revaluation run decided in ADR-028 (2026-03-09)."""
    if ctx.date < "2026-03-09":
        text = text.replace("; reserve-engine revaluation runs from Wave 2", "")
    return text


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date)
    tr = W.company["reinsurance_treaty_2026"]
    doc = Doc(ctx, title="Reinsurance Treaty Summary 2026", doc_id="RI-SUM-2026", version="1.0", status="Final",
              subtitle="Excess of loss programme for the 2026 underwriting year – summary for claims and finance staff",
              style=Style(serif=True, accent="0E4D64", accent2="D5E8EE", size=11.6),
              header_left="Corvane Mutual – Reinsurance", header_right="RI-SUM-2026 – Treaty Summary 2026",
              footer_left="Confidential – not for external distribution", classification="Confidential")
    doc.title_page([["Document", "Reinsurance Treaty Summary 2026"], ["Reference", "RI-SUM-2026 v1.0"],
                    ["Status", "Final"], ["Date", long_date(date)], ["Prepared by", ctx.person("P038")],
                    ["Approved by", ctx.person(ctx.holder("the CFO"))],
                    ["Applies to", "All claims with a date of loss in the treaty period"],
                    ["Classification", "Confidential"]])
    doc.toc(depth=1)

    # 1 Summary (page 3) -------------------------------------------------------------------
    ctx.need("ORG:company", "reinsurance_treaty_2026")
    v12, v13 = W.vendors["VEN-12"], W.vendors["VEN-13"]
    s = tr["shares_pct"]
    doc.h(1, "1 Programme at a glance")
    doc.p("The table summarises the 2026 excess of loss programme. The signed treaty wordings prevail over this summary.")
    rows = [["Programme", "2026 excess of loss programme"], ["Type", tr["type"]], ["Period", tr["period"]],
            ["Retention", f"£{tr['retention_gbp_m']:.0f}m each and every loss"],
            ["Limit", f"£{tr['limit_gbp_m']:.0f}m"],
            ["Lead reinsurer", f"{v12['short']} – {s['VEN-12']}% ({v12['name']}, {v12['location']})"],
            ["Reinsurer", f"{v13['short']} – {s['VEN-13']}% ({v13['name']}, {v13['location']})"],
            ["Other market participants", f"{s['other_market']}% in aggregate"],
            ["Large loss notification", tr["large_loss_notification"]],
            ["Treaty administration", f"{ctx.team('T17')} ({ctx.name('P038')})"]]
    doc.table(["Item", "2026 terms"], rows, widths=[4.6, 12.0], caption="2026 programme summary", font_size=9.2,
              facts=[PF(ctx, "ld26_retention", f"{v12['short']} – {s['VEN-12']}%",
                        notes="Page-3 summary table; retention, limit and shares appear only in this table."),
                     F("needle", "2026 XoL retention is £5m each and every loss.", f"£{tr['retention_gbp_m']:.0f}m each and every loss",
                       "ORG:company#reinsurance_treaty_2026.retention_gbp_m", exclusive=True,
                       notes="Same summary table as PL-069."),
                     F("needle", "2026 XoL limit is £150m.", f"£{tr['limit_gbp_m']:.0f}m", "ORG:company#reinsurance_treaty_2026.limit_gbp_m",
                       exclusive=True, notes="Same summary table as PL-069 (row 'Limit')."),
                     F("needle", "Calderbank Re takes a 35% share of the 2026 XoL programme.", f"{v13['short']} – {s['VEN-13']}%",
                       "VENDOR:VEN-13#role", exclusive=True, notes="Same summary table as PL-069.")])
    doc.p("Figures are shown in pounds sterling; Nordic losses are converted under the rates of exchange clause.")

    # 2 Purpose -----------------------------------------------------------------------
    doc.h(1, "2 Purpose and status of this summary", page_break=True)
    doc.p("This summary explains, for claims, reserving and finance staff, how the 2026 reinsurance programme affects "
          "day-to-day work: which claims must be notified, how notifications are made, and how cessions and "
          "bordereaux are produced. It does not replace the treaty wordings, which are held in the contract repository.")
    doc.ps(pr.paras(["ri2", "reinsurance"], 3))
    doc.h(2, "2.1 Audience")
    doc.bullets(["Claims Handlers and team leaders, who must identify potential large losses.",
                 "The Major & Complex Loss team, which handles most claims likely to be ceded.",
                 "The Reserving team, which owns reserve movements and the large loss register reconciliation.",
                 "Financial Control, which accounts for cessions and reinstatement premiums.",
                 "The Reinsurance team, which administers the programme."])
    doc.ps(pr.paras(["ri2"], 1))

    # 3 Structure -------------------------------------------------------------------
    doc.h(1, "3 Programme structure")
    doc.p("The programme provides per-risk and catastrophe excess of loss protection for the whole of the Society's "
          "property and casualty account, including the Nordic branches. Losses are recoverable once the Society's "
          "retention for a single loss or event is exceeded, up to the programme limit shown in section 1.")
    doc.ps(pr.paras(["ri2", "reinsurance"], 3))
    doc.h(2, "3.1 Reinstatements")
    doc.p("Reinstatements are available as set out in the treaty wordings. Reinstatement premiums become payable when a "
          "recovery is made and are accrued by Financial Control when a loss is notified.")
    doc.ps(pr.paras(["ri2"], 2))
    doc.h(2, "3.2 Security")
    doc.p("All participating reinsurers meet the Society's reinsurance security policy. The Risk function monitors "
          "counterparty exposure to each reinsurer and reports it to the Executive Risk Committee.")
    doc.ps(pr.paras(["ri2"], 1))

    # 4 Business covered ------------------------------------------------------------
    doc.h(1, "4 Business covered", page_break=True)
    doc.p("The programme covers all lines of business written by the Society: " + ", ".join(W.company["lines_of_business"]) +
          ". The branches covered are listed below.")
    doc.table(["Branch", "Country", "Currency"],
              [[b["name"], b["country"], b["currency"]] for b in W.company["branches"]] + [["Corvane Mutual (UK)", "UK", "GBP"]],
              widths=[7.0, 4.0, 5.6], caption="Branches covered", font_size=9)
    rows = []
    for p in W.products.values():
        rows.append([p["name"], p["code"], p["line"], p.get("country", "—")])
    doc.table(["Product", "Code", "Line", "Country"], rows, widths=[6.2, 3.2, 4.2, 3.0], caption="Products covered",
              font_size=8.6)
    doc.ps(pr.paras(["ri2", "reinsurance"], 3))
    doc.h(2, "4.1 Perils likely to give rise to recoveries")
    rows = []
    for ct in W.claim_types.values():
        rows.append([ct["name"], ct["id"], ", ".join(ct.get("lines", []) or []) or "—"])
    doc.table(["Claim type", "Code", "Lines"], rows, widths=[6.6, 3.0, 7.0], caption="Claim types", font_size=8.4)
    doc.ps(pr.paras(["ri2"], 2))

    # 5 Notification ----------------------------------------------------------------
    doc.h(1, "5 Large loss notification", page_break=True)
    r11 = ctx.rule("BR-RSV-011")
    doc.p(f"Rule BR-RSV-011 (v{r11['version']}): {r11['text']}",
          facts=[F("needle", "BR-RSV-011 v2: notify Reinsurance (ReCede) within 24 hours of a reserve movement above the £250,000 LLNT.",
                   "within 24 hours of any reserve movement exceeding the Large Loss Notification Threshold", "RULE:BR-RSV-011@v2#text")])
    st = W.steps["PS-RSV-04"]
    doc.kv([["Process step", f"{st['id']} {st['name']}"], ["Description", st["description"]],
            ["Responsible", ", ".join(ctx.team(t) for t in st["raci"]["R"])], ["Accountable", ctx.person(st["raci"]["A"])],
            ["Consulted", ", ".join(ctx.team(t) for t in st["raci"]["C"]) or "—"],
            ["Informed", ", ".join(ctx.team(t) for t in st["raci"]["I"]) or "—"],
            ["System", ctx.sys("SYS07")]], widths=(3.6, 13.0), font_size=9, caption="Large loss notification step")
    doc.ps(pr.paras(["ri2", "reinsurance"], 3))
    doc.h(2, "5.1 How notifications are made")
    doc.bullets(["CLARA identifies reserve movements above the threshold in the daily large loss extract.",
                 "The extract is sent to ReCede, the reinsurance administration system, over the large loss notification interface.",
                 "The Reinsurance team reviews each notification and sends it to the reinsurers with the supporting claim information.",
                 "The notification time is recorded on the claim and in the large loss register.",
                 "Material developments on notified claims are reported to reinsurers as they occur."], numbered=True)
    doc.ps(pr.paras(["ri2"], 2))
    doc.h(2, "5.2 Potential catastrophe events")
    doc.p("Claims handlers must flag claims that may arise from a catastrophe event, such as a storm or flood affecting "
          "many policyholders, so that the Reinsurance team can assess aggregation. Event coding is applied to all "
          "claims arising from the same event.")
    doc.ps(pr.paras(["ri2", "reinsurance"], 3))

    # 6 Cessions and bordereaux -------------------------------------------------------
    doc.h(1, "6 Cessions, bordereaux and accounting", page_break=True)
    rows = []
    for iid in ("CLX-IF-031", "CLX-IF-047", "CLX-IF-048", "CLX-IF-055"):
        i = W.interfaces[iid]
        sch = W.interface_schedule(iid, date) if ctx.ok(f"INTERFACE:{iid}", "schedule") else None
        rows.append([iid, i["name"], ctx.sys(i["source_system"]), ctx.sys(i["target_system"]), i["protocol"], sch or "—"])
    doc.table(["Interface", "Name", "From", "To", "Protocol", "Schedule"], rows, widths=[2.2, 4.4, 2.6, 2.8, 1.6, 3.0],
              caption="Reinsurance interfaces", font_size=8.2)
    doc.p("Ceded reserves are recalculated monthly (BR-RSV-024) and bordereaux are produced from the claims data and "
          "checked by Financial Control before release to reinsurers through the Bordereaux Exchange.")
    doc.ps(pr.paras(["ri2", "reinsurance"], 3))
    doc.h(2, "6.1 Effect of the Claims Hub migration")
    doc.p("As claims migrate to Claims Hub, reserve movements reach ReCede from both platforms. The reserve movement "
          "Kafka bridge (CLX-IF-049), live since 12 December 2025, makes CLARA movements available to Claims Hub during "
          "the transition. The Reinsurance team reconciles notifications from both sources until CLARA is decommissioned.")
    doc.ps(pr.paras(["ri2", "migration"], 2))

    # 7 Currency ----------------------------------------------------------------------
    doc.h(1, "7 Currency")
    r12 = ctx.rule("BR-RSV-012")
    if r12 and ctx.ok(f"RULE:BR-RSV-012@v{r12['version']}", "text"):
        doc.p(f"Nordic reserves are held in local currency (BR-RSV-012 v{r12['version']}): {_rsv012(ctx, r12['text'])}")
    doc.p("Amounts are stored in both the original currency and GBP (ADR-016). For reinsurance purposes losses are "
          "converted at the rates set out in the treaty wordings.")
    doc.ps(pr.paras(["ri2"], 2))

    # 8 Exclusions --------------------------------------------------------------------
    doc.h(1, "8 Principal exclusions and conditions", page_break=True)
    doc.p("The exclusions below are summarised for orientation only. The treaty wordings set out the exclusions in full.")
    doc.bullets(["War, terrorism and related risks, except as provided in the wordings.",
                 "Nuclear, radioactive and pollution risks, in line with standard market clauses.",
                 "Business not written under the Society's approved underwriting authorities.",
                 "Liabilities assumed under contract beyond those in the underlying policies.",
                 "Losses excluded by the underlying policy wordings."])
    doc.ps(pr.paras(["ri2"], 2))
    doc.h(2, "8.1 Claims conditions")
    doc.bullets(["Prompt notification of losses likely to involve the programme.",
                 "Co-operation with reinsurers on large and complex losses.",
                 "Access for reinsurers to claim files on reasonable notice.",
                 "Consultation with the lead reinsurer before settling a loss that will exhaust the retention."])
    doc.ps(pr.paras(["ri2", "reinsurance"], 3))

    # 9 Responsibilities --------------------------------------------------------------
    doc.h(1, "9 Responsibilities")
    rows = [["Identify potential large losses", ctx.team("T02"), ctx.person(W.owner_of_process("S4", date))],
            ["Set and maintain reserves", ctx.team("T09"), ctx.person(W.owner_of_process("S4", date))],
            ["Notify reinsurers", ctx.team("T17"), ctx.person("P038")],
            ["Maintain the large loss register", ctx.team("T17"), ctx.person("P038")],
            ["Account for cessions and reinstatement premiums", ctx.team("T14"), ctx.person("P021")],
            ["Monitor reinsurer security", "Risk function", ctx.person("P007")],
            ["Approve the programme", "Executive Committee", ctx.person(ctx.holder("the CFO"))]]
    doc.table(["Activity", "Responsible", "Accountable"], rows, widths=[6.2, 4.6, 5.8], caption="Responsibilities",
              font_size=8.8)
    doc.ps(pr.paras(["ri2"], 2))

    # 10 Contacts ---------------------------------------------------------------------
    doc.h(1, "10 Contacts")
    rows = [[ctx.name(p), ctx.title(p), ctx.team(W.team_of(p, date))] for p in ("P038", "P009", "P030", "P021", "P007")]
    doc.table(["Name", "Title", "Team"], rows, widths=[4.6, 6.4, 5.6], font_size=9)
    doc.ps(pr.paras(["ri2"], 1))

    # 11 Data requirements -------------------------------------------------------------
    doc.h(1, "11 Information required for notification", page_break=True)
    doc.p("Notifications and bordereaux depend on complete and accurate claim data. The table lists the information "
          "the Reinsurance team needs for each notified claim and where it comes from.")
    doc.table(["Item", "Source", "Notes"],
              [["Claim reference", "CLARA / Claims Hub", "Both platforms during the migration"],
               ["Policy and product", "PALM via the claims platform", "Product code determines the treaty section"],
               ["Date and cause of loss", "Claim record", "Drives allocation to the treaty period and aggregation"],
               ["Location of loss", "Claim record", "Needed for catastrophe aggregation"],
               ["Event code", "Claim record", "Applied by the claims team for catastrophe events"],
               ["Currency and amounts", "Reserve and payment records", "Original currency and GBP"],
               ["Reserve history", "Reserve movement history", "Shows how the estimate developed"],
               ["Recoveries", "Recovery records", "Salvage and subrogation reduce the net loss"],
               ["Handler and reviewer", "Claim record", "Contact for reinsurer queries"]],
              widths=[4.0, 5.2, 7.4], caption="Notification data", font_size=8.8)
    doc.ps(pr.paras(["ri2", "data"], 3))

    # 12 Administration calendar -------------------------------------------------------
    doc.h(1, "12 Treaty administration")
    doc.table(["Activity", "Frequency", "Team"],
              [["Large loss notifications", "As they occur", ctx.team("T17")],
               ["Large loss register reconciliation", "Monthly", f"{ctx.team('T17')} / {ctx.team('T12')}"],
               ["Claims bordereaux", "Monthly", ctx.team("T17")],
               ["Ceded reserve recalculation", "Monthly", ctx.team("T14")],
               ["Treaty accounts", "Quarterly", ctx.team("T14")],
               ["Recovery collection", "As recoveries fall due", ctx.team("T17")],
               ["Renewal preparation", "Annually", ctx.team("T17")]],
              widths=[6.4, 4.6, 5.6], caption="Administration activities", font_size=9)
    doc.ps(pr.paras(["ri2", "reinsurance"], 3))
    doc.h(2, "12.1 Queries and disputes")
    doc.ps(pr.paras(["ri2"], 2))
    doc.h(2, "12.2 Records")
    doc.ps(pr.paras(["ri2", "governance"], 2))

    # 13 Reserving interaction -------------------------------------------------------
    doc.h(1, "13 Interaction with reserving", page_break=True)
    doc.p(f"Gross case reserves are set by the claims teams within their authority and reviewed under the reserving "
          f"rules. The Reserving team, led by {ctx.person('P009')}, owns the reserve process and reports to the "
          f"Reserving Committee. Net reserves are derived from gross reserves using the programme terms.")
    rows = []
    for rid in ("BR-RSV-003", "BR-RSV-011", "BR-RSV-012", "BR-RSV-016", "BR-RSV-019", "BR-RSV-024"):
        v = ctx.rule(rid)
        if not v or not ctx.ok(f"RULE:{rid}@v{v['version']}", "text"):
            continue
        rows.append([f"{rid} v{v['version']}", W.rules[rid]["title"], _rsv012(ctx, v["text"])])
    doc.table(["Rule", "Title", "Text"], rows, widths=[2.8, 4.4, 9.4], caption="Reserving rules relevant to reinsurance",
              font_size=8.2)
    doc.ps(pr.paras(["ri2", "reinsurance"], 3))

    # 14 Systems --------------------------------------------------------------------
    doc.h(1, "14 Systems")
    C.systems_table(ctx, doc, ["SYS01", "SYS02", "SYS07", "SYS26", "SYS06", "SYS11", "SYS21"], "Systems used for reinsurance")
    doc.ps(pr.paras(["ri2", "integration"], 3))

    # Appendices ----------------------------------------------------------------------
    doc.h(1, "Appendix A – Large loss checklist for claims handlers", page_break=True)
    doc.table(["#", "Check"], [[str(i), c] for i, c in enumerate([
        "Is the reserve movement above the Large Loss Notification Threshold?",
        "Has the claim been flagged as a potential catastrophe event?",
        "Is the claim in a Nordic branch? If so, confirm the currency and the GBP equivalent.",
        "Are the cause of loss, date of loss and location recorded accurately?",
        "Has the Major & Complex Loss team been informed?",
        "Has the reserve rationale been recorded on the claim?",
        "Has the notification been confirmed by the Reinsurance team?",
        "Have material developments since the notification been reported?"], 1)], widths=[1.0, 15.6], font_size=9)
    doc.ps(pr.paras(["ri2"], 2))
    doc.h(1, "Appendix B – Large loss register", page_break=True)
    doc.p("The large loss register is maintained by the Reinsurance team. Each notified claim has one entry, updated "
          "whenever the claim develops materially.")
    doc.table(["Field", "Content"],
              [["Register reference", "Sequential reference assigned by the Reinsurance team"],
               ["Claim reference", "CLARA or Claims Hub claim reference"],
               ["Branch and product", "As recorded on the claim"],
               ["Date and cause of loss", "As recorded on the claim"],
               ["Event code", "Catastrophe event code, if any"],
               ["Gross incurred", "Paid plus outstanding reserve, in original currency and GBP"],
               ["Notification date and time", "When the notification was sent to reinsurers"],
               ["Reinsurer acknowledgements", "Date each reinsurer acknowledged the notification"],
               ["Recoveries", "Amounts invoiced and received"],
               ["Status", "Open, closed or disputed"],
               ["Notes", "Significant developments and correspondence"]],
              widths=[4.6, 12.0], caption="Register fields", font_size=8.8)
    doc.ps(pr.paras(["ri2", "reinsurance"], 3))
    doc.h(1, "Appendix C – Reserve movement record")
    doc.p("Cessions and large loss notifications are derived from reserve movements. The CLARA reserve movement record "
          "is shown below for reference.")
    cb = W.copybooks["RSVMVT01"]
    doc.table(["Level", "Field", "PIC"], [[str(f["level"]).zfill(2), f["name"], f.get("pic") or "group"] for f in cb.get("fields", [])],
              widths=[1.6, 8.0, 7.0], font_size=8.4, caption="RSVMVT01")
    doc.ps(pr.paras(["ri2", "data"], 2))
    doc.h(1, "Appendix D – Glossary", page_break=True)
    doc.table(["Term", "Meaning"],
              [["Excess of loss", "Reinsurance that pays the part of a loss above the retention, up to the limit."],
               ["Retention", "The amount of each loss the Society bears before the reinsurance responds."],
               ["Reinstatement", "Restoration of the limit after a loss, usually for an additional premium."],
               ["Cession", "The part of a loss or reserve passed to reinsurers."],
               ["Hours clause", "The treaty clause that defines how losses are grouped into a single event."]]
              + [[t, ctx.a(m)] for t, m in C.glossary_terms(["G-015", "G-017", "G-016"])],
              widths=[3.6, 13.0], font_size=8.8)
    return doc


def post_check(doc, texts):
    from harness import extract as X
    pages = [i + 1 for i, t in enumerate(texts) if X.match("Brynholt", t) or X.match("£150m", t) or X.match("Calderbank", t)]
    out = [f"INFO treaty terms on pages {pages}; total {len(texts)}"]
    if pages != [3]:
        out.append(f"exclusive treaty terms on pages {pages}, want [3]")
    return out
