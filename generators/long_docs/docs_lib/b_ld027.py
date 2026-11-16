"""LD027 – Sentinel Model Independent Validation Report (DOCX -> PDF via LibreOffice, 2026-03-20, Karin Holmberg).

The population stability index (PL-070, exclusive) is stated only in the executive summary. The model's AUC belongs to
LD020 and is never stated here.
"""
from __future__ import annotations

from . import common as C
from . import figures as FG
from .core import CACHE, Ctx, Doc, F, PF, Style, W, long_date, short_date, util
from .prose import Prose

FID = "LD027"

FINDINGS = [
    # ref, title, rating, observation, recommendation, owner
    ("VF-01", "Feature documentation", "Low",
     "The model documentation describes the input groups but does not define every derived feature used by the vendor "
     "engine in terms that a reviewer outside the vendor can reproduce.",
     "Obtain a complete feature dictionary from the vendor and hold it with the model documentation.", "P027"),
    ("VF-02", "Monitoring triggers", "Medium",
     "Monitoring measures are produced monthly, but the trigger levels that require escalation are not yet formally "
     "approved by the Claims Fraud Forum.",
     "Approve trigger levels for each monitoring measure and record breaches in the model inventory.", "P008"),
    ("VF-03", "Threshold implementation across scoring paths", "Medium",
     "The validator confirmed that the new threshold is configured as an effective-dated parameter for the online path "
     "and in Claims Hub. Documentation did not show how each batch path obtains the threshold.",
     "Before 1 April 2026, test every scoring and referral path (online, batch and Claims Hub) with claims scored just "
     "below and just above the new threshold, and retain the evidence.", "P016"),
    ("VF-04", "Fairness analysis", "Low",
     "Fairness testing compared referral rates between regions and product lines. Analysis by other customer "
     "characteristics was limited by the data available to the validator.",
     "Extend the quarterly fairness review to the additional characteristics agreed with Compliance.", "P037"),
    ("VF-05", "Outcome label lag", "Low",
     "Investigation outcomes take time to mature, so recent cohorts are under-represented in outcome analysis.",
     "Report outcome-based measures on matured cohorts and show early indicators separately.", "P027"),
]


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date)
    snt = W.systems["SYS03"]
    ven = W.vendors[snt["vendor"]]
    val = snt["model_validation"]
    doc = Doc(ctx, title="Sentinel Model Independent Validation Report", doc_id="RSK-MVR-2026-01", version="1.0",
              status="Final", subtitle=f"Independent validation of fraud scoring model {snt['model_version']}",
              style=Style(font="Cambria", heading_font="Cambria", accent="4A235A", accent2="E8DAEF", size=11.5),
              header_left="Risk – Model Validation", header_right="RSK-MVR-2026-01 – Sentinel SNT-4.2",
              footer_left="Confidential – Model Risk", classification="Confidential")
    doc.title_page(C.control_rows(ctx, doc, extra=[["Model", f"Sentinel {snt['model_version']}"],
                                                    ["Model owner", ctx.person("P027")],
                                                    ["Accountable executive", ctx.person("P008")],
                                                    ["Validation date", long_date(val["date"])]]))
    C.distribution(ctx, doc, [ctx.person("P008"), ctx.person("P027"), ctx.person("P005"), ctx.person("P037"),
                              "Claims Fraud Forum", "Executive Risk Committee"])
    doc.toc(depth=2)

    # 1 Executive summary -------------------------------------------------------------------
    doc.h(1, "1 Executive summary")
    ctx.need("SYSTEM:SYS03", "model_psi")
    doc.p(f"The Risk function has completed its independent validation of the Sentinel fraud scoring model "
          f"{snt['model_version']}, recalibrated on {long_date(snt['model_calibrated'])}, and of its use with the referral "
          f"threshold of 65 that applies from {long_date('2026-04-01')} under NISA Circular 2026/04.")
    doc.p(f"Independent validation ({long_date(val['date'])}) found {snt['model_version']} stable, with a population "
          f"stability index of {snt['model_psi']} between the calibration sample and recent scored claims.",
          facts=[PF(ctx, "ld27_psi", f"population stability index of {snt['model_psi']}", notes="Executive summary.")])
    doc.p("The validator's opinion is that the model is fit for its approved purpose, prioritising claims for referral "
          "to Counter-Fraud & SIU, subject to the findings below. Recalibration is due annually.",
          facts=[F("general", "The validation result for SNT-4.2: stable; recalibration due annually.",
                   "Recalibration is due annually", "SYSTEM:SYS03#model_validation")])
    doc.table(["Ref", "Finding", "Rating", "Owner"], [[r, t, g, ctx.name(o)] for r, t, g, _, _, o in FINDINGS],
              widths=[1.8, 9.0, 2.2, 3.6], caption="Summary of findings", font_size=9)
    doc.ps(pr.paras(["valid"], 1))

    # 2 Scope ---------------------------------------------------------------------------
    doc.h(1, "2 Scope and approach", page_break=True)
    doc.p(f"The validation covered the recalibrated model {snt['model_version']}, its implementation in CLARA and Claims "
          f"Hub, and the proposed referral threshold approved by the Claims Fraud Forum on {long_date('2026-03-12')}. "
          f"It was requested by the accountable executive, {ctx.person('P008')}, under the corporate model risk policy.")
    doc.ps(pr.paras(["valid"], 3, n=(4, 6)))
    doc.h(2, "2.1 Independence")
    doc.p("The validation team has no role in the development, calibration or operation of the model and reports to "
          "the Chief Risk Officer.")
    doc.ps(pr.paras(["valid", "model2"], 1, n=(3, 5)))
    doc.h(2, "2.2 Work performed")
    doc.table(["Area", "Work performed"],
              [["Documentation", "Review of model documentation, calibration evidence pack and vendor technical material"],
               ["Conceptual soundness", "Assessment of features against known fraud indicators and the referral process"],
               ["Data", "Lineage tracing from the claims platforms to the scoring engine; completeness reconciliation"],
               ["Performance", "Replication of discrimination and outcome measures on the calibration and recent samples"],
               ["Stability", "Comparison of score and input distributions between the calibration sample and recent claims"],
               ["Threshold", "Review of the proposed threshold, its calibration and its compliance with the Circular"],
               ["Implementation", "Replication of a sample of scores; review of threshold configuration in each platform"],
               ["Fairness", "Comparison of referral rates between regions and product lines"],
               ["Governance", "Review of roles, monitoring, change control and the model inventory"]],
              widths=[3.6, 13.0], caption="Validation work", font_size=8.8)
    doc.ps(pr.paras(["valid"], 2, n=(4, 6)))
    doc.h(2, "2.3 Limitations of the review")
    doc.ps(pr.paras(["valid", "model2"], 2, n=(3, 5)))

    # 3 Model description -------------------------------------------------------------
    doc.h(1, "3 Model description", page_break=True)
    doc.kv([["Model", f"Sentinel fraud score {snt['model_version']}"], ["Engine", snt["tech"]],
            ["Vendor", f"{ven['name']}, {ven['location']}"], ["Business owner", ctx.person(snt["owner"])],
            ["Model owner", ctx.person("P027")], ["Last calibration", long_date(snt["model_calibrated"])],
            ["Purpose", "Prioritise new claims for referral to Counter-Fraud & SIU"],
            ["Prohibited uses", "Declining, reducing or repudiating a claim on the score alone"]],
           widths=(4.0, 12.6), font_size=9, caption="Model summary")
    doc.ps(pr.paras(["model2", "model"], 3, n=(4, 6)))
    doc.h(2, "3.1 Use in the claims process")
    rows = []
    for sid in ("PS-TRI-01", "PS-FRD-01", "PS-FRD-02"):
        st = W.steps[sid]
        rows.append([sid, st["name"], st["description"]])
    doc.table(["Step", "Name", "Description"], rows, widths=[2.4, 4.0, 10.2], font_size=8.8)
    doc.ps(pr.paras(["model2"], 2, n=(4, 6)))

    # 4 Conceptual soundness ----------------------------------------------------------
    doc.h(1, "4 Conceptual soundness", page_break=True)
    doc.ps(pr.paras(["valid", "model2"], 3, n=(4, 6)))
    rows = []
    for rid, r in W.rules.items():
        if not rid.startswith("BR-FRD-0") or int(rid[-3:]) > 16 or rid == "BR-FRD-012":
            continue
        v = ctx.rule(rid)
        if not v:
            continue
        rows.append([rid, r["title"], "Represented in model inputs"])
    doc.table(["Indicator rule", "Title", "Assessment"], rows, widths=[2.6, 8.6, 5.4],
              caption="Fraud indicators and their representation in the model", font_size=8.6)
    doc.ps(pr.paras(["valid"], 2, n=(4, 6)))

    # 5 Data ------------------------------------------------------------------------
    doc.h(1, "5 Data", page_break=True)
    rows = []
    for iid in ("CLX-IF-003", "CLX-IF-004", "CLX-IF-008", "CLX-IF-009", "CLX-IF-010", "CLX-IF-012", "CLX-IF-036"):
        i = W.interfaces[iid]
        rows.append([iid, i["name"], f"{ctx.sys(i['source_system'])} → {ctx.sys(i['target_system'])}", i["protocol"]])
    doc.table(["Interface", "Name", "Flow", "Protocol"], rows, widths=[2.4, 6.2, 5.8, 2.2], caption="Data flows reviewed",
              font_size=8.6)
    doc.ps(pr.paras(["valid", "data"], 3, n=(4, 6)))
    doc.h(2, "5.1 Data quality tests")
    rows = []
    descs = {c["name"]: c.get("description", "") for c in W.tables["CLR.T_CLAIM"]["columns"]}
    for col in ("CLAIM_ID", "PRODUCT_CD", "PERIL_CD", "LOSS_DT", "NOTIFIED_TS", "CHANNEL_CD", "TIER_CD", "REGION_CD",
                "CURRENCY_CD", "FRAUD_FLAG", "LOSS_POSTCODE"):
        rows.append([f"CLR.T_CLAIM.{col}", ctx.a(descs.get(col, "")), "Completeness and validity", "Satisfactory"])
    for c in W.tables["triage.triage_decision"]["columns"]:
        rows.append([f"triage.triage_decision.{c['name']}", ctx.a(c.get("description", "")), "Completeness; agreement with CLARA where both exist", "Satisfactory"])
    doc.table(["Field", "Description", "Test", "Result"], rows, widths=[5.4, 5.2, 3.8, 2.2], caption="Input data tests",
              font_size=8.0)
    doc.ps(pr.paras(["valid", "data"], 2, n=(4, 6)))
    fin = W.company["financials"]["fy2025"]
    doc.h(2, "5.2 Outcome data")
    doc.p(f"Outcome labels come from SIU investigations recorded in the SIU Case Manager. In 2025 Counter-Fraud & SIU "
          f"received {fin['fraud_referrals']:,} referrals and confirmed {fin['confirmed_fraud_cases']:,} cases of fraud.",
          facts=[F("general", "FY2025: 4,812 referrals and 1,109 confirmed fraud cases.", f"confirmed {fin['confirmed_fraud_cases']:,} cases of fraud",
                   "ORG:company#financials.fy2025.confirmed_fraud_cases")])
    doc.ps(pr.paras(["valid", "model2"], 2, n=(4, 6)))

    # 6 Performance -----------------------------------------------------------------
    doc.h(1, "6 Performance", page_break=True)
    doc.p("The validator replicated the model owner's discrimination and outcome measures on the calibration sample and "
          "on recent scored claims. The replicated results agree with those reported in the calibration evidence pack, "
          "and performance on recent claims is consistent with performance on the calibration sample.")
    doc.ps(pr.paras(["valid", "model2"], 3, n=(4, 6)))
    doc.h(2, "6.1 Outcome analysis")
    doc.p("Confirmed-fraud outcomes are concentrated in the highest score bands, and the share of confirmed fraud falls "
          "steadily as the score decreases. No score band shows an outcome pattern inconsistent with the ranking.")
    doc.ps(pr.paras(["valid"], 2, n=(4, 6)))

    # 7 Stability -------------------------------------------------------------------
    doc.h(1, "7 Stability", page_break=True)
    doc.p("Stability was assessed by comparing the distribution of scores, and of the main inputs, between the "
          "calibration sample and claims scored in the most recent period. Input distributions were compared by region, "
          "channel and claim type. The results support the conclusion in the executive summary that the model is stable.")
    doc.ps(pr.paras(["valid", "model2"], 3, n=(4, 6)))
    doc.h(2, "7.1 Effect of the migration to Claims Hub")
    doc.p("Claims notified through digital channels have been scored by Claims Hub since the MVP release on "
          f"{long_date('2025-11-03')}. The validator compared scores for similar claims from the two platforms and found "
          "no systematic difference attributable to the platform.")
    doc.ps(pr.paras(["valid"], 2, n=(4, 6)))

    # 8 Threshold -------------------------------------------------------------------
    doc.h(1, "8 Threshold and calibration", page_break=True)
    r12 = W.rule_version("BR-FRD-012", date)
    r31 = W.rules["BR-FRD-031"]["versions"][0]
    circ = W.circulars["CIRC-2026-04"]
    p33 = next(r["text"] for r in circ["requirements"] if str(r["para"]) == "3.3")
    doc.p(f"At the date of this report the referral threshold is {r12['parameters']['threshold']} (BR-FRD-012 "
          f"v{r12['version']}). From {long_date(r31['effective_from'])} it will be {r31['parameters']['threshold']} for all "
          f"tiers (BR-FRD-031 v1, approved on {long_date(r31['approved_on'])}). Circular 2026/04 §3.3 requires: {p33}",
          facts=[F("temporal", "On 2026-03-20 the threshold is still 70 (BR-FRD-012 v2); 65 applies from 2026-04-01 (BR-FRD-031 v1).",
                   f"the referral threshold is {r12['parameters']['threshold']} (BR-FRD-012 v{r12['version']})", "RULE:BR-FRD-012@v2")])
    doc.p("The validator reviewed the calibration evidence for the new threshold and confirmed that it is documented, "
          "that it does not exceed the maximum set by the Circular, and that the expected change in referral volumes "
          "has been shared with Counter-Fraud & SIU for capacity planning.")
    doc.ps(pr.paras(["valid", "model2"], 3, n=(4, 6)))

    # 9 Implementation -------------------------------------------------------------
    doc.h(1, "9 Implementation testing", page_break=True)
    rows = []
    for r in W.tables["CLR.T_PARAM"]["param_rows"]:
        if r["key"] != "FRD_REFER_THRESH" or not ctx.ok("TABLE:CLR.T_PARAM", f"param_rows:{r['key']}"):
            continue
        rows.append([r["key"], r["value"], short_date(r["valid_from"]), short_date(r["valid_to"]) if r["valid_to"] else "—",
                     r["rule"].replace("@v", " v")])
    doc.table(["Parameter", "Value", "Valid from", "Valid to", "Rule"], rows, widths=[4.2, 1.8, 3.0, 3.0, 4.6],
              caption="CLARA threshold parameter rows inspected", font_size=8.8)
    doc.p("A sample of scores was recomputed from the raw inputs using the vendor's reference implementation; all "
          "recomputed scores matched production. Threshold configuration was inspected in CLARA and in Claims Hub; see "
          "finding VF-03 on the batch paths.")
    doc.ps(pr.paras(["valid"], 3, n=(4, 6)))

    # 10 Fairness -----------------------------------------------------------------
    doc.h(1, "10 Fairness and explainability", page_break=True)
    doc.ps(pr.paras(["valid", "model2"], 3, n=(4, 6)))
    r33 = ctx.rule("BR-FRD-033")
    if r33 and ctx.ok(f"RULE:BR-FRD-033@v{r33['version']}", "text"):
        doc.p(f"BR-FRD-033 (v{r33['version']}) applies from {long_date(r33['effective_from'])}: {r33['text']}")

    # 11 Governance --------------------------------------------------------------
    doc.h(1, "11 Governance and monitoring", page_break=True)
    com = W.committees["COM-02"]
    doc.p(f"The {com['name']}, chaired by {ctx.person('P008')}, approves material model changes and receives monitoring "
          f"reports. The model owner, {ctx.person('P027')}, produces the monitoring reports.")
    doc.ps(pr.paras(["valid", "model2", "governance"], 3, n=(4, 6)))
    fig = FG.box_diagram(CACHE / "fig" / FID / "lines.png", title="Lines of defence for the Sentinel model",
                         boxes=[{"id": "l1", "label": f"First line\nModel owner ({ctx.name('P027')})\nCounter-Fraud & SIU", "x": 60, "y": 180, "w": 560, "h": 220},
                                {"id": "l2", "label": "Second line\nRisk function – model validation\nCompliance", "x": 720, "y": 180, "w": 560, "h": 220, "color": "purple"},
                                {"id": "l3", "label": "Third line\nInternal Audit", "x": 1380, "y": 180, "w": 560, "h": 220, "color": "grey"},
                                {"id": "f", "label": "Claims Fraud Forum", "x": 60, "y": 560, "w": 560, "h": 150, "color": "green"},
                                {"id": "c", "label": "Chief Risk Officer", "x": 720, "y": 560, "w": 560, "h": 150, "color": "purple"}],
                         arrows=[{"src": "l1", "dst": "f", "label": "monitoring reports"},
                                 {"src": "l2", "dst": "c", "label": "validation opinion"},
                                 {"src": "l1", "dst": "l2", "label": "evidence pack"}],
                         size=(2000, 780))
    doc.figure(fig, "Lines of defence for the Sentinel model",
               alt="Lines of defence: the model owner in Counter-Fraud & SIU (first line) sends an evidence pack to the Risk function (second line), which gives its validation opinion to the CRO.",
               facts=[F("image_text", "Figure: the Risk function (second line) gives the validation opinion to the CRO.",
                        "validation opinion", "SYSTEM:SYS03#model_validation", where="image")])

    # 12 Process controls --------------------------------------------------------
    doc.h(1, "12 Referral process controls", page_break=True)
    doc.p("Because the model's risk depends on how the score is used, the validator reviewed the controls in the "
          "process steps that use the score.")
    for sid in ("PS-TRI-01", "PS-TRI-03", "PS-FRD-01", "PS-FRD-02", "PS-FRD-04"):
        st = W.steps[sid]
        rules = []
        for rid in st.get("rules", []):
            v = ctx.rule(rid) or (ctx.rule("BR-FRD-012") if rid == "BR-FRD-031" else None)
            if v:
                lab = f"{'BR-FRD-012' if rid == 'BR-FRD-031' else rid} v{v['version']}"
                if lab not in rules:
                    rules.append(lab)
        doc.h(2, f"{sid} {st['name']}")
        doc.kv([["Description", st["description"]], ["Accountable", ctx.person(st["raci"]["A"])],
                ["Responsible", ", ".join(ctx.team(t) for t in st["raci"]["R"])],
                ["Rules in force", ", ".join(rules) or "—"], ["Validator's assessment", "Controls adequately designed"]],
               widths=(3.8, 12.8), font_size=9)
        doc.p(pr.para(["valid", "model2"], n=(3, 5)))

    # 13 Vendor --------------------------------------------------------------------
    doc.h(1, "13 Vendor oversight", page_break=True)
    doc.p(f"The scoring engine is licensed from {ven['name']} ({ven['location']}). The vendor supplied technical "
          f"documentation, the calibration tooling and a reference implementation used for score replication. The "
          f"validator did not rely on the vendor's own validation work.")
    doc.ps(pr.paras(["valid", "vendor"], 2, n=(4, 6)))

    # 14 Sensitivity ---------------------------------------------------------------
    doc.h(1, "14 Sensitivity testing", page_break=True)
    doc.table(["Input group", "Test", "Observation"],
              [["Claim facts", "Vary time to notify and channel", "Score responds in the expected direction"],
               ["Policy facts", "Vary time since inception and recent cover changes", "Score responds in the expected direction"],
               ["Party facts", "Add prior claims and shared identifiers", "Largest effect of any input group, as expected"],
               ["Evidence facts", "Introduce photo metadata inconsistencies", "Moderate effect; consistent with the indicator rules"],
               ["Missing inputs", "Remove each input group in turn", "Score degrades gracefully; behaviour documented"]],
              widths=[3.4, 6.2, 7.0], caption="Sensitivity tests", font_size=8.8)
    doc.ps(pr.paras(["valid"], 3, n=(4, 6)))

    # 15 Documentation review ------------------------------------------------------
    doc.h(1, "15 Documentation review", page_break=True)
    doc.table(["Document", "Version reviewed", "Assessment"],
              [["Sentinel Model Governance and Calibration", "v2.3 (draft for v3.0)", "Generally clear; see VF-01 and VF-02"],
               ["Calibration evidence pack", short_date(snt["model_calibrated"]), "Complete"],
               ["Vendor technical documentation", f"{snt['model_version']}", "Adequate for validation; see VF-01"],
               ["Monitoring reports", "Last three reports", "Clear; triggers not yet approved (VF-02)"],
               ["Model inventory entry", "Current", "Accurate"]],
              widths=[6.4, 4.2, 6.0], caption="Documents reviewed", font_size=8.8)
    doc.ps(pr.paras(["valid", "model2"], 3, n=(4, 6)))
    doc.h(2, "15.1 Interviews")
    doc.table(["Name", "Title"], [[ctx.name(p_), ctx.title(p_)] for p_ in ("P008", "P027", "P028", "P036", "P037", "P042", "P016")],
              widths=[5.0, 11.6], font_size=9)

    # 16 Findings ---------------------------------------------------------------
    doc.h(1, "16 Findings and management responses", page_break=True)
    for ref, title, rating, obs, rec, owner in FINDINGS:
        doc.h(2, f"{ref} {title} ({rating})")
        doc.kv([["Observation", obs], ["Recommendation", rec], ["Owner", ctx.person(owner)],
                ["Management response", "Accepted. Action to be completed within three months of this report."]],
               widths=(3.8, 12.8), font_size=9)
        doc.p(pr.para(["valid", "finding"], n=(4, 6)))
        doc.p(pr.para(["valid", "model2"], n=(3, 5)))
    doc.h(2, "Rating definitions")
    doc.table(["Rating", "Meaning"], [["High", "Model should not be used until resolved"],
                                     ["Medium", "Resolve within the agreed timeframe; use may continue"],
                                     ["Low", "Improvement; resolve at the next scheduled change"]],
              widths=[3.0, 13.6], font_size=9)

    # Appendices --------------------------------------------------------------
    doc.h(1, "Appendix A – Tests performed", page_break=True)
    tests = ["Documentation completeness review", "Feature-to-indicator mapping", "Lineage trace for a sample of claims",
             "Completeness reconciliation of scored claims to scoring logs", "Replication of discrimination measures",
             "Outcome analysis by score band", "Score distribution comparison", "Input distribution comparison by region",
             "Input distribution comparison by channel", "Threshold calibration review", "Circular §3.3 compliance check",
             "Score replication from raw inputs", "Threshold configuration inspection – CLARA", "Threshold configuration inspection – Claims Hub",
             "Fairness comparison by region", "Fairness comparison by product line", "Monitoring report review",
             "Change log and inventory review"]
    doc.table(["#", "Test", "Result"], [[str(i), t, "See finding VF-03" if "CLARA" in t else ("See finding VF-04" if "Fairness" in t else "Satisfactory")]
                                        for i, t in enumerate(tests, 1)], widths=[1.0, 11.0, 4.6], font_size=8.8)
    doc.ps(pr.paras(["valid"], 2, n=(4, 6)))
    doc.h(2, "A.1 Test detail")
    for i, t in enumerate(tests, 1):
        res = "See finding VF-03" if "CLARA" in t else ("See finding VF-04" if "Fairness" in t else "Satisfactory")
        doc.h(3, f"Test {i}: {t}")
        doc.kv([["Objective", f"Confirm that the {t.lower()} supports the validation opinion."],
                ["Result", res]], widths=(3.0, 13.6), font_size=8.8)
        doc.p(pr.para(["valid", "model2"], n=(3, 5)))
    doc.h(1, "Appendix B – Fraud rules relevant to the model", page_break=True)
    rows = []
    for rid in ("BR-TRI-007", "BR-FRD-012", "BR-FRD-031", "BR-FRD-033", "BR-FRD-035"):
        r = W.rules[rid]
        v = ctx.rule(rid) or (r["versions"][0] if rid in ("BR-FRD-031", "BR-FRD-033") else None)
        if not v or not ctx.ok(f"RULE:{rid}@v{v['version']}", "text"):
            continue
        rows.append([f"{rid} v{v['version']}", r["title"], v["text"], short_date(v["effective_from"]) if v.get("effective_from") else "—"])
    doc.table(["Rule", "Title", "Text", "Effective"], rows, widths=[2.8, 4.0, 7.4, 2.4], font_size=8.4)
    doc.h(1, "Appendix C – Glossary")
    doc.table(["Term", "Meaning"],
              [["Population stability index", "A measure of the shift between two distributions, computed over score bands."],
               ["Discrimination", "The ability of a score to rank claims with confirmed fraud above genuine claims."],
               ["Matured cohort", "Claims whose investigation outcomes are substantially complete."]]
              + [[t, ctx.a(m)] for t, m in C.glossary_terms(["G-002", "G-009", "G-012"])],
              widths=[4.0, 12.6], font_size=8.8)
    return doc


def post_check(doc, texts):
    from harness import extract as X
    out = []
    psi = [i + 1 for i, t in enumerate(texts) if X.match("0.06", t)]
    auc = [i + 1 for i, t in enumerate(texts) if X.match("0.87", t) or X.match("AUC", t)]
    if auc:
        out.append(f"AUC (LD020-exclusive) appears on pages {auc}")
    out.append(f"INFO PSI value pages {psi}; total {len(texts)}")
    return out
