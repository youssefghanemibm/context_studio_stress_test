"""Document-style filler .txt files: IVR / contact-centre scripts, call notes, ops handovers and a
printed log excerpt. No new world facts: only non-exclusive facts true on each file's date.
"""
from __future__ import annotations

from generators.common import util

from .common import D, W, Facts, TextDoc, out_path, name, title, long_date, short_date, assert_may


def _doc(fid, slug, facts):
    return TextDoc(fid, out_path(fid, slug, "txt"), facts)


def _control(doc: TextDoc, *, title_: str, ref: str, version: str, d, owner: str, approver: str | None,
             history: list[tuple], audience: str = "Internal", extra: list[str] = ()):
    doc.add("CORVANE MUTUAL INSURANCE SOCIETY LIMITED")
    doc.add(title_.upper())
    doc.add("=" * 88)
    doc.add(f"Document reference : {ref}")
    doc.add(f"Version            : {version}")
    doc.add(f"Date               : {short_date(d)}")
    doc.add(f"Owner              : {name(owner, d)}, {title(owner, d)}")
    if approver:
        doc.add(f"Approved by        : {name(approver, d)}, {title(approver, d)}")
    doc.add(f"Classification     : {audience}")
    for e in extra:
        doc.add(e)
    doc.add("")
    doc.add("Version history")
    for v, vd, who, chg in history:
        doc.add(f"  {v:<6} {vd:<11} {who:<20} {chg}")
    doc.add("=" * 88)
    doc.add("")


def _end(doc: TextDoc, d, owner):
    doc.add("")
    doc.add("-" * 88)
    doc.add(f"End of document. Owner: {name(owner, d)}. Printed copies are uncontrolled.")


# =============================================================================================
def tx021(facts: Facts):
    fid, d = "TX021", D("2026-07-06")
    for ref, f in [("RULE:BR-FNOL-001@v3", "text"), ("RULE:BR-TRI-003@v3", "text"), ("VENDOR:VEN-04", None),
                   ("SYSTEM:SYS04", None), ("SYSTEM:SYS12", None)]:
        assert_may(fid, ref, f)
    r = util.rng(f"{fid}:v")
    doc = _doc(fid, "ivr_script_motor_fnol_uk", facts)
    _control(doc, title_="IVR and agent script - Motor claims UK (new claims line)", ref="CC-SCR-MOT-UK-003",
             version="3.2", d=d, owner="P029", approver="P011",
             history=[("3.0", "2025-11-03", "E. Strachan", "Digital hand-off to MyCorvane Claims added"),
                      ("3.1", "2026-04-01", "E. Strachan", "Guidance on 'additional checks' letters cross-referenced"),
                      ("3.2", "2026-07-06", "E. Strachan", "Acknowledgement wording updated (BR-FNOL-001 v3)")],
             extra=["Applies to      : Glasgow Contact Centre, motor claims queue (Harbour CRM)"])
    doc.add("1. IVR PROMPTS")
    doc.add("")
    prompts = [
        ("IVR-01", "Welcome", "Thank you for calling Corvane Mutual claims. Calls may be recorded for training and quality purposes."),
        ("IVR-02", "Emergency", "If anyone is in immediate danger, please hang up and call the emergency services."),
        ("IVR-03", "Main menu", "To report a new motor claim, press 1. For an existing claim, press 2. For windscreen damage only, press 3. For anything else, please hold."),
        ("IVR-04", "Digital offer", "Did you know you can report a claim at any time using MyCorvane Claims? To receive a link by email, press 9."),
        ("IVR-05", "Queue", "Thank you for waiting. One of our claims team will be with you shortly."),
        ("IVR-06", "Windscreen", "For windscreen damage, we will pass your details to our approved windscreen partner, who will contact you to arrange a repair or replacement."),
        ("IVR-07", "Out of hours", "Our phone lines are closed. You can report your claim now using MyCorvane Claims, or call back when we are open."),
    ]
    for code, label, text in prompts:
        doc.add(f"  [{code}] {label}")
        doc.add(f"      \"{text}\"")
    doc.add("")
    doc.add("2. AGENT SCRIPT - NEW MOTOR CLAIM")
    doc.add("")
    steps = [
        ("Opening", ["\"Good morning / afternoon, you're through to Corvane Mutual claims, my name is ... How can I help?\"",
                     "Confirm the caller is the policyholder or an authorised person before discussing the policy."]),
        ("Identify the policy", ["Search Harbour CRM by policy number, registration or postcode.",
                                 "If the policy cannot be found, take the caller's details and tell them a handler will call back."]),
        ("What happened", ["Ask the caller to describe the incident in their own words. Do not lead.",
                           "Record date, time and location of the incident, and where the vehicle is now.",
                           "Ask whether the police attended and record any reference number."]),
        ("Injuries", ["Ask: \"Was anyone hurt, even slightly?\"",
                      "If anyone was injured, record it on the claim. Any bodily injury makes the claim Tier-3, so make sure the injury details are complete; do not promise timescales on the call."]),
        ("Other parties", ["Record the other driver's details, vehicle and insurer if known.",
                           "If the caller does not have them, reassure them that the handler will follow up."]),
        ("Repairs", ["Offer repair through the approved repair network (Thistlecombe Repair Network) and explain the benefits.",
                     "If the customer prefers their own repairer, note it; the handler will confirm what is covered."]),
        ("Evidence", ["Offer to send a secure upload link by email for photos.",
                      "Customers using MyCorvane Claims can upload photos there instead."]),
        ("Closing", ["Give the claim reference and read it back.",
                     "Telephone claims are acknowledged in writing within 2 business days; claims made through MyCorvane Claims or the app are acknowledged within 1 business day.",
                     "\"Is there anything else I can help you with today?\""]),
    ]
    ack_line = None
    for i, (head, items) in enumerate(steps, 1):
        doc.add(f"  2.{i} {head}")
        for it in items:
            n = doc.add(f"      - {it}")
            if it.startswith("Telephone claims are acknowledged"):
                ack_line = n
        doc.add("")
    doc.fact(ack_line, needle="Telephone claims are acknowledged in writing within 2 business days", kind="general",
             world_ref="RULE:BR-FNOL-001@v3",
             statement="BR-FNOL-001 v3 (from 2026-07-01): telephone FNOLs are acknowledged within 2 business days, digital within 1 business day.")
    doc.add("3. THINGS NOT TO SAY")
    for it in ["Never mention fraud scoring, Sentinel or SIU to a customer.",
               "Never tell a customer whether their claim will be paid; the handler decides once the facts are known.",
               "Never give a repair cost estimate on the call.",
               "Never ask for bank details on the new claims line; payment details are collected by the handler."]:
        doc.add(f"  - {it}")
    doc.add("")
    doc.add("4. CALL WRAP CODES (HARBOUR CRM)")
    codes = ["NEWCLM-MOT  New motor claim registered", "NEWCLM-WSC  Windscreen only, passed to partner",
             "INFO-ONLY   Caller wanted information, no claim", "CALLBK      Callback requested",
             "TRANSFER    Transferred to existing-claims queue"]
    for c in codes:
        doc.add(f"  {c}")
    _end(doc, d, "P029")
    return doc


# =============================================================================================
def tx022(facts: Facts):
    fid, d = "TX022", D("2025-11-17")
    for ref, f in [("RULE:BR-FNOL-001@v2", "text"), ("VENDOR:VEN-06", None), ("VENDOR:VEN-01", None),
                   ("SYSTEM:SYS05", "renames")]:
        assert_may(fid, ref, f)
    doc = _doc(fid, "ivr_script_home_escape_of_water", facts)
    _control(doc, title_="Agent script - Home claims: escape of water", ref="CC-SCR-HOM-UK-007", version="2.4", d=d,
             owner="P029", approver="P011",
             history=[("2.2", "2024-10-14", "E. Strachan", "Portal name updated to MyCorvane Claims"),
                      ("2.3", "2025-09-01", "E. Strachan", "Approver changed after the re-organisation"),
                      ("2.4", "2025-11-17", "E. Strachan", "Photo upload wording updated after the document store rename")],
             extra=["Applies to      : Glasgow Contact Centre, home claims queue"])
    sections = [
        ("1. MAKE SAFE FIRST", [
            "\"Before we go any further, is the water still running? Do you know where your stopcock is?\"",
            "If water is near electrics, advise the customer not to touch switches and to call an electrician if needed.",
            "If the customer is vulnerable or the home is uninhabitable, flag the claim as priority and tell the team leader.",
        ]),
        ("2. ABOUT THE LEAK", [
            "Ask where the water came from (for example a pipe, tank, appliance or the floor above).",
            "Ask when it was first noticed and whether it happened suddenly or has been going on for a while.",
            "Record what is damaged: ceilings, walls, floors, contents.",
            "Do not tell the customer whether the damage is covered. The handler and, where needed, a Claims Assessor will look at that.",
        ]),
        ("3. DRYING AND REPAIRS", [
            "Explain that we may arrange drying through our repair network (Kilnmoor Property Repairs).",
            "If a visit is needed, a Claims Assessor will be appointed. This may be one of our own assessors or a loss adjuster from Brackenfield.",
        ]),
        ("4. PHOTOS AND EVIDENCE", [
            "Ask the customer to take photos of the damage and of the source of the leak, if it is safe to do so.",
            "Photos uploaded through MyCorvane Claims are stored with the claim automatically.",
            "Advise the customer to keep any damaged items until the handler confirms they can be thrown away.",
        ]),
        ("5. CLOSING", [
            "Give the claim reference and read it back.",
            "We acknowledge every new claim in writing within 2 business days.",
            "Explain that the excess shown on the policy schedule applies, without quoting an amount.",
        ]),
    ]
    ack = None
    for head, items in sections:
        doc.add(head)
        for it in items:
            n = doc.add(f"  - {it}")
            if it.startswith("We acknowledge every new claim"):
                ack = n
        doc.add("")
    doc.fact(ack, needle="We acknowledge every new claim in writing within 2 business days", kind="general",
             world_ref="RULE:BR-FNOL-001@v2",
             statement="In November 2025 (BR-FNOL-001 v2) every FNOL is acknowledged within 2 business days.")
    doc.add("6. GLOSSARY FOR AGENTS")
    for t_, dsc in [("Escape of water", "Water escaping from a fixed system or appliance."),
                    ("Claims Assessor", "The person who inspects the damage; customers often say 'loss adjuster'."),
                    ("Excess", "The amount the customer pays towards a claim, shown on the schedule."),
                    ("Make safe", "Immediate steps to stop further damage.")]:
        doc.add(f"  {t_:<18} {dsc}")
    _end(doc, d, "P029")
    return doc


# =============================================================================================
def tx023(facts: Facts):
    fid, d = "TX023", D("2026-10-16")
    r = util.rng(f"{fid}:calls")
    doc = _doc(fid, "call_notes_contact_centre_quality_review_2026_10", facts)
    _control(doc, title_="Call quality review notes - Glasgow Contact Centre (week ending 16 Oct 2026)",
             ref="CC-QA-2026-W42", version="1.0", d=d, owner="P029", approver=None,
             history=[("1.0", "2026-10-16", "E. Strachan", "Weekly sample of calls reviewed")],
             extra=["Scope           : random sample of recorded calls; customer details removed"])
    doc.add("HOW TO READ THESE NOTES")
    doc.add("  Each call is scored against the standard checklist: greeting, identification, empathy, accuracy,")
    doc.add("  wrap-up. Customer details have been removed; claim references are masked.")
    doc.add("")
    call_types = [
        ("New motor claim", ["Clear opening and good empathy after a stressful accident.",
                             "Injury question asked at the right point and recorded on the claim.",
                             "Repair network offered; customer accepted.",
                             "Claim reference read back correctly."]),
        ("Existing motor claim - progress chase", ["Agent found the claim quickly on the Hub screens.",
                                                   "Explained next steps without promising a date.",
                                                   "Could have summarised at the end."]),
        ("Home - escape of water", ["Make-safe advice given first, as per script.",
                                    "Agent avoided giving a view on cover, correctly.",
                                    "Upload link offered for photos."]),
        ("Query about an 'additional checks' letter", ["Agent followed the script and did not discuss fraud checks.",
                                                       "Customer calmed by the explanation that checks are routine.",
                                                       "Callback logged for the handler."]),
        ("Windscreen only", ["Passed to the windscreen partner correctly.", "Short, efficient call."]),
        ("Payment query", ["Agent checked the payment status and explained it clearly.",
                           "Transferred to Payments Operations appropriately when the customer asked about a bank change."]),
        ("Complaint about delays", ["Agent acknowledged the frustration and logged the complaint correctly.",
                                    "Escalated to the team leader as required."]),
        ("Broker calling on behalf of a client", ["Authority checked before details were shared.",
                                                  "Agent used plain language."]),
    ]
    marks = ["Met", "Met", "Met", "Partly met", "Met", "Exceeded"]
    for i in range(1, 15):
        ct, obs = call_types[r.randrange(len(call_types))]
        ref = f"CLM-UK-2026-****{r.randint(10, 99)}"
        doc.add(f"CALL {i:02d}  |  {ct}  |  claim ref {ref}  |  agent GLA-{r.randint(100, 999)}")
        sel = list(obs)
        r.shuffle(sel)
        for o in sel[: r.randint(2, len(sel))]:
            doc.add(f"    - {o}")
        doc.add("    Checklist: " + ", ".join(f"{k} {r.choice(marks)}" for k in
                                                ("greeting", "identification", "empathy", "accuracy", "wrap-up")))
        doc.add("")
    doc.add("THEMES THIS WEEK")
    for th in ["Agents are more confident on the Claims Hub screens for motor claims than a month ago.",
               "Wrap-up summaries are the most common gap. Team leaders to coach in huddles.",
               "The 'additional checks' script is being followed well. No agent discussed fraud checks with a customer.",
               "Hold times on the existing-claims queue were longer on Monday mornings."]:
        doc.add(f"  - {th}")
    _end(doc, d, "P029")
    return doc


# =============================================================================================
def tx024(facts: Facts):
    fid, d = "TX024", D("2026-10-14")
    for ref, f in [("INCIDENT:INC-2026-0518", "workaround"), ("TICKET:CHUB-395", None), ("TICKET:CHUB-298", None)]:
        assert_may(fid, ref, f)
    r = util.rng(f"{fid}:jobs")
    import yaml
    jobs = yaml.safe_load((util.ROOT / "world/data/jcl_jobs.yaml").read_text(encoding="utf-8"))["jcl_jobs"]
    doc = _doc(fid, "ops_handover_mainframe_batch_2026_10_14", facts)
    _control(doc, title_="Shift handover - Mainframe Batch Operations (night shift 14/15 Oct 2026)",
             ref="OPS-HND-2026-10-14N", version="1.0", d=d, owner="P026", approver=None,
             history=[("1.0", "2026-10-14", "S. Vaghela", "Night shift handover")],
             extra=["Team            : Mainframe Batch Operations, Leeds (scheduler: Batch Scheduler)"])
    doc.add("1. SUMMARY")
    doc.add("  Night batch completed normally. No abends. No reruns. All return codes 0000 unless shown.")
    doc.add("")
    doc.add("2. JOB STATUS")
    doc.add(f"  {'Job':<10} {'Description':<48} {'Status':<14} RC")
    for j in jobs:
        if j["status"] != "active":
            continue
        if j["name"].startswith(("CLRM", "CLRQ", "CLRY")):
            continue
        if j["name"].startswith("CLRW") and r.random() < 0.6:
            continue
        doc.add(f"  {j['name']:<10} {j['description'][:48]:<48} {'Completed':<14} 0000")
    doc.add("")
    doc.add("  Not scheduled tonight: monthly, quarterly and year-end jobs; disabled job CLRNFR99 (auto-decline sweep).")
    doc.add("  Retired: CLRDRSV9 (reserve parallel-run reconciliation), retired at the end of the parallel run.")
    doc.add("")
    doc.add("3. STANDING NOTES")
    n = doc.add("  - CLRNFR01 includes the CLRFR040 sweep, which still has the old threshold hard-coded until CHUB-298 is released.")
    doc.fact(n, needle="CLRFR040 sweep, which still has the old threshold hard-coded until CHUB-298 is released", kind="general",
             world_ref="TICKET:CHUB-298",
             statement="As at mid-October 2026, the CLRFR040 sweep (in job CLRNFR01) still has the old threshold hard-coded until CHUB-298 is released.")
    n = doc.add("    Compliance continue their daily query for unreferred claims (65-69, and 60-64 for Tier-3 since 1 October).")
    doc.fact(n, needle="daily query for unreferred claims (65-69, and 60-64 for Tier-3 since 1 October)", kind="general",
             world_ref="INCIDENT:INC-2026-0518#workaround",
             statement="Compliance's daily query covers unreferred claims scoring 65-69, and 60-64 for Tier-3 claims from 2026-10-01.")
    doc.add("    No action for Ops; do not raise an incident for this.")
    doc.add("  - The Tier-3 threshold parameter FRD_REFER_T3_THRESH has been in CLR.T_PARAM since 1 October (CHUB-395).")
    doc.add("  - UK motor claims are on Claims Hub since Wave 1 (14 September).")
    doc.add("")
    doc.add("4. HANDOVER CHECKS")
    for c in ["Scheduler console clear of alerts at handover.", "Spool housekeeping done.",
              "Dataset space checked; no warnings.", "Incident queue checked: nothing open for Batch Operations.",
              "Change calendar checked: no changes tonight."]:
        doc.add(f"  [x] {c}")
    doc.add("")
    doc.add("  Handed over by: Night shift (S. Vaghela's team)   Received by: Day shift")
    _end(doc, d, "P026")
    return doc


# =============================================================================================
def tx027(facts: Facts):
    fid, d = "TX027", D("2026-06-11")
    for ref, f in [("DECISION:DEC-019", None), ("SYSTEM:SYS17", "renames"), ("TICKET:CHUB-340", None),
                   ("VENDOR:VEN-03", "panel_to")]:
        assert_may(fid, ref, f)
    doc = _doc(fid, "call_notes_brackenfield_monthly_2026_06", facts)
    _control(doc, title_="Call notes - Brackenfield Loss Adjusting monthly account call (June 2026)",
             ref="ASM-VEN-BLA-2026-06", version="1.0", d=d, owner="P033", approver=None,
             history=[("1.0", "2026-06-11", "I. Talwar", "Notes of the monthly call")],
             extra=["Attendees       : Imran Talwar (Corvane), Kirsty Mowbray (Corvane), Colin Rudd (Brackenfield)"])
    items = [
        ("Open instructions transferred from Fellgate",
         ["Fellgate Adjusting Partners left the assessor panel on 31 January 2026; their open instructions moved to Brackenfield at that point.",
          "Colin confirmed the transferred files are all now allocated to named loss adjusters.",
          "Kirsty asked for the major-loss files to keep the same adjuster through to settlement where possible."]),
        ("Assessor Portal",
         ["Brackenfield adjusters are using the Assessor Portal for instructions and reports. No access issues this month.",
          "Colin asked whether the portal will change when assessment moves to Claims Hub. Imran: the portal stays; the appointment API behind it is being built."]),
        ("Claims Hub appointment API",
         ["Corvane explained that the Claims Assessor appointment API (assessment-svc) is in development for Wave 1.",
          "Brackenfield will be invited to test with sample instructions before go-live."]),
        ("Report quality",
         ["Imran thanked Brackenfield for the improvement in report turnaround.",
          "Two reports this month needed resubmission for missing photographs. Colin will remind the adjusters."]),
        ("AOB", ["Next call in July. Colin to send the account summary in advance."]),
    ]
    for i, (head, pts) in enumerate(items, 1):
        doc.add(f"{i}. {head}")
        for p in pts:
            n = doc.add(f"   - {p}")
            if p.startswith("Fellgate Adjusting Partners left"):
                doc.fact(n, needle="Fellgate Adjusting Partners left the assessor panel on 31 January 2026", kind="general",
                         world_ref="DECISION:DEC-019",
                         statement="Fellgate Adjusting Partners left the assessor panel on 2026-01-31; open instructions moved to Brackenfield.")
        doc.add("")
    doc.add("Actions")
    for a in ["Colin Rudd: remind adjusters about photograph requirements.",
              "Imran Talwar: confirm test dates for the appointment API with the squad.",
              "Kirsty Mowbray: share the list of major-loss files that should keep the same adjuster."]:
        doc.add(f"  - {a}")
    _end(doc, d, "P033")
    return doc


# =============================================================================================
def _k8s_namespace(svc: str, d) -> str:
    """Kubernetes namespace of a service as of ``d`` (services.yaml path_history, else k8s_namespace)."""
    s = W.services[svc]
    for h in s.get("path_history") or []:
        if h.get("k8s_namespace") and D(str(h["to"])) >= d:
            return h["k8s_namespace"]
    return s["k8s_namespace"]


def tx028(facts: Facts):
    fid, d = "TX028", D("2026-08-27")
    for ref, f in [("TOPIC:claims.reserve.movement.v1", "name"), ("TICKET:CHUB-241", None), ("TOPIC:reserve.changed.v2", "name")]:
        assert_may(fid, ref, f)
    r = util.rng(f"{fid}:log")
    doc = _doc(fid, "printed_log_excerpt_reserve_engine_2026_08_27", facts)
    products = ["PRD-MOT-UK", "PRD-HOM-UK", "PRD-COM-UK", "PRD-LIA-UK", "PRD-MOT-NO", "PRD-HOM-NO", "PRD-MOT-SE",
                "PRD-HOM-SE", "PRD-MOT-DK", "PRD-HOM-DK"]
    lines_per_page = 54
    body = []
    t = 4 * 3600 + 30 * 60 + r.randint(0, 59)

    def ts():
        nonlocal t
        t += r.randint(0, 3) + r.random()
        h, rem = divmod(int(t), 3600)
        mi, s = divmod(rem, 60)
        ms = int((t % 1) * 1000)
        return f"2026-08-27 {h:02d}:{mi:02d}:{s:02d}.{ms:03d}"

    def log(level, thread, logger, msg):
        body.append(f"{ts()} {level:<5} [{thread}] {logger} - {msg}")

    log("INFO", "main", "c.c.r.ReconciliationJob", "Starting parallel-run reconciliation for businessDate=2026-08-26")
    log("INFO", "main", "c.c.r.ReconciliationJob", "Comparing CLARA outstanding reserves with reserve-engine outstanding reserves")
    log("INFO", "main", "c.c.r.MovementReplay", "Replaying movements from topic claims.reserve.movement.v1 for businessDate=2026-08-26")
    for k in range(r.randint(10, 14)):
        log("DEBUG", f"replay-{k % 4}", "c.c.r.MovementReplay", f"Batch {k + 1} consumed, size={r.choice([250, 500])}, lagMs={r.randint(12, 240)}")
    log("INFO", "main", "c.c.r.MovementReplay", "Replay complete")
    for p in products:
        log("INFO", "recon-1", "c.c.r.ProductComparator", f"Comparing outstanding reserves product={p}")
        for k in range(r.randint(2, 4)):
            log("DEBUG", "recon-1", "c.c.r.ProductComparator",
                f"product={p} chunk={k + 1} durationMs={r.randint(300, 2400)}")
        status = "WITHIN_TOLERANCE"
        log("INFO", "recon-1", "c.c.r.ProductComparator", f"product={p} status={status}")
    log("INFO", "main", "c.c.r.ReportWriter", "Writing reconciliation report for the daily review")
    log("WARN", "main", "c.c.r.ReportWriter", "Report adapter responded slowly (retry 1 of 3) - succeeded on retry")
    log("INFO", "main", "c.c.r.ReconciliationJob", "Reconciliation finished for businessDate=2026-08-26: all products within tolerance")
    log("INFO", "main", "c.c.r.ReconciliationJob", "Note: parallel run final business day is 2026-08-28 (CHUB-241)")
    pages = [body[i:i + lines_per_page] for i in range(0, len(body), lines_per_page)]
    svc_name, ns = W.service_name("reserve-engine", d), _k8s_namespace("reserve-engine", d)
    for pi, page in enumerate(pages, 1):
        doc.add(f"REPRINT  {svc_name} application log (namespace {ns})        Page {pi} of {len(pages)}")
        doc.add("Printed 2026-08-27 for the parallel-run review pack - extract only - Internal")
        doc.add("-" * 110)
        for ln in page:
            n = doc.add(ln)
            if "final business day is 2026-08-28" in ln:
                doc.fact(n, needle="parallel run final business day is 2026-08-28", kind="general", world_ref="TICKET:CHUB-241",
                         statement="The reserve parallel run's final business day was 2026-08-28.")
        doc.add("-" * 110)
        doc.add("")
    doc.add("Annotation (handwritten on the original, transcribed): 'all green again - attach to review pack, D.A.'")
    return doc


# =============================================================================================
def tx029(facts: Facts):
    fid, d = "TX029", D("2026-04-01")
    for ref, f in [("RULE:BR-FRD-032@v2", "text"), ("RULE:BR-FRD-033@v1", "text"), ("CIRCULAR:CIRC-2026-04", "title")]:
        assert_may(fid, ref, f)
    doc = _doc(fid, "contact_centre_script_additional_checks_letters", facts)
    _control(doc, title_="Agent guidance - customer calls about 'additional checks' letters", ref="CC-SCR-GEN-021",
             version="1.0", d=d, owner="P029", approver="P037",
             history=[("0.9", "2026-03-20", "E. Strachan", "Draft for Compliance review"),
                      ("1.0", "2026-04-01", "E. Strachan", "Issued for go-live of the new letters")],
             extra=["Background      : NISA Circular 2026/04 (Fair Treatment in Fraud Referral), effective 1 April 2026"])
    doc.add("WHY CUSTOMERS ARE CALLING")
    n = doc.add("  From 1 April 2026 we write to customers within 10 business days when their claim is selected for additional checks.")
    doc.fact(n, needle="within 10 business days when their claim is selected for additional checks", kind="general",
             world_ref="RULE:BR-FRD-032@v2",
             statement="BR-FRD-032 v2: customers are notified in writing within 10 business days of a fraud referral (unless deferred).")
    doc.add("  Some customers will be worried by the letter. Your job is to reassure them, not to explain the checks.")
    doc.add("")
    doc.add("WHAT TO SAY")
    for s in ["\"Thank you for calling. I can see the letter you've received. These checks are a normal part of how we handle some claims.\"",
              "\"It doesn't mean we've made any decision about your claim.\"",
              "\"Your handler will contact you if they need anything else from you.\""]:
        doc.add(f"  - {s}")
    n = doc.add("  - If asked: \"No decision on a claim is ever made on an automated check alone. A person always reviews it.\"")
    doc.fact(n, needle="No decision on a claim is ever made on an automated check alone", kind="general",
             world_ref="RULE:BR-FRD-033@v1",
             statement="BR-FRD-033: no adverse claim decision is made on an automated fraud score alone; a human review is required.")
    doc.add("")
    doc.add("WHAT NOT TO SAY")
    for s in ["Do not use the words 'fraud', 'investigation' or 'SIU'.", "Do not mention scores or how claims are selected.",
              "Do not give a date for the outcome of the checks.", "Do not transfer the call to the SIU team."]:
        doc.add(f"  - {s}")
    doc.add("")
    doc.add("RECORDING THE CALL")
    doc.add("  Log the call in Harbour CRM with wrap code ADDCHK-QUERY and add a short note for the handler.")
    doc.add("  If the customer wants to complain, log a complaint in the usual way and tell your team leader.")
    _end(doc, d, "P029")
    return doc


# =============================================================================================
def tx030(facts: Facts):
    fid, d = "TX030", D("2026-09-16")
    for ref, f in [("INCIDENT:INC-2026-0914", "impact"), ("TICKET:CHUB-371", None), ("ADR:ADR-021", None),
                   ("WAVE:MW-1", "date")]:
        assert_may(fid, ref, f)
    doc = _doc(fid, "ops_handover_wave1_hypercare_day3", facts)
    _control(doc, title_="Wave 1 hypercare - shift handover, day 3 (Wednesday 16 September 2026)", ref="W1-HYP-HND-D3",
             version="1.0", d=d, owner="P048", approver=None,
             history=[("1.0", "2026-09-16", "A. Kesavan", "Evening handover to the overnight hypercare cover")],
             extra=["Distribution    : hypercare leads, squad leads, Claims Operations duty manager"])
    doc.add("1. OVERALL STATUS")
    doc.add("  UK motor has been live on Claims Hub since Monday 14 September. Handlers are working claims end to end.")
    doc.add("  No Sev 1 incidents open. Defect triage continues each morning with the squads and business leads.")
    doc.add("")
    doc.add("2. INCIDENTS")
    n = doc.add("  INC-2026-0914 (Sev 2): duplicate payment instructions on cut-over Monday - 18 claims paid twice, £41,236.50 in total.")
    doc.fact(n, needle="18 claims paid twice, £41,236.50 in total", kind="general", world_ref="INCIDENT:INC-2026-0914#impact",
             statement="INC-2026-0914: 18 claims paid twice on the Wave 1 cut-over Monday, £41,236.50 in total.")
    doc.add("    Cause: payment-orchestrator retried after a timeout from the payments gateway without an idempotency key.")
    n = doc.add("    Fix: CHUB-371 deployed today. ADR-021 (idempotency keys for all payment instructions) accepted today.")
    doc.fact(n, needle="CHUB-371 deployed today", kind="general", world_ref="TICKET:CHUB-371",
             statement="The fix for the Wave 1 duplicate payments (CHUB-371) was deployed on 2026-09-16, the day ADR-021 was accepted.")
    doc.add("    Recovery: Payments Operations have issued recall requests for every duplicate. Recalls are being tracked daily.")
    doc.add("")
    doc.add("3. WATCH ITEMS FOR TONIGHT")
    for w in ["Overnight payment batch: Payments Operations duty contact to confirm there are no duplicate instructions.",
              "Claims Hub queues: check the triage and assessment queues are draining as expected.",
              "Evidence uploads: check document-svc is storing documents normally.",
              "Any new Sev 2: call the hypercare lead on the duty phone; do not wait for the morning call."]:
        doc.add(f"  - {w}")
    doc.add("")
    doc.add("4. CONTACTS (DUTY ROTA)")
    doc.add("  Hypercare lead: on the duty phone (see the rota).  Payments Operations: duty contact on the rota.")
    doc.add("  Integration: on-call via the service desk.  CLARA: on-call via the service desk.")
    _end(doc, d, "P048")
    return doc


# =============================================================================================
def tx062(facts: Facts):
    fid, d = "TX062", D("2026-07-09")
    for ref, f in [("VENDOR:VEN-02", "role"), ("SYSTEM:SYS17", None), ("WAVE:MW-2", "scope")]:
        assert_may(fid, ref, f)
    doc = _doc(fid, "call_notes_norrvik_quarterly_2026_07", facts)
    _control(doc, title_="Call notes - Norrvik Skadetaxering quarterly review (Q2 2026)", ref="ASM-VEN-NSK-2026-Q2",
             version="1.0", d=d, owner="P034", approver=None,
             history=[("1.0", "2026-07-09", "A. Nygaard", "Notes of the quarterly call")],
             extra=["Attendees       : Astrid Nygaard (Corvane), Karl Eriksen (Corvane), Sigrid Nyhus (Norrvik)"])
    items = [
        ("Service review", ["Sigrid summarised the quarter for the Swedish and Norwegian work. No escalations.",
                            "Astrid noted good feedback from the Stockholm handlers on the besiktningsman reports.",
                            "Karl raised two Norwegian motor files where the skadetakstmann report arrived after the repair had started; Sigrid will follow up."]),
        ("Assessor Portal", ["Norrvik assessors use the Assessor Portal for instructions and reports in both countries.",
                             "Sigrid asked for the portal help pages in Swedish. Astrid will raise it with the portal owner."]),
        ("Claims Hub", ["Astrid explained that Norway and Sweden move to Claims Hub in Wave 2, next year.",
                        "Norrvik will be involved in testing the assessor appointment flow before then."]),
        ("Fees", ["Fees were not discussed on this call; they are handled in the annual contract review."]),
        ("AOB", ["Next quarterly call in October."]),
    ]
    for i, (h, pts) in enumerate(items, 1):
        doc.add(f"{i}. {h}")
        for p in pts:
            n = doc.add(f"   - {p}")
            if p.startswith("Astrid explained that Norway and Sweden"):
                doc.fact(n, needle="Norway and Sweden move to Claims Hub in Wave 2", kind="general", world_ref="WAVE:MW-2#scope",
                         statement="Norway and Sweden move to Claims Hub in Wave 2.")
        doc.add("")
    doc.add("Actions")
    for a in ["Sigrid Nyhus: follow up the two late Norwegian reports.", "Astrid Nygaard: ask about Swedish help pages.",
              "Karl Eriksen: send the file references to Sigrid."]:
        doc.add(f"  - {a}")
    _end(doc, d, "P034")
    return doc


# =============================================================================================
def tx063(facts: Facts):
    fid, d = "TX063", D("2025-10-01")
    for ref, f in [("VENDOR:VEN-05", None), ("RULE:BR-FNOL-001@v2", "text")]:
        assert_may(fid, ref, f)
    doc = _doc(fid, "ivr_script_motor_norge", facts)
    _control(doc, title_="IVR- og samtaleskript - Motor Privat Norge / IVR and call script - Motor Norway", ref="CC-SCR-MOT-NO-002",
             version="2.1", d=d, owner="P012", approver="P011",
             history=[("2.0", "2025-03-03", "M. Dahl", "Annual review"),
                      ("2.1", "2025-10-01", "M. Dahl", "Owner and approver updated after the re-organisation")],
             extra=["Applies to      : Oslo claims line, Corvane Mutual Norge (telefon +47 555 01 420)"])
    doc.add("1. IVR")
    for code, no, en in [
        ("IVR-N1", "Takk for at du ringer Corvane Mutual Norge, skadeavdelingen. Samtalen kan bli tatt opp.",
         "Thank you for calling Corvane Mutual Norge, claims. The call may be recorded."),
        ("IVR-N2", "Trykk 1 for å melde en ny bilskade. Trykk 2 for en skade du allerede har meldt. Trykk 3 for glasskade.",
         "Press 1 to report a new motor claim. Press 2 for an existing claim. Press 3 for glass damage."),
        ("IVR-N3", "For English, press 9.", "For English, press 9."),
    ]:
        doc.add(f"  [{code}] NO: \"{no}\"")
        doc.add(f"           EN: \"{en}\"")
    doc.add("")
    doc.add("2. SAMTALESKRIPT / CALL SCRIPT")
    for h, pts in [
        ("Åpning / Opening", ["Hils og presenter deg. Bekreft at innringer er forsikringstaker eller har fullmakt.",
                              "Greet the caller and confirm they are the policyholder or authorised."]),
        ("Hva skjedde? / What happened?", ["Dato, tid, sted, og om politiet var involvert.",
                                           "Date, time, place, and whether the police were involved."]),
        ("Personskade / Injury", ["Spør alltid om noen ble skadet. Personskade registreres på saken.",
                                  "Always ask whether anyone was hurt. Any injury is recorded on the claim."]),
        ("Verksted / Repairs", ["Tilby reparasjon hos et av våre samarbeidsverksteder (Vardholm Bilverksted).",
                                "Offer repair at one of our partner workshops (Vardholm Bilverksted)."]),
        ("Takst / Assessment", ["Ved behov sender vi en skadetakstmann for å se på bilen.",
                                "If needed, we send a Claims Assessor (skadetakstmann) to inspect the vehicle."]),
        ("Egenandel / Excess", ["Egenandelen står i forsikringsbeviset. Ikke oppgi beløp på telefonen.",
                                "The excess (egenandel) is shown on the policy certificate. Do not quote an amount on the call."]),
        ("Avslutning / Closing", ["Gi skadenummeret og les det tilbake. Vi bekrefter skademeldingen skriftlig innen 2 virkedager.",
                                  "Give the claim reference and read it back. We acknowledge the claim in writing within 2 business days."]),
    ]:
        doc.add(f"  {h}")
        for p in pts:
            n = doc.add(f"    - {p}")
            if "within 2 business days" in p:
                doc.fact(n, needle="We acknowledge the claim in writing within 2 business days", kind="general",
                         world_ref="RULE:BR-FNOL-001@v2",
                         statement="In October 2025 (BR-FNOL-001 v2) FNOLs are acknowledged within 2 business days.")
        doc.add("")
    _end(doc, d, "P012")
    return doc


# =============================================================================================
def tx064(facts: Facts):
    fid, d = "TX064", D("2026-09-24")
    for ref, f in [("INCIDENT:INC-2026-0604", None), ("SYSTEM:SYS13", None)]:
        assert_may(fid, ref, f)
    doc = _doc(fid, "ops_handover_contact_centre_2026_09_24", facts)
    _control(doc, title_="Contact centre shift handover - Glasgow (late shift, Thursday 24 September 2026)",
             ref="CC-HND-2026-09-24L", version="1.0", d=d, owner="P029", approver=None,
             history=[("1.0", "2026-09-24", "E. Strachan", "Late shift handover")],
             extra=["Distribution    : early shift team leaders, duty manager"])
    doc.add("1. HEADLINES")
    n = doc.add("  - Photo uploads are delayed. Since about 17:05 the Evidence Intake Gateway has a backlog of photos after the storm; INC-2026-0604 is open.")
    doc.fact(n, needle="the Evidence Intake Gateway has a backlog of photos after the storm", kind="general", world_ref="INCIDENT:INC-2026-0604",
             statement="INC-2026-0604 (2026-09-24, from about 17:05): Evidence Intake Gateway photo backlog after a storm.")
    doc.add("  - Call volumes were higher than usual from mid-afternoon, mostly new home claims (storm damage) and photo queries.")
    doc.add("  - No system outage on Harbour CRM or Claims Hub. Calls are being handled normally apart from the photo delay.")
    doc.add("")
    doc.add("2. WHAT TO TELL CUSTOMERS")
    for s in ["\"We've received your photos and they'll appear on your claim shortly. There's no need to send them again.\"",
              "If a customer has already sent photos twice, reassure them; duplicates are not a problem.",
              "Do not promise a time for the photos to appear."]:
        doc.add(f"  - {s}")
    doc.add("")
    doc.add("3. FOR THE EARLY SHIFT")
    for s in ["Check the incident status on the service desk before the morning huddle.",
              "Brief agents on the photo wording above if the incident is still open.",
              "Expect more storm-related home claims in the morning. Make-safe advice first, as per the home script.",
              "Team leaders: keep an eye on wrap-up times, they crept up this evening."]:
        doc.add(f"  - {s}")
    _end(doc, d, "P029")
    return doc


# =============================================================================================
def tx066(facts: Facts):
    fid, d = "TX066", D("2026-05-19")
    for ref, f in [("RULE:BR-FRD-033@v1", "text"), ("VENDOR:VEN-10", None), ("SYSTEM:SYS22", None),
                   ("RULE:BR-FRD-035@v2", "text")]:
        assert_may(fid, ref, f)
    doc = _doc(fid, "call_notes_greyfold_siu_2026_05", facts)
    _control(doc, title_="Call notes - Greyfold Investigations partner call (May 2026)", ref="SIU-VEN-GFI-2026-05",
             version="1.0", d=d, owner="P028", approver=None,
             history=[("1.0", "2026-05-19", "R. Dunmore", "Notes of the partner call")],
             extra=["Attendees       : Rachel Dunmore (Corvane), Niall Brannigan (Corvane), Declan Furey (Greyfold)"])
    items = [
        ("Changes since 1 April", [
            "Rachel recapped the changes from NISA Circular 2026/04 that affect partner work.",
            "No claim can be declined on an automated score alone; every adverse outcome needs a documented human review by SIU.",
            "SIU now triage new referrals within 3 business days, so instructions to Greyfold may arrive earlier in the life of a claim."]),
        ("Instructions", [
            "All instructions continue to come from SIU Case Manager. Declan confirmed Greyfold will not act on instructions by email alone.",
            "Niall asked that interview reports state clearly what was observed and what was inferred."]),
        ("Customer contact", [
            "Declan asked how the new customer letters affect surveillance timing. Rachel: speak to the investigator on the case before any contact; do not assume the customer has or has not been written to."]),
        ("AOB", ["Next partner call in August."]),
    ]
    for i, (h, pts) in enumerate(items, 1):
        doc.add(f"{i}. {h}")
        for p in pts:
            n = doc.add(f"   - {p}")
            if p.startswith("No claim can be declined"):
                doc.fact(n, needle="No claim can be declined on an automated score alone", kind="general",
                         world_ref="RULE:BR-FRD-033@v1",
                         statement="From 2026-04-01 (BR-FRD-033) no claim can be declined on an automated fraud score alone.")
        doc.add("")
    doc.add("Actions")
    for a in ["Declan Furey: update the report template to separate observation from inference.",
              "Rachel Dunmore: circulate the summary of the Circular changes to Greyfold's team leads."]:
        doc.add(f"  - {a}")
    _end(doc, d, "P028")
    return doc


# =============================================================================================
def tx067(facts: Facts):
    fid, d = "TX067", D("2026-10-01")
    for ref, f in [("SYSTEM:SYS09", None), ("WAVE:MW-1", "scope")]:
        assert_may(fid, ref, f)
    doc = _doc(fid, "ivr_script_payments_enquiries", facts)
    _control(doc, title_="IVR and agent script - Claim payment enquiries", ref="PAY-SCR-ENQ-004", version="4.0", d=d,
             owner="P035", approver="P029",
             history=[("3.3", "2026-02-02", "A. Prothero", "Annual review"),
                      ("4.0", "2026-10-01", "A. Prothero", "Updated after Wave 1: UK motor payments now made from Claims Hub")],
             extra=["Applies to      : payment enquiries queue (Glasgow) with escalation to Payments Operations (Bristol)"])
    doc.add("1. IVR")
    for code, text in [("IVR-P1", "To check on a claim payment, please have your claim reference ready."),
                       ("IVR-P2", "For a motor claim payment, press 1. For a home or business claim payment, press 2."),
                       ("IVR-P3", "If you need to change the bank account for a payment, please stay on the line to speak to an adviser.")]:
        doc.add(f"  [{code}] \"{text}\"")
    doc.add("")
    doc.add("2. AGENT GUIDANCE")
    n = doc.add("  - UK motor claims have been on Claims Hub since Wave 1. Check motor payment status on the Hub screens.")
    doc.fact(n, needle="UK motor claims have been on Claims Hub since Wave 1", kind="general", world_ref="WAVE:MW-1#scope",
             statement="Since Wave 1 (2026-09-14) UK motor claims and their payments are on Claims Hub.")
    for s in ["Home, commercial and liability payments are still checked in CLARA until Wave 2.",
              "Payments go out through the Corvane Payments Gateway. If the status shows 'sent', the money has left us.",
              "Never take or change bank details on the enquiries line. Transfer to Payments Operations.",
              "If a customer says they have been paid twice, thank them, note the claim, and transfer to Payments Operations."]:
        doc.add(f"  - {s}")
    doc.add("")
    doc.add("3. WRAP CODES")
    for c in ["PAY-STATUS  Payment status given", "PAY-XFER    Transferred to Payments Operations",
              "PAY-DUPL    Customer reports a possible duplicate payment"]:
        doc.add(f"  {c}")
    _end(doc, d, "P035")
    return doc


# =============================================================================================
def tx068(facts: Facts):
    fid, d = "TX068", D("2026-10-02")
    for ref, f in [("RULE:BR-RSV-007@v3", "text"), ("INTERFACE:CLX-IF-058", None), ("TOPIC:reserve.changed.v2", "consumers"),
                   ("WAVE:MW-1", "date")]:
        assert_may(fid, ref, f)
    doc = _doc(fid, "ops_handover_reserving_month_end_2026_09", facts)
    _control(doc, title_="Reserving - month-end handover notes (September 2026 close)", ref="RSV-ME-2026-09", version="1.0",
             d=d, owner="P009", approver=None,
             history=[("1.0", "2026-10-02", "L. Kristiansen", "Handover for the October close team")],
             extra=["Distribution    : Reserving team, Financial Control, Actuarial"])
    doc.add("1. WHAT WAS DIFFERENT THIS MONTH")
    doc.add("  - First month-end with UK motor on Claims Hub (Wave 1 cut over on 14 September).")
    n = doc.add("  - Motor reserve movements now come from reserve-engine as reserve.changed.v2 events, consumed by gl-posting-svc and reporting-feed-svc.")
    doc.fact(n, needle="reserve.changed.v2 events, consumed by gl-posting-svc and reporting-feed-svc", kind="general",
             world_ref="TOPIC:reserve.changed.v2",
             statement="reserve-engine publishes reserve.changed.v2, consumed by gl-posting-svc and reporting-feed-svc.")
    doc.add("  - All other products are still reserved in CLARA. The month-end snapshot for those ran as usual.")
    doc.add("")
    doc.add("2. CHECKS COMPLETED")
    for c in ["Motor outstanding on the Hub agreed to the general ledger after journals posted.",
              "CLARA outstanding for the remaining products agreed to the general ledger.",
              "Large movements reviewed and confirmed with the handlers.",
              "Tier-3 review diary checked: reviews are running on the 14-day cycle."]:
        doc.add(f"  [x] {c}")
    n = len(doc.lines)
    doc.fact(n, needle="reviews are running on the 14-day cycle", kind="general", world_ref="RULE:BR-RSV-007@v3",
             statement="Tier-3 reserve reviews run on a 14-day cycle (BR-RSV-007 v3, from 2026-07-01).")
    doc.add("")
    doc.add("3. FOR THE IBNR RUN")
    n = doc.add("  - The triangles extract (CLX-IF-058) from the Claims Data Warehouse runs on the 3rd business day as usual and feeds the monthly IBNR run.")
    doc.fact(n, needle="triangles extract (CLX-IF-058)", kind="general", world_ref="INTERFACE:CLX-IF-058",
             statement="CLX-IF-058 (reserve triangles extract, monthly on the 3rd business day) feeds the Reserving team's monthly IBNR run.")
    doc.add("  - Actuarial asked for motor to be flagged separately this month so the first Hub month can be reviewed on its own.")
    doc.add("")
    doc.add("4. OPEN POINTS")
    for c in ["Agree with Financial Control how the Hub journals are labelled in the ledger reports.",
              "Confirm with Actuarial that the motor triangle has no break at the cut-over date."]:
        doc.add(f"  - {c}")
    _end(doc, d, "P009")
    return doc


DOCS = [tx021, tx022, tx023, tx024, tx027, tx028, tx029, tx030, tx062, tx063, tx064, tx066, tx067, tx068]
