"""LD020 – Sentinel Model Governance and Calibration (DOCX, 2026-05-20, Oskar Lindgren, approved)."""
from __future__ import annotations

from . import common as C
from . import hub as H
from . import figures as FG
from .core import CACHE, Ctx, Doc, F, PF, Style, W, gbp, long_date, short_date, util
from .prose import Prose

FID = "LD020"


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date)
    snt = W.systems["SYS03"]
    ven = W.vendors[snt["vendor"]]
    doc = Doc(ctx, title="Sentinel Model Governance and Calibration", doc_id="CFR-MDL-002", version="3.0",
              status="Approved", subtitle=f"Fraud scoring model {snt['model_version']}: governance, calibration and monitoring",
              style=Style(font="Calibri", heading_font="Calibri", accent="3F3151", accent2="E4DFEC", size=11),
              header_left="Counter-Fraud & SIU – Sentinel Model Governance and Calibration",
              header_right="CFR-MDL-002 v3.0", classification="Confidential", footer_left="Classification: Confidential")
    doc.title_page(C.control_rows(ctx, doc, owner="P008", extra=[["Model", f"Sentinel {snt['model_version']}"],
                                                                  ["Model owner", ctx.person("P027")],
                                                                  ["Model risk tier", "Tier 1 (material)"]]))
    C.version_history(ctx, doc, [("1.0", 1210, "Governance framework for the FRAUDNET scoring model"),
                                 ("2.0", 420, "Updated for the Sentinel name and the re-organisation of Counter-Fraud & SIU"),
                                 ("2.3", 70, "Calibration section rewritten for the 2026 recalibration"),
                                 ("3.0", 0, "Approved for NISA Circular 2026/04")])
    C.approvals(ctx, doc, [("P008", "Accountable executive for the model"), ("P007", "Model risk oversight"),
                           ("P037", "Compliance")])
    C.reviewers(ctx, doc, ["P028", "P036", "P042", "P018"])
    doc.toc(depth=2)

    # 1 -----------------------------------------------------------------------------------
    doc.h(1, "1 Introduction")
    doc.p(f"This document sets out how the Sentinel fraud scoring model is governed, calibrated and monitored. It covers "
          f"model {snt['model_version']}, which scores every new claim at triage, and the way the score is used in the "
          f"referral of claims to Counter-Fraud & SIU. It replaces version 2.0 and reflects the requirements of NISA "
          f"Circular 2026/04, effective from {long_date('2026-04-01')}.")
    doc.ps(pr.paras(["model", "model2"], 3, n=(4, 6)))
    doc.h(2, "1.1 Scope")
    doc.bullets(["The Sentinel scoring engine and model, licensed from " + ven["name"] + ".",
                 "The use of the score in the triage and referral steps of the claims process.",
                 "The referral threshold and its calibration.",
                 "Monitoring, validation, change control and incident management for the model."])
    doc.h(2, "1.2 Regulatory context")
    circ = W.circulars["CIRC-2026-04"]
    rows = [[f"§{r['para']}", r["text"]] for r in circ["requirements"]]
    doc.table(["Paragraph", "Requirement"], rows, widths=[2.4, 14.2], caption=f"{circ['ref']} – {circ['title']}", font_size=8.6)
    doc.ps(pr.paras(["model2", "model"], 2, n=(4, 6)))

    # 2 -----------------------------------------------------------------------------------
    doc.h(1, "2 Model overview", page_break=True)
    doc.kv([["System", f"Sentinel (formerly FRAUDNET, renamed {long_date('2025-03-01')})"],
            ["Type", snt["type"]], ["Technology", snt["tech"]], ["Vendor", f"{ven['name']} ({ven['location']})"],
            ["Hosting", snt["hosting"]], ["Endpoint", "sentinel.corvane.internal"],
            ["Business owner", ctx.person(snt["owner"])], ["Model owner", ctx.person("P027")],
            ["Model version", snt["model_version"]]], caption="Model summary", widths=(4.0, 12.6), font_size=8.8,
           facts=[F("general", "Sentinel was called FRAUDNET until it was renamed on 2025-03-01.",
                    "formerly FRAUDNET, renamed 1 March 2025", "SYSTEM:SYS03#renames", where=(0, 1))])
    doc.p("The engine produces a score from 0 to 100 for each claim. Higher scores indicate a higher likelihood that the "
          "claim warrants investigation. The score is accompanied by the main contributing indicators, which are shown "
          "to the handler and to SIU.")
    doc.ps(pr.paras(["model2", "valid"], 3, n=(4, 6)))
    doc.h(2, "2.1 Where the score is produced and used")
    rows = []
    for iid in ("CLX-IF-008", "CLX-IF-009", "CLX-IF-010", "CLX-IF-036"):
        i = W.interfaces[iid]
        rows.append([iid, i["name"], ctx.sys(i["source_system"]), ctx.sys(i["target_system"]), i["protocol"]])
    doc.table(["Interface", "Name", "From", "To", "Protocol"], rows, widths=[2.4, 6.0, 2.8, 2.8, 2.6],
              caption="Scoring interfaces", font_size=8.6)
    rows = []
    for sid in ("PS-TRI-01", "PS-TRI-03", "PS-FRD-01", "PS-FRD-02"):
        st = W.steps[sid]
        rows.append([sid, st["name"], st["description"], ctx.person(st["raci"]["A"])])
    doc.table(["Step", "Name", "Use of the score", "Accountable"], rows, widths=[2.2, 3.4, 7.4, 3.6],
              caption="Process steps that use the score", font_size=8.4)
    t7 = ctx.rule("BR-TRI-007")
    doc.p(f"Rule BR-TRI-007 (v{t7['version']}) requires every new claim to be scored within "
          f"{t7['parameters']['score_within_minutes']} minutes of notification. Claims Hub calls Sentinel synchronously "
          f"over REST (ADR-013); CLARA uses the online interface and a nightly batch for claims not scored online.")
    doc.ps(pr.paras(["model2", "model"], 1))
    doc.h(2, "2.2 Inputs")
    doc.table(["Input group", "Examples", "Source"],
              [["Claim facts", "Claim type, loss date, notification channel, time to notify", "CLARA / Claims Hub"],
               ["Policy facts", "Inception date, recent changes to cover, payment history", "PALM"],
               ["Party facts", "Prior claims, shared contact or bank details", "CLARA / Claims Hub"],
               ["Evidence facts", "Photo metadata consistency, document completeness", "Evidence Intake Gateway"],
               ["Indicator flags", "Rule-based indicators BR-FRD-001 to BR-FRD-016", "Fraud indicator rules"]],
              widths=[3.4, 8.6, 4.6], caption="Model input groups", font_size=8.6)
    doc.ps(pr.paras(["model2", "model"], 2, n=(4, 6)))
    doc.h(2, "2.3 Fraud indicator rules")
    rows = []
    for rid, r in W.rules.items():
        if not rid.startswith("BR-FRD-0") or int(rid[-3:]) > 16:
            continue
        v = ctx.rule(rid)
        if not v or not ctx.ok(f"RULE:{rid}@v{v['version']}", "text"):
            continue
        rows.append([rid, f"v{v['version']}", r["title"], v["text"]])
    doc.table(["Rule", "Version", "Title", "Text"], rows, widths=[2.2, 1.4, 4.4, 8.6], caption="Fraud rules in force",
              font_size=8.0)
    doc.ps(pr.paras(["model2", "model"], 2))
    doc.h(2, "2.4 Integration with Claims Hub")
    rows = []
    for name in ("triage-svc", "fraud-referral-svc"):
        sv = W.services[name]
        o = W.service_owner(name, date)
        rows.append([name, H.svc_desc(ctx, name), ", ".join(H.topics_ok(ctx, sv["kafka_topics"]["produces"])) or "—",
                     ", ".join(H.topics_ok(ctx, sv["kafka_topics"]["consumes"])) or "—", ctx.team(o["team"]) if o else "—"])
    doc.table(["Service", "Role", "Produces", "Consumes", "Squad"], rows, widths=[2.8, 5.0, 3.2, 3.4, 2.2],
              caption="Claims Hub services that use the score", font_size=8.0)
    doc.p("triage-svc calls Sentinel for every new claim, stores the score with the triage decision and publishes it "
          "on fraud.score.received.v1. fraud-referral-svc consumes the score, applies the referral threshold in force on "
          "the scoring date and creates the referral.")
    rows = [[a["method"], a["path"], a["summary"]] for a in H.svc_apis(ctx, "fraud-referral-svc")]
    doc.table(["Method", "Path", "Summary"], rows, widths=[2.0, 5.6, 9.0], caption="fraud-referral-svc API", font_size=8.4)
    doc.ps(pr.paras(["model2", "integration"], 2))

    # 3 Calibration ------------------------------------------------------------------------
    doc.h(1, "3 Calibration", page_break=True)
    ctx.need("SYSTEM:SYS03", "model_auc")
    auc, cal, share = snt["model_auc"], snt["model_calibrated"], snt["model_referral_share_pct"]
    thr = ctx.rule("BR-FRD-031")["parameters"]["threshold"]
    doc.p(f"Model {snt['model_version']} was recalibrated on {long_date(cal)} on claims notified and investigated during "
          f"the preceding period. The calibration aligns the score scale with observed investigation outcomes so that the "
          f"referral threshold set under NISA Circular 2026/04 refers a stable and explainable share of claims.")
    doc.p(f"On the calibration sample, {snt['model_version']} achieves an AUC of {auc}. At the referral threshold of "
          f"{thr}, the model refers the top {share}% of scored claims to Counter-Fraud & SIU.",
          facts=[PF(ctx, "ld20_auc", f"AUC of {auc}", notes="§3 Calibration."),
                 F("needle", f"At threshold {thr}, SNT-4.2 refers the top {share}% of scored claims.",
                   f"refers the top {share}% of scored claims", "SYSTEM:SYS03#model_referral_share_pct", exclusive=False,
                   notes="Same sentence as the AUC placement (PL-059).")])
    doc.p("The calibration was carried out by the model owner with the vendor's tooling, reviewed by the Data & Analytics "
          "team and submitted to the Risk function for independent validation before deployment.")
    fig = FG.box_diagram(CACHE / "fig" / FID / "calibration.png", title="Calibration and approval workflow",
                         boxes=[{"id": "a", "label": "Extract scored claims\nand SIU outcomes", "x": 60, "y": 160, "w": 400, "h": 160},
                                {"id": "b", "label": "Recalibrate score\n(vendor tooling)", "x": 560, "y": 160, "w": 400, "h": 160},
                                {"id": "c", "label": "Back-test and\nfairness checks", "x": 1060, "y": 160, "w": 400, "h": 160},
                                {"id": "d", "label": "Independent\nvalidation (Risk)", "x": 1560, "y": 160, "w": 380, "h": 160, "color": "purple"},
                                {"id": "e", "label": "Claims Fraud Forum\napproval", "x": 1060, "y": 520, "w": 400, "h": 160, "color": "green"},
                                {"id": "f", "label": "Deploy as effective-\ndated configuration", "x": 560, "y": 520, "w": 400, "h": 160, "color": "amber"},
                                {"id": "g", "label": "Monitor and report", "x": 60, "y": 520, "w": 400, "h": 160, "color": "grey"}],
                         arrows=[{"src": "a", "dst": "b", "label": "sample"}, {"src": "b", "dst": "c", "label": "candidate"},
                                 {"src": "c", "dst": "d", "label": "evidence pack"}, {"src": "d", "dst": "e", "label": "opinion"},
                                 {"src": "e", "dst": "f", "label": "approved"}, {"src": "f", "dst": "g", "label": "live"}],
                         size=(2000, 800))
    doc.figure(fig, "Calibration and approval workflow", alt="Workflow: extract, recalibrate, back-test, independent validation, "
               "Claims Fraud Forum approval, deployment as effective-dated configuration, monitoring.",
               facts=[F("image_text", "The calibration workflow shows independent validation by Risk before Claims Fraud Forum approval.",
                        "Independent validation (Risk)", "SYSTEM:SYS03#model_validation", where="image")])
    doc.h(2, "3.1 Calibration procedure")
    doc.bullets(["Extract scored claims and their investigation outcomes, allowing for the lag in SIU outcomes.",
                 "Recalibrate the score scale using the vendor's tooling under the model owner's control.",
                 "Back-test the candidate on a hold-out sample and compare with the current production model.",
                 "Run fairness and stability checks on the candidate.",
                 "Submit the evidence pack to the Risk function for independent validation.",
                 "Obtain approval from the Claims Fraud Forum and notify the Chief Risk Officer.",
                 "Deploy the new calibration and threshold as effective-dated configuration (ADR-020)."], numbered=True)
    doc.ps(pr.paras(["model2", "valid"], 3, n=(4, 6)))
    doc.h(2, "3.2 Independent validation")
    val = snt["model_validation"]
    doc.p(f"The Risk function, under {ctx.person(val['by'])}, completed its independent validation of "
          f"{snt['model_version']} on {long_date(val['date'])}. The validation concluded that the model is stable and that "
          f"recalibration is due annually. The validation report and management's responses are held in the model "
          f"inventory.",
          facts=[F("general", "SNT-4.2 was independently validated by Karin Holmberg's Risk function on 2026-03-20: stable; recalibration due annually.",
                   "recalibration is due annually", "SYSTEM:SYS03#model_validation")])
    doc.ps(pr.paras(["model2", "model"], 1))
    doc.h(2, "3.3 Next recalibration")
    doc.p("The next recalibration is planned within twelve months of the last one, or earlier if monitoring shows a "
          "material shift in the score distribution or in model performance.")
    doc.ps(pr.paras(["model2", "model"], 2, n=(4, 6)))

    # 4 Threshold ----------------------------------------------------------------------------
    doc.h(1, "4 Referral threshold", page_break=True)
    doc.p("The referral threshold is a business decision informed by the model's performance. It is held as an "
          "effective-dated parameter so that the threshold applied to any claim can be reconstructed.")
    rows, facts = [], []
    for rid in ("BR-FRD-012", "BR-FRD-031"):
        for v in W.rules[rid]["versions"]:
            if not v.get("effective_from") or v["effective_from"] > date:
                continue
            to = v.get("effective_to")
            if to and to > date:
                to = None
            rows.append([f"{rid} v{v['version']}", str(v["parameters"]["threshold"]), short_date(v["effective_from"]),
                         short_date(to) if to else "in force", ctx.a(v["text"]) if date >= "2025-03-01" else v["text"]])
            if rid == "BR-FRD-031":
                facts.append(F("temporal", "From 2026-04-01 the referral threshold is a Sentinel score of 65 (BR-FRD-031 v1, all tiers).",
                               "Refer a claim to SIU when the Sentinel score is 65 or more (all tiers).", "RULE:BR-FRD-031@v1#parameters.threshold",
                               where=(len(rows), 4)))
            if rid == "BR-FRD-012" and v["version"] == 2:
                facts.append(F("temporal", "From 2023-04-01 to 2026-03-31 the referral threshold was 70 (BR-FRD-012 v2).", "31 Mar 2026",
                               "RULE:BR-FRD-012@v2", where=(len(rows), 3)))
    doc.table(["Rule", "Threshold", "From", "To", "Text"], rows, widths=[2.8, 1.8, 2.4, 2.2, 7.4],
              caption="Referral threshold history", font_size=8.4, facts=facts)
    doc.p("Circular 2026/04 requires score-based cut-offs on a 0–100 scale not to exceed 65. The threshold of 65 "
          "applies to all tiers from 1 April 2026. Decisions to decline, reduce or repudiate a claim are never taken on "
          "the score alone (BR-FRD-033); every adverse outcome requires a documented human review by SIU.")
    doc.ps(pr.paras(["model2", "valid"], 3, n=(4, 6)))
    doc.h(2, "4.1 Changing the threshold")
    doc.p(f"A proposal to change the threshold is prepared by the model owner with an impact assessment, reviewed by "
          f"Compliance and decided by the Claims Fraud Forum chaired by {ctx.person('P008')}. Approved changes are "
          f"deployed to CLARA (CLR.T_PARAM) and to Claims Hub configuration with the same effective date.")
    doc.ps(pr.paras(["model2", "governance"], 2))
    doc.h(2, "4.2 Parameter configuration")
    doc.p("In CLARA the threshold is read from CLR.T_PARAM through the parameter lookup routine. The rows below show the "
          "fraud referral parameters and their validity periods up to the date of this document.")
    rows = []
    for r in W.tables["CLR.T_PARAM"]["param_rows"]:
        if r["key"] not in ("FRD_REFER_THRESH", "FRD_NOTICE_BUS_DAYS") or r["valid_from"] > date:
            continue
        if not ctx.ok("TABLE:CLR.T_PARAM", f"param_rows:{r['key']}"):
            continue
        to = r["valid_to"] if r["valid_to"] and r["valid_to"] <= date else None
        rows.append([r["key"], r["value"], short_date(r["valid_from"]), short_date(to) if to else "—", r["rule"].replace("@v", " v"),
                     r["ticket"] or "—"])
    doc.table(["Key", "Value", "Valid from", "Valid to", "Rule", "Change"], rows, widths=[4.2, 1.6, 2.6, 2.6, 3.2, 2.4],
              caption="Fraud referral parameters in CLR.T_PARAM", font_size=8.6,
              facts=[F("general", "CLR.T_PARAM FRD_REFER_THRESH = 65 from 2026-04-01 (CHUB-205).", "CHUB-205",
                       "TABLE:CLR.T_PARAM#param_rows:FRD_REFER_THRESH", where=(next(i for i, r in enumerate(rows, 1) if r[1] == "65"), 5))])
    doc.p("In Claims Hub the same values are held as effective-dated configuration of fraud-referral-svc. A daily check "
          "compares the two configurations while both platforms score claims.")
    doc.ps(pr.paras(["model2", "model"], 2, n=(4, 6)))

    # 5 Roles ---------------------------------------------------------------------------
    doc.h(1, "5 Roles and responsibilities")
    rows = [["Accountable executive", ctx.person("P008"), "Accountable for the model and its use; chairs the Claims Fraud Forum"],
            ["Model owner", ctx.person("P027"), "Performance, documentation, calibration and monitoring"],
            ["Independent validator", f"Risk function ({ctx.person('P007')})", "Independent validation and model risk oversight"],
            ["Compliance", ctx.person("P037"), "Conduct and regulatory compliance of the referral process"],
            ["SIU operations", ctx.person("P028"), "Investigation outcomes used as model labels"],
            ["Data & Analytics", ctx.person("P036"), "Data extracts, monitoring dashboards and data quality"],
            ["Claims Hub squad", ctx.person("P042"), "Integration of the score into fraud-referral-svc"],
            ["Vendor", ven["name"], "Scoring engine, technical documentation and calibration tooling"]]
    doc.table(["Role", "Holder", "Responsibilities"], rows, widths=[3.6, 5.6, 7.4], caption="Model governance roles",
              font_size=8.6)
    doc.ps(pr.paras(["model", "model2"], 3, n=(4, 6)))
    doc.h(2, "5.1 Governance forums")
    com = W.committees["COM-02"]
    doc.p(f"The {com['name']} meets {com['cadence']} and is chaired by {ctx.name('P008')}. Its remit is: "
          f"{com['remit'][0].lower() + com['remit'][1:]}" + ("" if com["remit"].endswith(".") else "."))
    doc.ps(pr.paras(["governance", "model2"], 1))

    # 6 Monitoring ----------------------------------------------------------------------
    doc.h(1, "6 Monitoring", page_break=True)
    doc.ps(pr.paras(["model", "model2"], 3, n=(4, 6)))
    doc.table(["Measure", "What it shows", "Frequency", "Reported to"],
              [["Score distribution", "Shift in the population of scored claims", "Monthly", "Claims Fraud Forum"],
               ["Population stability", "Change in the distribution of scores and key inputs against the calibration sample", "Monthly", "Claims Fraud Forum"],
               ["Referral share", "Share of scored claims at or above the threshold", "Monthly", "Claims Fraud Forum"],
               ["Discrimination", "Ability of the score to separate confirmed fraud from genuine claims", "Quarterly", "Claims Fraud Forum, Risk"],
               ["Outcome mix", "Investigation outcomes by score band", "Quarterly", "Claims Fraud Forum"],
               ["Fairness", "Differences in referral rates between customer groups", "Quarterly", "Compliance, Risk"],
               ["Availability", "Scoring service availability and response time", "Daily", "Integration Platform"],
               ["Unscored claims", "Claims not scored within the time required by BR-TRI-007", "Daily", "Counter-Fraud & SIU"]],
              widths=[3.2, 7.0, 2.2, 4.2], caption="Monitoring measures", font_size=8.4)
    doc.p("Trigger levels for each measure are set in the monitoring specification maintained by the model owner. A "
          "breach is reported to the accountable executive and recorded in the model inventory with the actions taken.")
    fin = W.company["financials"]["fy2025"]
    doc.h(2, "6.1 Outcomes in 2025")
    doc.p(f"In 2025 Counter-Fraud & SIU received {fin['fraud_referrals']:,} referrals and confirmed {fin['confirmed_fraud_cases']:,} "
          f"cases of fraud, with recorded fraud savings of £{fin['fraud_savings_gbp_m']}m. These outcomes are the labels "
          f"used for monitoring and for the 2026 calibration.",
          facts=[F("general", "FY2025: 4,812 fraud referrals, 1,109 confirmed fraud cases, fraud savings £38.7m.",
                   f"{fin['fraud_referrals']:,} referrals", "ORG:company#financials.fy2025.fraud_referrals")])
    doc.ps(pr.paras(["model2", "model"], 2, n=(4, 6)))

    # 7 Change ------------------------------------------------------------------------
    doc.h(1, "7 Change management")
    doc.table(["Change type", "Examples", "Approval"],
              [["Material", "New model version, recalibration, new input feature, threshold change", "Claims Fraud Forum after independent validation; CRO notified"],
               ["Minor", "Vendor patch without change to scores, documentation update", "Model owner, recorded in the inventory"],
               ["Emergency", "Disabling a corrupted input feed", "Accountable executive; retrospective review at the next forum"]],
              widths=[2.6, 7.4, 6.6], caption="Model change classes", font_size=8.6)
    doc.ps(pr.paras(["model2", "governance"], 2))

    # 8 Fairness ----------------------------------------------------------------------
    doc.h(1, "8 Fairness, explainability and customer treatment")
    doc.ps(pr.paras(["model2"], 3))
    doc.p("Customers whose claims are referred are told in writing that the claim is subject to additional checks, in "
          "line with BR-FRD-032 and the deferral rules in BR-FRD-036.")

    # 9 Incidents ---------------------------------------------------------------------
    doc.h(1, "9 Model incidents", page_break=True)
    rows = []
    for iid in ("INC-2025-0233", "INC-2026-0518"):
        inc = W.incidents[iid]
        rows.append([iid, short_date(inc["date"]), inc["severity"], ctx.a(inc["title"]).strip(), inc["root_cause"]])
    doc.table(["Incident", "Date", "Severity", "Title", "Root cause"], rows, widths=[2.6, 2.2, 1.6, 4.2, 6.0],
              caption="Incidents affecting the use of the score", font_size=8.2,
              facts=[F("general", "INC-2026-0518 (2026-05-12): the batch fraud sweep used the pre-2026 referral threshold.",
                       "Batch fraud sweep used pre-2026 referral threshold", "INCIDENT:INC-2026-0518", where=(2, 3))])
    doc.p("Following INC-2026-0518, Compliance runs a daily query for claims scoring 65 to 69 that were not referred, "
          "until the permanent fix to the batch path is released.")
    doc.ps(pr.paras(["model2", "model"], 2, n=(4, 6)))

    # 10 Inventory ---------------------------------------------------------------------
    doc.h(1, "10 Model inventory record")
    doc.kv([["Model ID", "MDL-CFR-001"], ["Name", f"Sentinel fraud score {snt['model_version']}"],
            ["Purpose", "Prioritise claims for referral to Counter-Fraud & SIU"], ["Risk tier", "Tier 1 (material)"],
            ["Owner", ctx.person("P027")], ["Accountable executive", ctx.person("P008")],
            ["Validator", f"Risk function ({ctx.name('P007')})"], ["Last calibration", long_date(cal)],
            ["Last validation", long_date(val["date"])], ["Validation result", val["result"]],
            ["Approved uses", "Referral prioritisation at triage; SIU case prioritisation"],
            ["Prohibited uses", "Declining, reducing or repudiating a claim on the score alone; pricing; underwriting"]],
           widths=(4.4, 12.2), font_size=8.8)
    doc.ps(pr.paras(["model2", "model"], 2, n=(4, 6)))

    # 11 Data -------------------------------------------------------------------------
    doc.h(1, "11 Data management and quality", page_break=True)
    doc.ps(pr.paras(["model2", "data"], 2))
    rows = []
    for iid in ("CLX-IF-003", "CLX-IF-004", "CLX-IF-008", "CLX-IF-009", "CLX-IF-010", "CLX-IF-012", "CLX-IF-036", "CLX-IF-041"):
        i = W.interfaces[iid]
        rows.append([iid, i["name"], f"{ctx.sys(i['source_system'])} → {ctx.sys(i['target_system'])}", i["protocol"],
                     ctx.name(i["owner"]) if i.get("owner") and ctx.employed(i["owner"]) else "—"])
    doc.table(["Interface", "Name", "Flow", "Protocol", "Owner"], rows, widths=[2.4, 5.4, 4.6, 1.8, 2.4],
              caption="Data flows relevant to the model", font_size=8.2)
    doc.ps(pr.paras(["model2", "data"], 2))
    doc.h(2, "11.1 Outcome labels")
    doc.p("Investigation outcomes recorded in the SIU Case Manager are returned to the claims platforms and form the "
          "labels used for monitoring and calibration. Outcome codes follow the SIU case closure codes (BR-FRD-011); "
          "feedback of outcomes to the claims teams follows BR-FRD-017.")
    doc.ps(pr.paras(["model2", "valid"], 3, n=(4, 6)))

    # 12 Limitations -------------------------------------------------------------------
    doc.h(1, "12 Model limitations")
    doc.table(["Limitation", "Effect", "Mitigation"],
              [["Outcome labels arrive with a delay", "Recent performance cannot be measured immediately", "Monitoring uses matured cohorts alongside early indicators"],
               ["Only referred claims are investigated", "Labels are missing for claims below the threshold", "Periodic random sampling of claims below the threshold"],
               ["New fraud patterns", "Patterns absent from the calibration sample are scored poorly", "SIU intelligence fed into indicator rules and recalibration"],
               ["Input data quality", "Missing or late inputs reduce score quality", "Data quality checks on each feed; unscored claims monitored daily"],
               ["Vendor model internals", "Corvane cannot change the model structure directly", "Contractual documentation and testing rights; independent validation"],
               ["Different populations by region", "Nordic and UK claims differ in volume and mix", "Monitoring by region; regional review of referrals"]],
              widths=[4.0, 5.8, 6.8], caption="Known limitations", font_size=8.4)
    doc.ps(pr.paras(["model2", "model"], 2))

    # 13 Vendor ------------------------------------------------------------------------
    doc.h(1, "13 Vendor management")
    doc.p(f"The scoring engine is licensed from {ven['name']}, {ven['location']} (supplier code {ven['code']}), a supplier "
          f"to Corvane since {long_date(ven['panel_from'])}. The vendor provides the engine, technical documentation, "
          f"calibration tooling and support. Corvane remains accountable for the use of the model and for its outcomes.",
          facts=[F("general", "The Sentinel scoring engine is licensed from Kestwick Analytics Ltd (Cambridge).", ven["name"],
                   f"VENDOR:{ven['id']}#role")])
    doc.ps(pr.paras(["model2", "vendor"], 2))

    # 14 Risk assessment ----------------------------------------------------------------
    doc.h(1, "14 Model risk assessment", page_break=True)
    doc.table(["Risk", "Description", "Controls", "Residual"],
              [["Performance deterioration", "The model refers fewer fraudulent claims over time", "Monitoring, annual recalibration, independent validation", "Low"],
               ["Inappropriate use", "The score is used outside its approved purpose", "Prohibited uses in the inventory; BR-FRD-033; access controls", "Low"],
               ["Implementation error", "Production threshold or scores differ from the approved specification", "Effective-dated configuration; daily reconciliation of parameters", "Medium"],
               ["Unfair outcomes", "Some customer groups are referred disproportionately", "Quarterly fairness review; Compliance oversight", "Low"],
               ["Availability", "Claims are not scored when the service is unavailable", "Nightly batch scoring of unscored claims; monitoring", "Low"],
               ["Vendor dependency", "Loss of vendor support", "Contract terms; documented exit plan", "Medium"]],
              widths=[3.2, 5.0, 6.0, 2.4], caption="Model risks", font_size=8.4)
    doc.ps(pr.paras(["model2", "model"], 2))

    # 15 Circular mapping ---------------------------------------------------------------
    doc.h(1, "15 Mapping to NISA Circular 2026/04", page_break=True)
    doc.p("The table shows how each requirement of the Circular that touches the model or the use of the score is "
          "met. Requirements that concern only the referral process are covered in the fraud referral BRD.")
    maps = {"3.1": "Approved uses exclude adverse decisions on the score alone; BR-FRD-033 enforced in both platforms",
            "3.2": "Out of scope for the model; covered by BR-FRD-032 and BR-FRD-036",
            "3.3": "Calibration in section 3; threshold of 65 in section 4; calibration evidence approved by the Claims Fraud Forum",
            "3.4": "Referral counts in the NISA-FR1 return reconciled to the model's referral share",
            "3.5": "Scores, thresholds applied and referral records retained in line with the retention schedule"}
    doc.table(["Paragraph", "Requirement", "How it is met"],
              [[f"§{r['para']}", r["text"], maps.get(str(r["para"]), "—")] for r in circ["requirements"]],
              widths=[1.8, 7.2, 7.6], caption="Circular requirements and model controls", font_size=8.2)
    doc.ps(pr.paras(["model2", "valid"], 3, n=(4, 6)))
    gfig = FG.box_diagram(CACHE / "fig" / FID / "governance.png", title="Sentinel model governance structure",
                          boxes=[{"id": "cro", "label": f"Chief Risk Officer\n{ctx.name('P007')}", "x": 1300, "y": 140, "w": 560, "h": 150, "color": "purple"},
                                 {"id": "cff", "label": f"Claims Fraud Forum\nchair {ctx.name('P008')}", "x": 140, "y": 140, "w": 560, "h": 150, "color": "green"},
                                 {"id": "own", "label": f"Model owner\n{ctx.name('P027')}", "x": 140, "y": 460, "w": 560, "h": 150},
                                 {"id": "val", "label": "Independent validation\n(Risk function)", "x": 1300, "y": 460, "w": 560, "h": 150, "color": "purple"},
                                 {"id": "cmp", "label": f"Compliance\n{ctx.name('P037')}", "x": 720, "y": 760, "w": 560, "h": 150, "color": "amber"}],
                          arrows=[{"src": "own", "dst": "cff", "label": "reports performance"},
                                  {"src": "val", "dst": "cro", "label": "validation opinion"},
                                  {"src": "own", "dst": "val", "label": "evidence pack"},
                                  {"src": "cmp", "dst": "cff", "label": "conduct review"}],
                          size=(2000, 980))
    doc.figure(gfig, "Sentinel model governance structure",
               alt="Governance structure: the model owner reports performance to the Claims Fraud Forum and submits an evidence pack to the Risk function, which gives its validation opinion to the CRO.")
    doc.ps(pr.paras(["model2", "governance"], 2, n=(4, 6)))

    # 16 Reporting -------------------------------------------------------------------
    doc.h(1, "16 Monitoring report")
    doc.p("The model owner produces a monitoring report for each Claims Fraud Forum. The report follows a fixed "
          "structure so that trends can be compared between meetings.")
    doc.table(["Section", "Content"],
              [["Summary", "Overall status of the model and any breaches since the last report"],
               ["Population", "Volumes scored by region, channel and claim type; unscored claims"],
               ["Distribution", "Score distribution and stability against the calibration sample"],
               ["Referrals", "Referral share, referrals by region and by indicator"],
               ["Outcomes", "Investigation outcomes by score band for matured cohorts"],
               ["Fairness", "Referral rates by customer group, with commentary"],
               ["Operations", "Availability, response time and incidents"],
               ["Actions", "Open actions from validation, incidents and previous reports"]],
              widths=[3.4, 13.2], caption="Monitoring report structure", font_size=8.6)
    doc.ps(pr.paras(["model2", "kpi"], 2, n=(4, 6)))
    doc.h(2, "16.1 Escalation")
    doc.ps(pr.paras(["model2", "governance"], 2, n=(4, 5)))

    # 17 Review cycle ----------------------------------------------------------------
    doc.h(1, "17 Annual review cycle")
    doc.table(["Activity", "Timing", "Lead"],
              [["Recalibration", "Annually, or earlier if triggered by monitoring", "Model owner"],
               ["Independent validation", "Before each material change and at least annually", "Risk function"],
               ["Fairness review", "Quarterly", "Compliance"],
               ["Documentation review", "With each material change and at least annually", "Model owner"],
               ["Inventory attestation", "Annually", "Accountable executive"],
               ["Vendor service review", "Twice a year", "Counter-Fraud & SIU"]],
              widths=[4.2, 8.2, 4.2], caption="Review cycle", font_size=8.6)
    doc.ps(pr.paras(["model2", "valid"], 2, n=(4, 6)))
    doc.h(2, "17.1 Calibration evidence pack")
    doc.bullets(["Description of the calibration sample and its outcome labels.",
                 "Performance of the candidate and the current model on the hold-out sample.",
                 "Referral share at the proposed threshold and at neighbouring values.",
                 "Stability and fairness analysis.",
                 "Implementation test results in CLARA and Claims Hub.",
                 "Vendor confirmation of the calibration method."])
    doc.ps(pr.paras(["model2"], 1, n=(4, 6)))

    # 18 SIU feedback ----------------------------------------------------------------
    doc.h(1, "18 SIU feedback loop", page_break=True)
    st4 = W.steps["PS-FRD-04"]
    r35 = ctx.rule("BR-FRD-035")
    doc.p(f"Referred claims are triaged and investigated by Counter-Fraud & SIU ({st4['id']} {st4['name']}). "
          f"Under BR-FRD-035 v{r35['version']}: {r35['text']} Investigation outcomes are recorded in the SIU Case "
          f"Manager and returned to the claims platforms, where they become the outcome labels for the model.")
    doc.ps(pr.paras(["model2", "model"], 2, n=(4, 6)))
    doc.table(["Stage", "Owner", "Output used by the model"],
              [["Referral created", ctx.team("T11"), "Referral date, threshold applied, score and indicators"],
               ["SIU triage", ctx.person("P028"), "Triage decision and priority"],
               ["Investigation", ctx.team("T11"), "Evidence gathered and investigation notes"],
               ["Outcome", ctx.person("P028"), "Closure code under BR-FRD-011"],
               ["Feedback", ctx.team("T11"), "Outcome communicated to the claims team under BR-FRD-017"]],
              widths=[3.6, 5.4, 7.6], caption="Feedback of investigation outcomes", font_size=8.6)
    doc.ps(pr.paras(["model2", "valid"], 2, n=(4, 6)))

    # 19 Training ----------------------------------------------------------------------
    doc.h(1, "19 Training and awareness")
    r18 = ctx.rule("BR-FRD-018")
    if r18 and ctx.ok(f"RULE:BR-FRD-018@v{r18['version']}", "text"):
        doc.p(f"Counter-fraud training follows BR-FRD-018 (v{r18['version']}): {r18['text']}")
    doc.p("Users of the score are trained on what it means, how the contributing indicators should be read, and the "
          "limits on its use. Training material is reviewed whenever the model or the threshold changes.")
    doc.ps(pr.paras(["model2", "model"], 2, n=(4, 6)))

    doc.h(1, "Appendix A – Measure definitions", page_break=True)
    doc.table(["Measure", "Definition"],
              [["AUC", "Probability that a randomly chosen confirmed-fraud claim has a higher score than a randomly chosen genuine claim."],
               ["Population stability index", "Sum over score bands of (actual share − expected share) × ln(actual share ÷ expected share)."],
               ["Referral share", "Claims scored at or above the threshold divided by all claims scored in the period."],
               ["Hit rate", "Referred claims with a confirmed-fraud outcome divided by referred claims with a closed investigation."],
               ["Capture rate", "Confirmed-fraud claims that were referred divided by all confirmed-fraud claims."],
               ["Unscored rate", "Claims not scored within the BR-TRI-007 window divided by new claims."]],
              widths=[4.2, 12.4], caption="Monitoring measure definitions", font_size=8.6)
    doc.ps(pr.paras(["model2", "model"], 2, n=(4, 6)))
    doc.h(1, "Appendix B – Model lifecycle RACI")
    rows = [["Recalibrate the model", "Model owner", ctx.name("P008"), "Data & Analytics, vendor", "Compliance"],
            ["Validate the model", "Risk function", ctx.name("P007"), "Model owner", "Claims Fraud Forum"],
            ["Approve a threshold change", "Model owner", "Claims Fraud Forum", "Compliance", "CRO, Claims Director"],
            ["Deploy configuration", "Claims Hub squad, CLARA support", ctx.name("P008"), "Model owner", "SIU operations"],
            ["Monitor performance", "Model owner", ctx.name("P008"), "Data & Analytics", "Claims Fraud Forum"],
            ["Review fairness", "Compliance", ctx.name("P037"), "Model owner", "Risk function"],
            ["Manage incidents", "Model owner", ctx.name("P008"), "Integration Platform", "Compliance"]]
    doc.table(["Activity", "Responsible", "Accountable", "Consulted", "Informed"], rows, widths=[4.2, 3.6, 3.0, 3.2, 2.6],
              caption="Model lifecycle RACI", font_size=8.4)
    doc.h(1, "Appendix C – Fraud rules related to referral")
    rows = []
    for rid, r in W.rules.items():
        if not rid.startswith("BR-FRD-") or int(rid[-3:]) < 17:
            continue
        v = ctx.rule(rid)
        if not v or not ctx.ok(f"RULE:{rid}@v{v['version']}", "text"):
            continue
        rows.append([rid, f"v{v['version']}", r["title"], v["text"]])
    doc.table(["Rule", "Version", "Title", "Text"], rows, widths=[2.2, 1.4, 4.4, 8.6], font_size=8.0,
              caption="Referral and SIU rules in force")
    doc.h(1, "Appendix D – Glossary", page_break=True)
    doc.table(["Term", "Meaning"],
              [["AUC", "Area under the receiver operating characteristic curve; a measure of how well the score separates the two outcome groups."],
               ["Calibration", "Alignment of the score scale with observed outcomes."],
               ["Population stability", "A measure of how much a distribution has shifted between two periods."],
               ["Referral share", "The share of scored claims at or above the referral threshold."]]
              + [[t, ctx.a(m)] for t, m in C.glossary_terms(["G-002", "G-009", "G-012"])],
              widths=[3.6, 13.0], font_size=8.6)
    return doc
