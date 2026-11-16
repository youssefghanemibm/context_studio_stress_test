"""LD030 – Brackenfield Loss Adjusting – Service Level Schedule 2025 (reportlab PDF, signed 2025-04-01)."""
from __future__ import annotations

from . import common as C
from .core import Ctx, Doc, F, PF, Style, W, gbp, long_date, short_date, util
from .prose import Prose


def rules_in_force(ctx: Ctx, prefix: str) -> list[tuple[str, dict, dict]]:
    out = []
    for rid, r in W.rules.items():
        if not rid.startswith(prefix):
            continue
        v = ctx.rule(rid)
        if not v:
            continue
        ref = f"RULE:{rid}@v{v['version']}"
        if not (ctx.ok(ref, "text") and ctx.ok(ref, "parameters")):
            continue
        out.append((rid, r, v))
    return out


def build() -> Doc:
    ctx = Ctx("LD030")
    date = ctx.date
    pr = Prose(util.rng("LD030:prose"), date=ctx.date)
    ven = W.vendors["VEN-01"]
    doc = Doc(ctx, title="Brackenfield Loss Adjusting – Service Level Schedule 2025", doc_id="PSA-BRK-S3-2025",
              version="1.0", status="Signed",
              subtitle="Schedule 3 to the Panel Services Agreement: UK property and motor loss adjusting",
              style=Style(serif=True, accent="2E4057", accent2="E3E8EF", size=11.2, pdf_leading=1.7),
              header_left="Corvane Mutual / Brackenfield Loss Adjusting Ltd – Service Level Schedule 2025",
              footer_left="Commercial in confidence – Classification: Confidential", classification="Confidential")
    ctx.need("VENDOR:VEN-01", "sla")
    sla = ven["sla"]
    fees = ven["fees"]
    head_asm = "P033"
    doc.title_page(C.control_rows(ctx, doc, owner=head_asm, extra=[
        ["Customer", W.company["legal_name"]],
        ["Supplier", f"{ven['name']} (supplier code {ven['code']}), {ven['location']}"],
        ["Supplier contact", f"{W.name_of(ven['contact'], date)}, {W.title_of(ven['contact'], date)}"],
        ["Effective date", long_date(date)],
        ["Panel appointment", f"Panel member since {long_date(ven['panel_from'])}"],
    ]))
    doc.toc(depth=2)

    # 1 -----------------------------------------------------------------------------------
    doc.h(1, "1. Introduction")
    doc.p(f"This Schedule sets out the service levels, fees and operating requirements that apply to loss adjusting "
          f"services provided by {ven['name']} (\"Brackenfield\" or the \"Supplier\") to {W.company['legal_name']} "
          f"(\"Corvane\") from {long_date(date)}. It forms part of the Panel Services Agreement and replaces the "
          f"previous service level schedule in full.")
    doc.p(f"Brackenfield provides {ven['role'][0].lower() + ven['role'][1:]}. Instructions are issued by the Claims "
          f"Assessment UK team on behalf of Claims Operations UK and the Major & Complex Loss team.")
    doc.ps(pr.paras("vendor", 2))
    doc.h(2, "1.1 Order of precedence")
    doc.p("In the event of any conflict between this Schedule and the Panel Services Agreement, the Agreement prevails "
          "except in relation to service levels and fees, where this Schedule prevails. Corvane's claims-handling "
          "standards apply to all work performed under this Schedule.")
    doc.p(pr.para("vendor", n=3))
    doc.h(2, "1.2 Interpretation")
    t3 = ctx.rule("BR-TRI-003")
    defs = [
        ["Business Day", "A day other than a Saturday, Sunday or public holiday in England."],
        ["Claims Assessor", "A person, employed by Corvane or by a panel firm, who inspects or desk-assesses a loss "
                            "and reports an estimate. Brackenfield's loss adjusters act as external Claims Assessors."],
        ["Instruction", "A request from Corvane to assess a claim, issued through the Adjuster Extranet."],
        ["Desk Assessment", "An assessment completed from documents, photographs and telephone or video contact, "
                            "without attending the risk address."],
        ["Site Visit", "Attendance at the risk address or vehicle location by a qualified loss adjuster."],
        ["Report", "The written assessment uploaded to the Adjuster Extranet, including the estimate, cause of loss, "
                   "policy liability observations and supporting photographs."],
        ["Tier-3 claim", f"A claim classified as Tier-3 under rule BR-TRI-003 (version {t3['version']}): {t3['text']}"],
        ["Service Level", "A measurable standard set out in Schedule 1."],
        ["Service Credit", "A reduction in fees applied under Schedule 6 when a Service Level is missed."],
        ["Adjuster Extranet", "Corvane's portal through which instructions, reports and invoices are exchanged with "
                              "Claims Assessors."],
        ["MI Pack", "The management information report described in Schedule 4."],
    ]
    doc.table(["Term", "Meaning"], defs, widths=[3.6, 13.0], caption="Defined terms")
    tier_fact = F("general", f"The 2025 Brackenfield schedule defines a Tier-3 claim by BR-TRI-003 v{t3['version']}.",
                  "A claim classified as Tier-3 under rule BR-TRI-003", f"RULE:BR-TRI-003@v{t3['version']}#text")
    doc.blocks[-1].facts.append(F("general", "Instructions to Brackenfield are issued through the Adjuster Extranet (the "
                                  "Assessor Portal's name before 2025-09-01).", "A request from Corvane to assess a claim, issued through the Adjuster Extranet",
                                  "SYSTEM:SYS17#renames", where=(3, 1)))
    doc.blocks[-1].facts.append(tier_fact)
    tier_fact.where = (7, 1)

    # 2 -----------------------------------------------------------------------------------
    doc.h(1, "2. Scope of services")
    doc.p(pr.intro("the services Brackenfield provides under this Schedule"))
    uk_products = [p for p in W.products.values() if p["id"].endswith("-UK") and p["line"] in ("Motor", "Home", "Commercial Property")]
    rows = []
    for p in uk_products:
        cts = [W.claim_types[c]["name"] for c in p.get("claim_types", []) if c in W.claim_types]
        rows.append([p["name"], p["code"], ", ".join(cts) if cts else "All perils"])
    doc.table(["Product", "Code", "Claim types in scope"], rows, widths=[4.6, 2.2, 9.8],
              caption="Products and claim types in scope")
    doc.p("SME Liability claims, Nordic claims and bodily-injury assessments are outside the scope of this Schedule. "
          "Major-loss work on Tier-3 claims is in scope and is charged at the hourly rate in Schedule 2.")
    doc.ps(pr.paras("vendor", 2))
    doc.h(2, "2.1 Services")
    svc_rows = [
        ["Desk assessment", "Assessment from documents and photographs, with telephone or video contact where needed.",
         "Motor and home claims where a site visit is not required"],
        ["Site visit", "Attendance at the risk address or vehicle location, scope of works and estimate.",
         "Property claims and motor claims requiring inspection"],
        ["Major-loss adjusting", "Ongoing adjusting of Tier-3 claims, including interim reports and reserve recommendations.",
         "Tier-3 claims routed to Major & Complex Loss"],
        ["Validation of repairer estimates", "Review of estimates submitted by repair networks and contractors.",
         "Claims referred by Claims Handlers"],
        ["Re-inspection", "Further attendance where the scope of loss changes materially.", "As instructed"],
    ]
    doc.table(["Service", "Description", "Typical use"], svc_rows, widths=[3.8, 7.6, 5.2], caption="Service catalogue")

    # 3 -----------------------------------------------------------------------------------
    doc.h(1, "3. Instructions, reports and invoices")
    doc.p("All instructions are issued electronically through the Adjuster Extranet. Brackenfield shall accept or "
          "decline each instruction through the Adjuster Extranet and shall not accept instructions by any other route "
          "unless Corvane confirms them in writing.")
    rows = []
    for iid in ("CLX-IF-013", "CLX-IF-014", "CLX-IF-016"):
        i = W.interfaces[iid]
        ctx.need(f"INTERFACE:{iid}", "schedule")
        rows.append([iid, ctx.a(i["name"]), f"{ctx.sys(i['source_system'])} → {ctx.sys(i['target_system'])}",
                     W.interface_schedule(iid, date)])
    doc.table(["Interface", "Name", "Flow", "Schedule"], rows, widths=[2.6, 4.4, 5.6, 4.0],
              caption="Interfaces supporting the service",
              facts=[F("general", "CLX-IF-013 (assessor instructions) runs every 30 minutes 07:00-19:00.",
                       W.interface_schedule("CLX-IF-013", date), "INTERFACE:CLX-IF-013#schedule", where=(1, 3)),
                     F("general", "CLX-IF-014 (assessor reports) runs hourly 08:00-20:00.",
                       W.interface_schedule("CLX-IF-014", date), "INTERFACE:CLX-IF-014#schedule", where=(2, 3))])
    doc.p("Instructions released by CLARA are made available on the Adjuster Extranet at the next interface run. "
          "Reports uploaded by Brackenfield are imported into CLARA at the next scheduled report run and are then "
          "visible to the Claims Handler. Invoices are matched against instructions before payment.")
    doc.ps(pr.paras("integration", 2))

    # 4 -----------------------------------------------------------------------------------
    doc.h(1, "4. Schedule 1 – Service levels", page_break=True)
    doc.p("The following Service Levels apply to every instruction issued under this Schedule. Service Levels are "
          "measured in Business Days from the time the instruction is issued on the Adjuster Extranet.")
    sla_rows = [
        ["SL1", "Desk assessment completed", f"within {sla['desk_assessment_business_days']} business days of instruction"],
        ["SL2", "Site visit attended", f"within {sla['site_visit_business_days']} business days of instruction"],
        ["SL3", "Report uploaded to the Adjuster Extranet", f"within {sla['report_business_days']} business days of the site visit or desk assessment"],
    ]
    pf = [F("needle", "Brackenfield SLA: desk assessment within 2 business days of instruction.",
            f"within {sla['desk_assessment_business_days']} business days of instruction",
            "VENDOR:VEN-01#sla.desk_assessment_business_days", where=(1, 2)),
          F("needle", "Brackenfield SLA: site visit within 5 business days of instruction.",
            f"within {sla['site_visit_business_days']} business days of instruction", "VENDOR:VEN-01#sla.site_visit_business_days",
            where=(2, 2)),
          F("needle", "Brackenfield SLA: report within 5 business days of the visit or desk assessment.",
            f"within {sla['report_business_days']} business days of the site visit", "VENDOR:VEN-01#sla.report_business_days",
            where=(3, 2))]
    doc.table(["Ref", "Service Level", "Standard"], sla_rows, widths=[1.5, 6.0, 9.1], caption="Schedule 1 service levels",
              facts=pf)
    doc.p(f"In summary, the Brackenfield service levels are: desk assessment within "
          f"{sla['desk_assessment_business_days']} business days; site visit within {sla['site_visit_business_days']} "
          f"business days; report within {sla['report_business_days']} business days.",
          facts=[PF(ctx, "ld30_sla",
                   f"desk assessment within {sla['desk_assessment_business_days']} business days; site visit within "
                   f"{sla['site_visit_business_days']} business days; report within {sla['report_business_days']} business days")])
    doc.h(2, "4.1 Corvane claims-handling standards that apply to panel work")
    doc.p("Brackenfield shall also comply with the following Corvane business rules in force at the date of this "
          "Schedule. Where a rule and a Service Level differ, the stricter standard applies.")
    asm = rules_in_force(ctx, "BR-ASM-")
    rows = [[rid, r["title"], v["text"]] for rid, r, v in asm]
    facts = []
    for i, (rid, r, v) in enumerate(asm):
        if rid in ("BR-ASM-005", "BR-ASM-004", "BR-ASM-006", "BR-ASM-003"):
            facts.append(F("general", f"{rid} v{v['version']} in force on {date}: {v['text']}", v["text"][:70].rstrip(),
                           f"RULE:{rid}@v{v['version']}#text", where=(i + 1, 2)))
    doc.table(["Rule", "Title", "Requirement"], rows, widths=[2.4, 4.6, 9.6], caption="Assessment rules applying to panel work",
              facts=facts, font_size=8.4)
    doc.ps(pr.paras("vendor", 2))
    doc.h(2, "4.2 Measurement and exclusions")
    doc.bullets([
        "The clock starts when the instruction is issued and stops when the relevant event is recorded on the Adjuster Extranet.",
        "Instructions cancelled by Corvane before the Service Level falls due are excluded from measurement.",
        "Where access to the risk address is refused or delayed by the policyholder, the clock is paused for the period of the delay, provided the delay is recorded on the instruction.",
        "Re-inspections are measured as new instructions.",
        "Measurement is based on the Adjuster Extranet audit trail; the Supplier's own records are used only where the Extranet was unavailable.",
    ])
    doc.p(pr.para(["vendor", "governance"], n=4))

    # 5 -----------------------------------------------------------------------------------
    doc.h(1, "5. Schedule 2 – Fees")
    doc.p("Fees are inclusive of all disbursements other than those listed as recoverable in the Panel Services "
          "Agreement. VAT is charged in addition where applicable.")
    frows = [["Desk assessment", "Per instruction", gbp(fees["desk_assessment_gbp"])],
             ["Site visit (including report)", "Per instruction", gbp(fees["site_visit_gbp"])],
             ["Major-loss adjusting", "Per hour", gbp(fees["major_loss_hourly_gbp"])]]
    doc.table(["Fee item", "Basis", "Fee (GBP)"], frows, widths=[7.0, 4.6, 5.0], caption="Schedule 2 fees",
              facts=[F("needle", "Brackenfield fee: desk assessment £185.", gbp(fees["desk_assessment_gbp"]),
                       "VENDOR:VEN-01#fees.desk_assessment_gbp", where=(1, 2)),
                     F("needle", "Brackenfield fee: site visit £420.", gbp(fees["site_visit_gbp"]),
                       "VENDOR:VEN-01#fees.site_visit_gbp", where=(2, 2)),
                     F("needle", "Brackenfield major-loss hourly rate £145.", gbp(fees["major_loss_hourly_gbp"]),
                       "VENDOR:VEN-01#fees.major_loss_hourly_gbp", where=(3, 2))])
    doc.p("Invoices are submitted electronically through the vendor invoice interface and matched against the "
          "instruction before payment. Invoices that cannot be matched are returned to the Supplier with the reason.")
    doc.p(pr.para("vendor", n=3))

    # 6 -----------------------------------------------------------------------------------
    doc.h(1, "6. Schedule 3 – Requirements by claim type", page_break=True)
    doc.p("This Schedule describes what Corvane expects to see in reports for each claim type in scope. It does not "
          "change the cover provided by the policy, which is determined by the policy wording applicable to the claim.")
    uk_ct = ["CT-COL", "CT-THF", "CT-WSC", "CT-FIR", "CT-EOW", "CT-STM", "CT-FLD", "CT-SUB", "CT-ACD", "CT-VAN", "CT-BIN"]
    generic = [
        "the cause of loss as established at inspection, distinguished from the cause reported at notification",
        "a scope of works or repair method with itemised costs",
        "photographs of the damage, the surrounding area and any identifying features",
        "observations on policy liability for the Claims Handler to consider, without making a coverage decision",
        "any indication of recovery potential against a third party",
        "any circumstances that suggest the claim should be reviewed by the Special Investigations Unit",
        "the recommended case reserve and the basis for it",
        "details of any emergency or mitigation work authorised at the visit",
    ]
    rng = util.rng("LD030:ct")
    for i, ct in enumerate(uk_ct, 1):
        c = W.claim_types[ct]
        doc.h(2, f"6.{i} {c['name']} ({c['peril_code']})")
        items = rng.sample(generic, 4)
        doc.p(f"For {c['name'].lower()} claims, the report must include " + "; ".join(items[:-1]) + "; and " + items[-1] + ".")
        extra = []
        if ct == "CT-WSC":
            v = ctx.rule("BR-ASM-001")
            extra.append(f"{v['text']} (BR-ASM-001). Site visits for windscreen claims are not chargeable unless pre-authorised.")
        if ct == "CT-EOW" and ctx.rule("BR-ASM-003"):
            v = ctx.rule("BR-ASM-003")
            extra.append(f"{v['text']} (BR-ASM-003 v{v['version']}). Where a video assessment is used it is charged as a desk assessment.")
        if ct in ("CT-EOW", "CT-FIR", "CT-STM", "CT-FLD", "CT-SUB"):
            v = ctx.rule("BR-ASM-002")
            extra.append(f"{v['text']} (BR-ASM-002).")
        for e in extra:
            doc.p(e)
        doc.p(pr.para(["vendor", "governance"], n=(2, 3)))

    # 7 -----------------------------------------------------------------------------------
    doc.h(1, "7. Schedule 4 – Management information")
    doc.p("Brackenfield shall provide an MI Pack each month covering the measures below. The MI Pack is reviewed at the "
          "service review meeting and forms the basis for any Service Credits.")
    mi = [["MI1", "Instructions received, accepted and declined", "Count by product and claim type"],
          ["MI2", "Service Level attainment", "SL1, SL2 and SL3 attainment with exceptions listed"],
          ["MI3", "Open instructions by age", "Age bands in Business Days"],
          ["MI4", "Report quality", "Reports returned for rework, with reasons"],
          ["MI5", "Photo standard", "Reports below the photo minimum in BR-ASM-004"],
          ["MI6", "Complaints", "Complaints relating to Brackenfield staff or reports"],
          ["MI7", "Major-loss hours", "Hours charged by claim for Tier-3 work"],
          ["MI8", "Invoices", "Invoices submitted, matched and rejected"]]
    doc.table(["Ref", "Measure", "Content"], mi, widths=[1.5, 6.5, 8.6], caption="MI Pack contents")
    doc.ps(pr.paras("vendor", 2))

    # 8 -----------------------------------------------------------------------------------
    doc.h(1, "8. Schedule 5 – Governance and escalation")
    contacts = [["Corvane", ctx.name("P033"), ctx.title("P033"), "Schedule owner; escalation level 2"],
                ["Corvane", ctx.name("P039"), ctx.title("P039"), "Property claims operational contact"],
                ["Corvane", ctx.name("P022"), ctx.title("P022"), "Motor claims operational contact (Leeds)"],
                ["Corvane", ctx.name("P030"), ctx.title("P030"), "Tier-3 and major-loss instructions"],
                ["Corvane", ctx.name("P011"), ctx.title("P011"), "Escalation level 3"],
                ["Brackenfield", W.name_of("P057", date), W.title_of("P057", date), "Supplier relationship owner"]]
    doc.table(["Party", "Name", "Title", "Role under this Schedule"], contacts, widths=[2.6, 3.8, 5.2, 5.0],
              caption="Contacts",
              facts=[F("general", "Colin Rudd is Brackenfield's Client Director and supplier relationship owner.",
                       W.name_of("P057", date), "PERSON:P057", where=(6, 1)),
                     F("alias_use", "The Corvane Motor Claims Team Leader Callum Fairbairn (Leeds) is the motor operational contact.",
                       "Motor claims operational contact (Leeds)", "PERSON:P022", where=(3, 3))])
    doc.p("Operational issues are raised first with the relevant operational contact. Issues not resolved within a "
          "reasonable period are escalated to the Schedule owner and then to the Head of Claims Operations UK.")
    doc.ps(pr.paras(["vendor", "governance"], 2))

    # 9 -----------------------------------------------------------------------------------
    doc.h(1, "9. Schedule 6 – Service credits and remediation")
    doc.p("Where a Service Level is missed in a month, Corvane may apply a Service Credit as set out in the Panel "
          "Services Agreement. Service Credits are not an exclusive remedy and do not limit Corvane's other rights.")
    doc.p("Where performance falls below a Service Level in consecutive months, Brackenfield shall provide a "
          "remediation plan describing the cause, the corrective actions and the expected date of recovery.")
    doc.ps(pr.paras("vendor", 3))

    # 10 ----------------------------------------------------------------------------------
    doc.h(1, "10. Schedule 7 – Information security and data protection")
    doc.p(f"Brackenfield acts as a processor of personal data on behalf of Corvane. Data protection queries are "
          f"directed to Corvane's Data Protection Officer, {ctx.name('P019')}.")
    doc.ps(pr.paras("security", 2))
    doc.ps(pr.paras("vendor", 1))

    # 11 ----------------------------------------------------------------------------------
    doc.h(1, "11. Execution", page_break=True)
    doc.p(f"This Schedule is signed on behalf of the parties on {long_date(date)} and takes effect on that date.")
    sig = [["For Corvane Mutual Insurance Society Limited", ctx.name("P033"), ctx.title("P033"), short_date(date)],
           ["For Corvane Mutual Insurance Society Limited", ctx.name("P011"), ctx.title("P011"), short_date(date)],
           ["For Brackenfield Loss Adjusting Ltd", W.name_of("P057", date), W.title_of("P057", date), short_date(date)]]
    doc.table(["Party", "Name", "Title", "Date"], sig, widths=[5.6, 3.8, 4.8, 2.4], caption="Signatures",
              facts=[F("general", "The schedule is signed for Corvane by Rob Tennant, Head of Claims Operations UK (title as at 2025-04-01).",
                       "Head of Claims Operations UK", "PERSON:P011#titles", where=(2, 2))])
    doc.p("Signed electronically. Original signatures are held by Corvane Vendor Management.", italic=True)
    return doc
