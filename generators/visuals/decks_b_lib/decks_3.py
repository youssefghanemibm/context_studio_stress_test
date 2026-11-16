"""VS025-VS028 deck builders."""
from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from . import phrases as PH
from . import raster as R
from .common import approvers, contacts_slide, glossary_slide, guard, history, next_steps_slide, person, risks_slide
from .core import (AMBER, CONTENT_LEFT, CONTENT_TOP, CONTENT_W, GREEN, GREY, GREY_LT, NAVY, RED, SAND, TEAL, TEAL_LT,
                   WHITE, Deck, fmt_date, minus_days)


def _as_of_names(W, text: str, d: str) -> str:
    """Rewrite world text that uses later names so it reads as of date d."""
    for sid in ("SYS17", "SYS05", "SYS03", "SYS04"):
        cur, old = W.systems[sid]["name"], W.system_name(sid, d)
        if cur != old:
            text = text.replace(f"{old} (now {cur})", old).replace(cur, old)
    cur, old = "reserve-engine", W.service_name("reserve-engine", d)
    if cur != old:
        text = text.replace(f"{cur} (then {old})", old).replace(cur, old)
    return text


# =========================================================================================
# VS025 Tier Classification Decision Tree (2025-01-06)
# =========================================================================================
def build_vs025(W, out_dir):
    fid = "VS025"
    dk = Deck(W, fid, out_dir, short_title="Tier Classification Decision Tree")
    d = dk.date
    v3 = W.rule_version("BR-TRI-003", d)
    assert v3["version"] == 3 and v3["parameters"]["tier3_min_gbp"] == 50000
    v2 = [v for v in W.rules["BR-TRI-003"]["versions"] if v["version"] == 2][0]
    guard(W, fid, [("RULE:BR-TRI-003@v3", "parameters.tier3_min_gbp"), ("RULE:BR-TRI-003@v3", "parameters.tier3_triggers"),
                   ("RULE:BR-TRI-003@v2", "parameters"), ("RULE:BR-TRI-004@v1", "text"), ("RULE:BR-TRI-006@v2", "parameters"),
                   ("RULE:BR-TRI-009@v1", "parameters")])
    assert W.system_name("SYS03", d) == "FRAUDNET"
    p3, p2 = v3["parameters"], v2["parameters"]

    s = dk.title_slide("Tier Classification Decision Tree", "BR-TRI-003 v3 – effective 1 January 2025",
                       [f"Owner: {person(W, 'P011', d)}",
                        f"Claims Operations UK  |  {fmt_date(d)}  |  Classification: Internal"])
    dk.notes(s, "This pack replaces the v2 tiering card. Approved by the Claims Director on 26 November 2024 via "
                "Claims Standards Bulletin CSB-2024-11.")
    dk.fact("speaker_notes", "Speaker notes: BR-TRI-003 v3 was approved on 26 November 2024 via CSB-2024-11.", 1,
            "notes", "Approved by the Claims Director on 26 November 2024 via Claims Standards Bulletin CSB-2024-11",
            world_ref="RULE:BR-TRI-003@v3#approved_on")

    # 2 decision tree (PL-124, PL-125)
    s = dk.new_slide("How to tier a claim", "Ask the questions in order; the first 'Yes' decides")
    qs = ["Estimated incurred ≥ £50,000?", "Bodily injury?", "Solicitor or litigation at notification?",
          "Property total loss?", "Estimated incurred ≥ £5,000 or any third-party involvement?"]
    dia = []
    for i, q in enumerate(qs):
        x = 0.45 + i * 2.38
        dia.append(dk.box(s, x, 1.75, 2.2, 1.6, q, shape=MSO_SHAPE.DIAMOND, fill=SAND, line=AMBER,
                          size=10 if i < 4 else 9, bold=True, color=NAVY, name=f"q{i + 1}"))
    terms = []
    for i in range(4):
        x = 0.45 + i * 2.38 + 0.3
        terms.append(dk.box(s, x, 4.3, 1.6, 0.65, "Tier-3", fill=RED, line=None, color=WHITE, size=15, bold=True,
                            name=f"t3-{i + 1}"))
    t2 = dk.box(s, 0.45 + 4 * 2.38 + 0.3, 4.3, 1.6, 0.65, "Tier-2", fill=AMBER, line=None, color=WHITE, size=15,
                bold=True, name="t2")
    t1 = dk.box(s, 11.25, 5.6, 1.6, 0.65, "Tier-1", fill=GREEN, line=None, color=WHITE, size=15, bold=True, name="t1")
    for i in range(4):
        dk.connect(s, dia[i], terms[i], 2, 0, label="Yes", label_w=0.5, label_offset=(0.32, -0.15),
                   name=f"yes-{i + 1}")
        dk.connect(s, dia[i], dia[i + 1], 3, 1, label="No", label_w=0.45, label_offset=(0, -0.33), name=f"no-{i + 1}")
    dk.connect(s, dia[4], t2, 2, 0, label="Yes", label_w=0.5, label_offset=(0.32, -0.15), name="yes-5")
    dk.connect(s, dia[4], t1, 3, 0, label="No", label_w=0.45, elbow=True, label_offset=(0.35, 0.3), name="no-5")
    dk.fact("arrow_only", "Decision 'Estimated incurred ≥ £50,000?' → 'Tier-3' [Yes].", 2, "connector",
            "Estimated incurred ≥ £50,000? -> Tier-3 [label: Yes]", placement="PL-124", shape_name="yes-1")
    dk.fact("arrow_only", "Decision 'Bodily injury?' → 'Tier-3' [Yes].", 2, "connector",
            "Bodily injury? -> Tier-3 [label: Yes]", placement="PL-125", shape_name="yes-2")
    dk.fact("arrow_only", "Decision 'Solicitor or litigation at notification?' → 'Tier-3' [Yes].", 2, "connector",
            "Solicitor or litigation at notification? -> Tier-3 [label: Yes]",
            world_ref="RULE:BR-TRI-003@v3#parameters.tier3_triggers", shape_name="yes-3")
    dk.fact("arrow_only", "Decision 'Property total loss?' → 'Tier-3' [Yes].", 2, "connector",
            "Property total loss? -> Tier-3 [label: Yes]", world_ref="RULE:BR-TRI-003@v3#parameters.tier3_triggers",
            shape_name="yes-4")
    dk.fact("arrow_only", "Decision 'Estimated incurred ≥ £5,000 or any third-party involvement?' → 'Tier-2' [Yes].",
            2, "connector", "Estimated incurred ≥ £5,000 or any third-party involvement? -> Tier-2 [label: Yes]",
            world_ref="RULE:BR-TRI-003@v3#parameters.tier2_min_gbp", shape_name="yes-5")
    dk.fact("arrow_only", "Otherwise the claim is Tier-1 (No branch of the last question).", 2, "connector",
            "Estimated incurred ≥ £5,000 or any third-party involvement? -> Tier-1 [label: No]",
            world_ref="RULE:BR-TRI-003@v3", shape_name="no-5")
    dk.fact("arrow_only", "If estimated incurred is below £50,000, the next question is bodily injury.", 2, "connector",
            "Estimated incurred ≥ £50,000? -> Bodily injury? [label: No]", world_ref="RULE:BR-TRI-003@v3",
            shape_name="no-1")
    dk.text(s, CONTENT_LEFT, 6.2, 10.4, 0.5, "Nordic claims use the local-currency equivalents (slide 5).", size=12,
            color=GREY, italic=True)
    dk.notes(s, "Walk the tree left to right. Most claims leave at the first question or at the last one. Remind "
                "handlers that re-tiering happens automatically when the estimate crosses a boundary.")
    # 3 document control
    appr = approvers(W, d, ["P005", "P030"], minus_days(d, 5))
    dk.doc_control_slide("CLM-TRI-TREE-V3", person(W, "P011", d), appr,
                         history(dk, ["P011", "P039", "P011"], spans=(33, 20, 8),
                                 notes=["Draft for CSB-2024-11", "Nordic equivalents added",
                                        "Examples reviewed with team leaders"]),
                         "Claims Operations UK, Claims Operations Nordics, Major & Complex Loss, Contact Centre")
    # 4 what changed from v2
    s = dk.new_slide("What changed from v2")
    rows = [["Item", "v2 (2022–2024)", "v3 (from 1 January 2025)"],
            ["Tier-3 threshold (GBP)", f"£{p2['tier3_min_gbp']:,}", f"£{p3['tier3_min_gbp']:,}"],
            ["Tier-3 threshold (NOK)", f"NOK {p2['tier3_min_nok']:,}", f"NOK {p3['tier3_min_nok']:,}"],
            ["Tier-3 threshold (SEK)", f"SEK {p2['tier3_min_sek']:,}", f"SEK {p3['tier3_min_sek']:,}"],
            ["Tier-3 threshold (DKK)", f"DKK {p2['tier3_min_dkk']:,}", f"DKK {p3['tier3_min_dkk']:,}"],
            ["Other Tier-3 triggers", "Any bodily injury", "Bodily injury; litigation at notification; property total loss"],
            ["Tier-2 band", "£5,000–£39,999 or third party", "£5,000–£49,999 or third party"]]
    dk.table(s, rows, col_w=[3.2, 4.0, 4.8], size=14, row_h=0.55, name="Version comparison")
    dk.fact("temporal", "BR-TRI-003 v2 Tier-3 threshold was £40,000; v3 is £50,000 from 1 January 2025.", 4, "table",
            "Tier-3 threshold (GBP) £40,000 £50,000", world_ref="RULE:BR-TRI-003@v2#parameters.tier3_min_gbp")
    dk.fact("temporal", "BR-TRI-003 Tier-3 threshold in DKK rose from 340,000 to 430,000.", 4, "table",
            "DKK 340,000 DKK 430,000", world_ref="RULE:BR-TRI-003@v3#parameters.tier3_min_dkk")
    # 5 nordic equivalents
    s = dk.new_slide("Nordic equivalents")
    rows = [["Country", "Currency", "Tier-3 threshold", "Route"],
            ["Norway", "NOK", f"{p3['tier3_min_nok']:,}", "Claims Operations Nordics"],
            ["Sweden", "SEK", f"{p3['tier3_min_sek']:,}", "Claims Operations Nordics"],
            ["Denmark", "DKK", f"{p3['tier3_min_dkk']:,}", "Claims Operations Nordics"]]
    dk.table(s, rows, col_w=[2.2, 1.6, 3.0, 4.2], size=15, row_h=0.6, w=11.0, name="Nordic thresholds")
    dk.text(s, CONTENT_LEFT, 4.3, CONTENT_W, 1.6, [W.rule_version("BR-TRI-015", d)["text"].rstrip(".") + " (BR-TRI-015)",
                                                   W.rule_version("BR-TRI-005", d)["text"].rstrip(".") + " (BR-TRI-005)"],
            size=15, bullets=True)
    dk.fact("general", "Swedish Tier-3 threshold: SEK 680,000.", 5, "table", "Sweden SEK 680,000",
            world_ref="RULE:BR-TRI-003@v3#parameters.tier3_min_sek")
    # 6 routing after tiering (connectors)
    s = dk.new_slide("Routing after tiering")
    tb = {k: dk.box(s, 0.7, 1.6 + i * 1.3, 2.0, 0.75, k, fill=c, line=None, color=WHITE, size=15, bold=True,
                    name=f"route-{k}") for i, (k, c) in enumerate([("Tier-3", RED), ("Tier-2", AMBER), ("Tier-1", GREEN)])}
    tm = W.team_name("T09", d)
    dest = {"mcl": dk.box(s, 7.2, 1.6, 3.6, 0.75, tm, size=14, bold=True, name="dest-mcl"),
            "spec": dk.box(s, 7.2, 2.9, 3.6, 0.75, "Specialist claim handlers", size=14, bold=True, name="dest-spec"),
            "fast": dk.box(s, 7.2, 4.2, 3.6, 0.75, "Fast-track queue", size=14, bold=True, name="dest-fast")}
    bi = dk.box(s, 0.7, 5.5, 2.0, 0.75, "Bodily injury", fill=GREY_LT, line=GREY, size=14, bold=True, name="route-bi")
    routes = [("Tier-3", "mcl", "within 4 hours (BR-TRI-004)"), ("Tier-2", "spec", "BR-TRI-004"),
              ("Tier-1", "fast", "if BR-TRI-006 is met")]
    for t, k, lab in routes:
        dk.connect(s, tb[t], dest[k], 3, 1, label=lab, label_w=2.6, label_offset=(0, -0.33))
        dk.fact("arrow_only", f"Routing connector {t} → {dest[k].text_frame.text} labelled '{lab}'.", 6, "connector",
                f"{t} -> {dest[k].text_frame.text} [label: {lab}]", world_ref="RULE:BR-TRI-004@v1")
    dk.connect(s, bi, dest["mcl"], 3, 2, label="any amount (BR-TRI-002)", label_w=2.4, elbow=True,
               label_offset=(0.0, 0.75), label_t=0.35)
    dk.fact("arrow_only", f"Bodily injury claims route to {tm} regardless of amount (BR-TRI-002).", 6, "connector",
            f"Bodily injury -> {tm} [label: any amount (BR-TRI-002)]", world_ref="RULE:BR-TRI-002@v1")
    # 7 fast-track and related rules
    s = dk.new_slide("Fast-track and related rules")
    ft = W.rule_version("BR-TRI-006", d)
    items = [ft["text"].replace("Sentinel", "FRAUDNET").rstrip(".") + f" (BR-TRI-006 v{ft['version']})",
             W.rule_version("BR-TRI-008", d)["text"].rstrip(".") + " (BR-TRI-008)",
             W.rule_version("BR-TRI-009", d)["text"].rstrip(".") + " (BR-TRI-009)",
             W.rule_version("BR-TRI-013", d)["text"].rstrip(".") + " (BR-TRI-013)",
             W.rule_version("BR-TRI-017", d)["text"].rstrip(".") + " (BR-TRI-017)",
             W.rule_version("BR-TRI-019", d)["text"].rstrip(".") + " (BR-TRI-019, new from 1 January 2025)"]
    dk.bullets(s, items, size=14)
    dk.fact("general", "January 2025 fast-track: Tier-1, FRAUDNET score below 30, no injury; cap £1,500 (BR-TRI-006 v2).",
            7, "text", "FRAUDNET score below 30 and no injury; cap £1,500", world_ref="RULE:BR-TRI-006@v2")
    dk.fact("general", "Public liability claims involving injury are always Tier-3 (BR-TRI-019).", 7, "text",
            "Public liability claims involving injury are always Tier-3", world_ref="RULE:BR-TRI-019@v1")
    dk.fact("general", "Flood claims above £30000 route to Major & Complex Loss (BR-TRI-017).", 7, "text",
            "Flood claims above £30000 route to Major & Complex Loss", world_ref="RULE:BR-TRI-017@v1")
    # 8 worked examples (table image)
    s = dk.new_slide("Worked examples")
    rows = [["Example", "Deciding question", "Tier"],
            ["Escape of water, estimate £62,000", "Estimated incurred ≥ £50,000", "Tier-3"],
            ["Rear-end collision, whiplash claimed, estimate £3,200", "Bodily injury", "Tier-3"],
            ["Storm damage, estimate £8,400, no third party", "≥ £5,000", "Tier-2"],
            ["Windscreen, estimate £420, no third party", "none (all No)", "Tier-1"],
            ["House fire, property total loss, estimate £45,000", "Property total loss", "Tier-3"],
            ["Theft from car, estimate £1,100, third party involved", "Third-party involvement", "Tier-2"]]
    png = R.table_image(rows, [720, 460, 180], title="Applying BR-TRI-003 v3", size=24, row_h=54)
    dk.picture(s, png, CONTENT_LEFT + 0.6, CONTENT_TOP, w=11.0, alt="Worked tiering examples under BR-TRI-003 v3.",
               name="examples-image")
    dk.fact("image_table", "Worked example: a house fire that is a property total loss (estimate £45,000) is Tier-3.",
            8, "image", "property total loss", world_ref="RULE:BR-TRI-003@v3#parameters.tier3_triggers")
    # 9 quick reference card (raster)
    s = dk.new_slide("Quick reference card (print version)")
    cv = R.Canvas(1700, 820)
    cv.title("Tiering card – BR-TRI-003 v3")
    xs = [170, 500, 830, 1160, 1490]
    short = [["Incurred GBP", "50,000 or more?"], ["Bodily", "injury?"], ["Litigation at", "notification?"],
             ["Property", "total loss?"], ["GBP 5,000+ or", "third party?"]]
    for i, (x, q) in enumerate(zip(xs, short)):
        cv.diamond(x, 290, 310, 230, q, size=23)
        if i < 4:
            cv.arrow((x + 150, 290), (xs[i + 1] - 150, 290), label="No", label_size=22, label_offset=(0, -40))
            cv.arrow((x, 400), (x, 560), label="Yes", label_size=22, label_offset=(34, -14))
            cv.box(x - 100, 570, 200, 80, "Tier-3", fill=(250, 220, 218), outline=R.RED, size=28)
    cv.arrow((xs[4], 400), (xs[4], 560), label="Yes", label_size=22, label_offset=(34, -14))
    cv.box(xs[4] - 100, 570, 200, 80, "Tier-2", fill=R.AMBER_LT, outline=R.AMBER, size=28)
    cv.text((xs[4], 690), "No: Tier-1", size=26, bold=True, fill=R.GREEN, anchor="ma")
    dk.picture(s, cv.png(), CONTENT_LEFT, CONTENT_TOP + 0.1, w=CONTENT_W,
               alt="Printable tiering card: five questions in order; the first Yes decides Tier-3, the last decides "
                   "Tier-2, otherwise Tier-1.", name="card-image")
    dk.fact("image_text", "Quick reference card: 'Incurred GBP 50,000 or more?' Yes → Tier-3.", 9, "image",
            "50,000 or more?",
            world_ref="RULE:BR-TRI-003@v3#parameters.tier3_min_gbp")
    dk.fact("alt_text", "Alt text: the first Yes decides Tier-3; otherwise Tier-1.", 9, "alt_text",
            "the first Yes decides Tier-3")
    # 10 where implemented
    s = dk.new_slide("Where the rule is implemented")
    progs = W.rules["BR-TRI-003"]["implemented_in"]["programs"]
    rows = [["Program", "Description", "Run"]]
    for p in progs:
        pr = W.programs[p]
        rows.append([p, pr["description"], pr.get("jcl_job") or (pr.get("cics_transaction") or "online")])
    dk.table(s, rows, col_w=[1.8, 7.4, 2.4], size=14, row_h=0.6, name="Implementation")
    dk.text(s, CONTENT_LEFT, 3.6, CONTENT_W, 2.0,
            ["The Tier-3 threshold is the CLR.T_PARAM row TRI_T3_MIN_GBP = 50000, valid from 1 January 2025",
             "The nightly triage job re-tiers claims whose estimate changed during the day"], size=15, bullets=True)
    dk.fact("general", "CLR.T_PARAM row TRI_T3_MIN_GBP holds the Tier-3 threshold 50000 from 1 January 2025.", 10,
            "text", "TRI_T3_MIN_GBP = 50000, valid from 1 January 2025",
            world_ref="TABLE:CLR.T_PARAM#param_rows:TRI_T3_MIN_GBP")
    dk.fact("general", "CLRTR020 (tier classification batch) runs in job CLRNTR01.", 10, "table", "CLRTR020",
            world_ref="PROGRAM:CLRTR020#jcl_job")
    # 11 FAQ
    s = dk.new_slide("Questions handlers ask")
    rows = [["Question", "Answer"],
            ["Can I override the tier?", "Yes, with a reason code and Team Leader approval (BR-TRI-009)."],
            ["What if the estimate changes?", "The claim is re-tiered when it crosses a boundary (BR-TRI-008)."],
            ["Is BI always Tier-3?", "Yes – any bodily injury, whatever the amount."],
            ["Do Nordic claims use GBP?", "No – local-currency thresholds apply (BR-TRI-015)."]]
    dk.table(s, rows, col_w=[4.0, 8.0], size=14, row_h=0.65, name="FAQ")
    # 12 next steps
    next_steps_slide(dk, extra=["Replace the v2 desk cards with the v3 card", "Brief Nordic teams on local thresholds"])
    return dk


# =========================================================================================
# VS026 Security and Identity Architecture (2025-04-14)
# =========================================================================================
def build_vs026(W, out_dir):
    fid = "VS026"
    dk = Deck(W, fid, out_dir, short_title="Security and Identity Architecture")
    d = dk.date
    assert W.system_name("SYS17", d) == "Adjuster Extranet" and W.system_name("SYS05", d) == "DOCSTOR"
    guard(W, fid, [("ADR:ADR-029", None), ("ADR:ADR-008", None), ("SYSTEM:SYS16", None), ("SYSTEM:SYS02", "hosting"),
                   ("SYSTEM:SYS01", "hosting"), ("RULE:BR-FNOL-017@v1", "text"), ("INTERFACE:CLX-IF-008", "format")])
    assert not W.may_state(fid, "EPISODE:EP-009", None)

    s = dk.title_slide("Security and Identity Architecture", "Claims Hub and partner access – approved architecture",
                       [f"Author: {person(W, 'P018', d)}",
                        f"Enterprise Architecture  |  {fmt_date(d)}  |  Classification: Internal"])
    appr = approvers(W, d, ["P006", "P032", "P019", "P049"], minus_days(d, 3))
    dk.doc_control_slide("EA-SEC-IAM-001", person(W, "P018", d), appr,
                         history(dk, ["P018", "P050", "P018"], spans=(28, 14, 4)),
                         "Design Authority, Technology Delivery, Data Protection, Integration Platform")
    # 3 partner access path (PL-126)
    s = dk.new_slide("Target state: partner and workforce access paths", "Policies shown on the arrows")
    ap = dk.box(s, 0.5, 1.8, 2.5, 0.9, "Assessor Portal", fill=SAND, line=AMBER, size=15, bold=True, name="ap")
    dk.text(s, 0.4, 2.75, 2.7, 0.55, "(target-state name for the Adjuster Extranet)", size=9, color=GREY,
            align=PP_ALIGN.CENTER, name="ap-caption")
    wb = dk.box(s, 0.5, 4.4, 2.5, 0.9, "Workforce browser", fill=SAND, line=AMBER, size=15, bold=True, name="wb")
    cis = dk.box(s, 4.7, 3.0, 2.4, 1.2, "CIS (OIDC)", fill=NAVY, line=None, color=WHITE, size=17, bold=True, name="cis")
    gw = dk.box(s, 8.6, 1.8, 2.3, 0.9, "Claims Hub API gateway", size=13, bold=True, name="gw")
    ui = dk.box(s, 8.6, 4.4, 2.3, 0.9, "Claims Hub UI", size=14, bold=True, name="ui")
    svc = dk.box(s, 11.4, 3.0, 1.5, 1.2, "Claims Hub services", fill=GREY_LT, line=GREY, size=12, bold=True,
                 name="svcs")
    dk.connect(s, ap, cis, 3, 1, label="partner sign-in", label_w=1.5, label_offset=(-0.1, -0.4), name="c-ap-cis")
    dk.connect(s, wb, cis, 3, 1, label="SSO with MFA", label_w=1.4, label_offset=(-0.1, 0.1), name="c-wb-cis")
    dk.connect(s, cis, gw, 3, 1, label="partner limit 50 req/s", label_w=2.0, label_offset=(0.0, -0.45),
               name="c-cis-gw")
    dk.connect(s, cis, ui, 3, 1, label="ID token", label_w=1.0, label_offset=(0.0, 0.08), name="c-cis-ui")
    dk.connect(s, gw, svc, 3, 0, label="routed API calls", label_w=1.5, elbow=True, label_offset=(0.2, -0.35),
               name="c-gw-svc")
    dk.connect(s, ui, svc, 3, 2, label="user session", label_w=1.3, elbow=True, label_offset=(0.2, 0.15),
               name="c-ui-svc")
    dk.fact("arrow_only", "Assessor Portal → CIS (OIDC) → Claims Hub API gateway; connector label 'partner limit 50 "
                          "req/s'.", 3, "connector", "CIS (OIDC) -> Claims Hub API gateway [label: partner limit 50 req/s]",
            placement="PL-126", shape_name="c-cis-gw",
            notes="Deck dated 2025-04-14 shows a target-state diagram; ADR-029 (the 50 req/s partner limit) is dated "
                  "2026-04-20 and the Assessor Portal name dates from 2025-09-01 (world-plan timing conflict).")
    dk.fact("arrow_only", "Partner users sign in from the Assessor Portal through CIS (OIDC).", 3, "connector",
            "Assessor Portal -> CIS (OIDC) [label: partner sign-in]", world_ref="ADR:ADR-008", shape_name="c-ap-cis")
    dk.fact("arrow_only", "Workforce users reach CIS with SSO and MFA.", 3, "connector",
            "Workforce browser -> CIS (OIDC) [label: SSO with MFA]", world_ref="SYSTEM:SYS16", shape_name="c-wb-cis")
    dk.notes(s, "Workforce and partner identity both go through the Corvane Identity Service; customers keep their "
                "own portal login. Gateway policies are applied per client, partners separately from internal "
                "traffic.")
    # 4 principles
    s = dk.new_slide("Architecture decisions that shape security")
    rows = [["ADR", "Decision", "Security consequence"]]
    for aid in ["ADR-008", "ADR-006", "ADR-003", "ADR-002", "ADR-004", "ADR-009", "ADR-010", "ADR-011"]:
        a = W.adrs[aid]
        assert a["date"] <= d, aid
        rows.append([aid, _as_of_names(W, a["title"], d), _as_of_names(W, a["consequences"], d)])
    dk.table(s, rows, col_w=[1.1, 5.0, 6.0], size=10.5, row_h=0.56, name="ADR table")
    dk.fact("general", "ADR-008: workforce and partner identity through CIS (OIDC).", 4, "table",
            "ADR-008 Workforce and partner identity through CIS (OIDC)", world_ref="ADR:ADR-008")
    dk.fact("general", "ADR-006: OpenShift runtime on clusters ocp-prd-lon1 (primary) and ocp-dr-lds1 (DR).", 4, "table",
            "Clusters ocp-prd-lon1 (primary) and ocp-dr-lds1 (DR)", world_ref="ADR:ADR-006")
    dk.fact("general", "ADR-004: MQ is retained for mainframe integration until CLARA is decommissioned.", 4, "table",
            "ADR-004 Retain MQ for mainframe integration until CLARA decommissioning", world_ref="ADR:ADR-004")
    # 5 trust zones (groups)
    s = dk.new_slide("Trust zones")
    zones = [("Internet", ["MyCorvane Claims users", "Adjuster Extranet users"]),
             ("Edge", ["Claims Hub API gateway", "Web application firewall"]),
             ("Private cloud – London", ["Claims Hub (ocp-prd-lon1)", "Corvane Identity Service", "PALM"]),
             ("Leeds Data Centre", ["CLARA – z/OS LPAR PRD1", "Sentinel VM cluster"]),
             ("Vendor SaaS", ["WatchScreen", "ReCede", "Harbour CRM", "Notify"])]
    for i, (zname, items) in enumerate(zones):
        g = dk.group(s, f"grp-zone-{i + 1}")
        x = CONTENT_LEFT + i * 2.46
        dk.box(s, x, CONTENT_TOP + 0.1, 2.35, 0.6, zname, shape=MSO_SHAPE.RECTANGLE, fill=NAVY, line=None, color=WHITE,
               size=13, bold=True, group=g, name=f"zone-hdr-{i + 1}")
        for k, it in enumerate(items):
            dk.box(s, x + 0.1, CONTENT_TOP + 0.9 + k * 0.95, 2.15, 0.8, it, fill=TEAL_LT, line=None, size=11, bold=True,
                   group=g, name=f"zone-{i + 1}-{k + 1}")
    dk.fact("visual_only", "Trust zone 'Leeds Data Centre' contains CLARA on z/OS LPAR PRD1 and the Sentinel VM cluster.",
            5, "group", "Leeds Data Centre CLARA – z/OS LPAR PRD1 Sentinel VM cluster", world_ref="LOC:LOC-LDC#functions",
            shape_name="grp-zone-4")
    dk.fact("visual_only", "Trust zone 'Vendor SaaS' groups WatchScreen, ReCede, Harbour CRM and Notify.", 5, "group",
            "Vendor SaaS WatchScreen ReCede Harbour CRM Notify", world_ref="SYSTEM:SYS19#hosting",
            shape_name="grp-zone-5")
    # 6 sign-in sequence raster
    s = dk.new_slide("Workforce sign-in sequence")
    cv = R.Canvas(1600, 760)
    cv.title("OIDC authorisation code flow (workforce)")
    cols = [("Browser", 170), ("Claims Hub UI", 590), ("CIS", 1010), ("API gateway", 1420)]
    for nm, x in cols:
        cv.box(x - 130, 100, 260, 64, nm, size=24)
        cv.d.line([(x, 164), (x, 730)], fill=R.GREY_MD, width=3)
    cv.arrow((170, 230), (590, 230), label="open Claims Hub")
    cv.arrow((590, 320), (170, 320), label="redirect to CIS", color=R.TEAL)
    cv.arrow((170, 410), (1010, 410), label="sign in + MFA")
    cv.arrow((1010, 500), (590, 500), label="authorisation code", color=R.TEAL)
    cv.arrow((590, 590), (1010, 590), label="code for tokens")
    cv.arrow((590, 680), (1420, 680), label="API call with access token")
    dk.picture(s, cv.png(), CONTENT_LEFT + 0.3, CONTENT_TOP, w=CONTENT_W - 0.6,
               alt="Sequence diagram of the workforce OIDC sign-in from the browser through CIS to the API gateway.",
               name="signin-image")
    dk.fact("image_text", "Sign-in sequence image: 'sign in + MFA' step from browser to CIS.", 6, "image",
            "sign in + MFA", world_ref="SYSTEM:SYS16")
    dk.fact("alt_text", "Alt text: workforce OIDC sign-in through CIS to the API gateway.", 6, "alt_text",
            "workforce OIDC sign-in from the browser through CIS to the API gateway")
    # 7 role model
    s = dk.new_slide("Role model (summary)")
    rows = [["Role", "Who", "Access"],
            ["Claim handler", "Claims Operations teams", "Own work queue, claims, reserves and payments within authority"],
            ["Team Leader", "Team leaders", "Approval queues for reserves and payments above handler authority"],
            ["Claims Assessor (internal)", "Claims Assessment UK and Nordics", "Assessment tasks and reports"],
            ["Claims Assessor (panel)", "Panel firms via the partner portal", "Own instructions only; rate-limited APIs"],
            ["SIU investigator", "Counter-fraud staff", "Referrals and investigation outcomes"],
            ["Auditor (read-only)", "Internal audit, Compliance", "Read-only access with full audit trail"]]
    dk.table(s, rows, col_w=[2.6, 3.4, 6.0], size=13, row_h=0.6, name="Roles")
    # 8 data protection
    s = dk.new_slide("Data protection by design")
    dk.bullets(s, [W.rule_version("BR-FNOL-017", d)["text"].rstrip(".") + " (BR-FNOL-017)",
                   f"Data Protection Officer: {W.name_of('P019', d)}",
                   "Binary documents are never stored in service databases; DOCSTOR holds them behind the document "
                   "service (ADR-009)",
                   "No production personal data in test environments"] + PH.pick(dk.rng, PH.GOVERNANCE, 1), size=15)
    dk.fact("general", "Nordic FNOLs show the personal number masked (last 4 digits only) outside production "
                       "(BR-FNOL-017).", 8, "text", "masked (last 4 digits only) outside production",
            world_ref="RULE:BR-FNOL-017@v1")
    dk.fact("general", "The Data Protection Officer is Morag Duthie.", 8, "text",
            f"Data Protection Officer: {W.name_of('P019', d)}", world_ref="PERSON:P019#titles")
    # 9 mainframe integration
    s = dk.new_slide("Securing the CLARA integration")
    i8 = W.interfaces["CLX-IF-008"]
    dk.bullets(s, [f"Online scoring (CLX-IF-008): {i8['format']}",
                   "MQ Backbone channels stay in place until CLARA is decommissioned (ADR-004)",
                   "No new MQ flows from Claims Hub; Claims Hub integrates through events and APIs",
                   "Service accounts are per interface and owned by the interface owner"], size=15)
    dk.fact("general", "CLX-IF-008 uses JSON over HTTPS via the mainframe API gateway (SENTREQ1/SENTRSP1 mapping).", 9,
            "text", "JSON (HTTPS) via mainframe API gateway; SENTREQ1/SENTRSP1 mapping", world_ref="INTERFACE:CLX-IF-008#format")
    # 10 threats and controls
    s = dk.new_slide("Threats and controls")
    rows = [["Threat", "Control"]] + [list(x) for x in dk.rng.sample(PH.SECURITY_CONTROLS, 6)]
    dk.table(s, rows, col_w=[3.2, 8.8], size=14, row_h=0.6, name="Controls")
    # 11 hosting
    s = dk.new_slide("Hosting")
    rows = [["System", "Hosting"]]
    for sid in ["SYS02", "SYS16", "SYS01", "SYS03", "SYS17", "SYS05"]:
        rows.append([W.system_name(sid, d), W.systems[sid]["hosting"]])
    dk.table(s, rows, col_w=[2.8, 9.2], size=13, row_h=0.6, name="Hosting")
    dk.fact("general", "Claims Hub runs on OpenShift cluster ocp-prd-lon1 with DR cluster ocp-dr-lds1 (Leeds).", 11,
            "table", "OpenShift cluster ocp-prd-lon1 (Corvane private cloud, London); DR cluster ocp-dr-lds1 (Leeds)",
            world_ref="SYSTEM:SYS02#hosting")
    dk.fact("general", "CLARA runs on z/OS LPAR PRD1 in the Leeds Data Centre, with DR on LPAR DRP1 in the Bristol DR "
                       "Data Centre.", 11, "table",
            "z/OS LPAR PRD1, Leeds Data Centre (LOC-LDC); DR on LPAR DRP1, Bristol DR Data Centre (LOC-BDC)",
            world_ref="SYSTEM:SYS01#hosting")
    dk.fact("general", "Sentinel is hosted on a Corvane private cloud VM cluster in the Leeds Data Centre.", 11, "table",
            "Sentinel Corvane private cloud VM cluster, Leeds Data Centre", world_ref="SYSTEM:SYS03#hosting")
    dk.fact("temporal", "In April 2025 the partner portal is still listed as the Adjuster Extranet (renamed Assessor "
                        "Portal on 2025-09-01).", 11, "table", "Adjuster Extranet Corvane private cloud, Leeds",
            world_ref="SYSTEM:SYS17#renames")
    # 12 next steps
    next_steps_slide(dk, extra=["Agree gateway policies per partner with the Design Authority",
                                "Confirm role mappings with Claims Operations before MVP"])
    return dk


# =========================================================================================
# VS027 Test Strategy Overview (2026-01-19)
# =========================================================================================
def build_vs027(W, out_dir):
    fid = "VS027"
    dk = Deck(W, fid, out_dir, short_title="Test Strategy Overview")
    d = dk.date
    assert not W.may_state(fid, "TIMELINE:programme", "parallel_run.variance_tolerance_pct_per_product_per_day")
    assert not W.may_state(fid, "TIMELINE:programme", "migration_reconciliation")
    guard(W, fid, [("ADR:ADR-023", None), ("ADR:ADR-025", None), ("ADR:ADR-024", None), ("ADR:ADR-013", None),
                   ("CIRCULAR:CIRC-2025-02", "requirements"), ("PROFILE:products", None), ("WAVE:MW-0", "rehearsals"),
                   ("WAVE:MW-1", "rehearsals"), ("TIMELINE:programme", "parallel_run.from")])

    s = dk.title_slide("Test Strategy Overview", "Programme Skerry – how we test Claims Hub and the migration",
                       [f"Author: {person(W, 'P053', d)}",
                        f"IBM Programme Skerry Team  |  {fmt_date(d)}  |  Classification: Internal"])
    appr = approvers(W, d, ["P049", "P048", "P017", "P032"], minus_days(d, 2))
    dk.doc_control_slide("SKR-TST-STRAT-002", person(W, "P053", d), appr,
                         history(dk, ["P053", "P054", "P053"], spans=(24, 11, 4)),
                         "Programme Skerry squads, Claims Hub Product, Technology Delivery, Data Protection")
    # 3 test levels pyramid (SmartArt-like group)
    s = dk.new_slide("Test levels")
    g = dk.group(s, "grp-test-pyramid")
    levels = ["Business acceptance (UAT)", "End-to-end regression", "System integration", "Contract tests",
              "Component tests", "Unit tests"]
    for i, lv in enumerate(levels):
        w = 3.0 + i * 1.2
        x = 0.55 + (9.0 - w) / 2
        dk.box(s, x, CONTENT_TOP + 0.1 + i * 0.85, w, 0.75, lv, shape=MSO_SHAPE.RECTANGLE,
               fill=[NAVY, TEAL][i % 2], line=None, color=WHITE, size=14, bold=True, group=g, name=f"level-{i + 1}")
    dk.text(s, 9.9, CONTENT_TOP + 0.2, 2.9, 4.8,
            ["Most tests sit at the bottom: fast and automated",
             "Contract tests protect every Kafka topic (ADR-023)",
             "UAT is owned by the business, not the squads"], size=13, bullets=True, para_space=12)
    dk.fact("visual_only", "Test pyramid includes a contract test level between component and system integration.", 3,
            "group", "System integration Contract tests Component tests", world_ref="ADR:ADR-023",
            shape_name="grp-test-pyramid")
    dk.fact("general", "Contract tests protect every Kafka topic (ADR-023).", 3, "text",
            "Contract tests protect every Kafka topic (ADR-023)", world_ref="ADR:ADR-023")
    # 4 pipeline (connectors)
    s = dk.new_slide("Path to production", "Gates on the arrows")
    stages = ["Commit", "Unit and component", "Contract tests", "Deploy to SIT", "E2E regression", "UAT", "Release"]
    bx = [dk.box(s, 0.5 + i * 1.8, 2.8, 1.45, 0.95, st, size=12, bold=True, name=f"pipe-{i + 1}")
          for i, st in enumerate(stages)]
    gates = ["build passes", "coverage met", "schema BACKWARD", "smoke tests", "no open Sev1", "business sign-off"]
    for i, gt in enumerate(gates):
        dk.connect(s, bx[i], bx[i + 1], 3, 1, label=gt, label_size=9, label_w=1.3,
                   label_offset=(0, -0.6 if i % 2 == 0 else 0.25))
    dk.fact("arrow_only", "Pipeline gate between contract tests and SIT deployment: schema compatibility BACKWARD.", 4,
            "connector", "Contract tests -> Deploy to SIT [label: schema BACKWARD]", world_ref="ADR:ADR-023")
    dk.fact("arrow_only", "Pipeline gate from UAT to release: business sign-off.", 4, "connector",
            "UAT -> Release [label: business sign-off]")
    dk.fact("arrow_only", "Pipeline gate from E2E regression to UAT: no open Sev1 defects.", 4, "connector",
            "E2E regression -> UAT [label: no open Sev1]")
    dk.text(s, CONTENT_LEFT, 4.6, CONTENT_W, 1.6, PH.pick(dk.rng, PH.TEST_PRACTICES, 3), size=14, bullets=True,
            color=GREY)
    # 5 environments
    s = dk.new_slide("Test environments")
    rows = [["Environment", "Purpose", "Data"],
            ["DEV", "Squad development and unit tests", "Synthetic"],
            ["SIT", "System integration with CLARA test region and partners' test endpoints", "Synthetic"],
            ["UAT", "Business acceptance by Claims Operations", "Synthetic and masked"],
            ["PERF", "Load and soak tests", "Synthetic, production-like volumes"],
            ["PRE-PROD", "Release rehearsal and migration dress rehearsals", "Masked"]]
    dk.table(s, rows, col_w=[2.0, 6.6, 3.4], size=14, row_h=0.6, name="Environments")
    # 6 test data (chart)
    s = dk.new_slide("Synthetic test data profile")
    prods = W.claims_profile["products"]
    cats = list(prods.keys())
    dk.chart(s, "bar", [W.products[p]["name"] for p in cats], {"Share of synthetic claims (%)":
                                                              [round(prods[p] * 100, 1) for p in cats]},
             CONTENT_LEFT, CONTENT_TOP, 7.6, 5.4, title="Synthetic claims by product (%)", number_format="0", legend=False,
             name="data-mix-chart")
    dk.text(s, 8.4, CONTENT_TOP + 0.2, 4.4, 4.8,
            ["Masked data for migration rehearsals (ADR-025), required by NISA Circular 2025/11 §4",
             "Synthetic claims follow the production product mix",
             "Nordic personal numbers are masked outside production (BR-FNOL-017)"], size=13, bullets=True,
            para_space=12)
    dk.fact("chart_only", "Synthetic test data: Motor Private UK is 34% of claims.", 6, "chart",
            "Share of synthetic claims (%): Motor Private UK=34", world_ref="PROFILE:products#PRD-MOT-UK")
    dk.fact("chart_only", "Synthetic test data: Hem Sverige is 5% of claims.", 6, "chart",
            "Share of synthetic claims (%): Hem Sverige=5", world_ref="PROFILE:products#PRD-HOM-SE")
    dk.fact("general", "Masked data is used for migration rehearsals (ADR-025), required by NISA Circular 2025/11 §4.", 6,
            "text", "Masked data for migration rehearsals (ADR-025), required by NISA Circular 2025/11 §4",
            world_ref="ADR:ADR-025")
    # 7 migration rehearsals
    s = dk.new_slide("Migration testing")
    rows = [["Wave", "Scope", "Planned date", "Rehearsals"]]
    for wid in ["MW-0", "MW-1"]:
        wv = W.waves[wid]
        rows.append([wv["name"], wv["scope"], fmt_date(wv["date"], "short"), str(wv["rehearsals"])])
    dk.table(s, rows, col_w=[2.6, 5.0, 2.0, 1.6], size=14, row_h=0.6, w=11.2, name="Rehearsals")
    dk.text(s, CONTENT_LEFT, 3.4, CONTENT_W, 2.6,
            ["Each rehearsal reconciles at claim level and at portfolio level before sign-off",
             "Claims closed more than 7 years before the wave date are archived, not migrated",
             "Exceptions are triaged daily by the data migration squad"], size=15, bullets=True, para_space=10)
    dk.fact("general", "Wave 1 (UK motor) is planned with 3 migration rehearsals.", 7, "table",
            "Wave 1 – UK motor PRD-MOT-UK 14 Sep 2026 3", world_ref="WAVE:MW-1#rehearsals")
    dk.fact("general", "Wave 0 (Denmark) is planned with 2 migration rehearsals.", 7, "table", "1 Jun 2026 2",
            world_ref="WAVE:MW-0#rehearsals")
    # 8 parallel run
    s = dk.new_slide("Reserve parallel run")
    pr = W.timeline["programme"]["parallel_run"]
    dk.bullets(s, [f"CLARA and {W.service_name('reserve-engine', d)} run side by side from {fmt_date(pr['from'])} to "
                   f"{fmt_date(pr['to'])}",
                   "Daily comparison per product; variances investigated with Reserving",
                   "The bridge republishes CLARA reserve movements as events for the engine (ADR-012)",
                   "Exit requires Reserving sign-off"], size=16)
    dk.fact("temporal", "In January 2026 the reserve service is still called reserve-svc; the parallel run is "
                        "2 March to 28 August 2026.", 8, "text",
            "CLARA and reserve-svc run side by side from 2 March 2026 to 28 August 2026",
            world_ref="TIMELINE:programme#parallel_run")
    # 9 non-functional
    s = dk.new_slide("Non-functional testing")
    ci = [r for r in W.circulars["CIRC-2025-02"]["requirements"] if r["para"] == "3.1"][0]
    rows = [["Area", "Target", "Source"],
            ["Availability", "SLO 99.5% for claim-core-svc", "ADR-024"],
            ["Fraud scoring", "Sentinel REST timeout 800 ms; fall back to batch scoring", "ADR-013"],
            ["Payment resilience", "Impact tolerance of 48 hours for claims payment disruption", "NISA Circular 2025/02 §3.1"],
            ["Failover", "Primary ocp-prd-lon1, DR ocp-dr-lds1", "ADR-006"]]
    assert "48 hours" in ci["text"]
    dk.table(s, rows, col_w=[2.4, 6.6, 3.0], size=14, row_h=0.65, name="NFR targets")
    dk.fact("general", "Availability target: SLO 99.5% for claim-core-svc (ADR-024).", 9, "table",
            "SLO 99.5% for claim-core-svc", world_ref="ADR:ADR-024")
    dk.fact("general", "Sentinel REST scoring timeout 800 ms with fallback to batch scoring (ADR-013).", 9, "table",
            "Sentinel REST timeout 800 ms", world_ref="ADR:ADR-013")
    dk.fact("general", "Impact tolerance of 48 hours for claims payment disruption (NISA Circular 2025/02 §3.1).", 9,
            "table", "Impact tolerance of 48 hours for claims payment disruption",
            world_ref="CIRCULAR:CIRC-2025-02#requirements")
    # 10 rules as configuration
    s = dk.new_slide("Testing rules held as configuration")
    dk.bullets(s, ["Business rules are versioned configuration, not a rules engine (ADR-010)",
                   "Every threshold change ships with examples agreed by the rule owner",
                   "Tiering is now served by triage-svc rather than a shared library (ADR-030)",
                   "Regression packs include boundary values either side of each threshold"], size=16)
    dk.fact("general", "The shared tier library was replaced by the triage-svc API (ADR-030).", 10, "text",
            "Tiering is now served by triage-svc rather than a shared library (ADR-030)", world_ref="ADR:ADR-030")
    # 11 defects (table image)
    s = dk.new_slide("Defect severities")
    png = R.table_image([["Severity", "Meaning", "Release impact"],
                         ["Sev1", "Service unusable or data corrupted", "Blocks release"],
                         ["Sev2", "Major function impaired, no workaround", "Blocks unless waived"],
                         ["Sev3", "Function impaired with workaround", "Planned fix"],
                         ["Sev4", "Cosmetic", "Backlog"]], [220, 620, 420], title="Severity definitions", size=26,
                        row_h=56)
    dk.picture(s, png, CONTENT_LEFT + 0.8, CONTENT_TOP, w=10.6, alt="Table of defect severity definitions.",
               name="severity-image")
    dk.fact("image_table", "Severity table image: Sev2 (major function impaired, no workaround) blocks release unless "
                           "waived.", 11, "image", "Blocks unless waived")
    # 12 roles
    s = dk.new_slide("Test roles")
    rows = [["Role", "Name", "Organisation"],
            ["Test strategy owner", W.name_of("P053", d), "IBM"],
            ["Business test lead", W.name_of("P054", d), "IBM"],
            ["Migration test lead", W.name_of("P051", d) + " (IBM, Data Migration Lead)", "IBM"],
            ["Product owner acceptance", W.name_of("P017", d), "Corvane"],
            ["Release approval", W.name_of("P032", d), "Corvane"]]
    dk.table(s, rows, col_w=[3.4, 5.6, 3.0], size=14, row_h=0.6, name="Test roles")
    dk.fact("general", "The migration test lead is Callum Fairbairn of IBM (Data Migration Lead), not the Corvane "
                       "namesake.", 12, "table", "Migration test lead Callum Fairbairn (IBM, Data Migration Lead)",
            world_ref="PERSON:P051")
    # 13 entry/exit (table image)
    s = dk.new_slide("Entry and exit criteria")
    png = R.table_image([["Stage", "Entry", "Exit"],
                         ["SIT", "Build deployed, smoke tests pass", "No open Sev1 or Sev2"],
                         ["UAT", "SIT exit met, test data loaded", "Business sign-off recorded"],
                         ["Dress rehearsal", "UAT exit met, cut-over plan approved", "Reconciliation signed off"]],
                        [300, 520, 520], title="Entry and exit criteria", size=26, row_h=56)
    dk.picture(s, png, CONTENT_LEFT + 0.8, CONTENT_TOP, w=10.6, alt="Table of entry and exit criteria per stage.",
               name="criteria-image")
    # 14 risks
    risks_slide(dk, k=5)
    return dk


# =========================================================================================
# VS028 Programme Skerry Kick-off (2025-01-13)
# =========================================================================================
def build_vs028(W, out_dir):
    fid = "VS028"
    dk = Deck(W, fid, out_dir, short_title="Programme Skerry Kick-off")
    d = dk.date
    mt = W.meetings["MTG-001"]
    assert mt["date"] == d
    C = W.company
    guard(W, fid, [("PERSON:P047", None), ("MEETING:MTG-001", None), ("DECISION:DEC-001", None),
                   ("ORG:company", "programme.budget_gbp_m"), ("COMMITTEE:COM-03", "cadence"),
                   ("COMMITTEE:COM-05", "cadence"), ("SYSTEM:SYS01", "go_live"), ("SYSTEM:SYS01", "decommission_target")])
    assert W.alias_holder("the CFO", d) == "P002"

    s = dk.title_slide("Programme Skerry Kick-off", "CLARA to Claims Hub modernisation",
                       [f"{fmt_date(d)}  |  Corvane House, London  |  Classification: Internal",
                        "Corvane Mutual and IBM Consulting"])
    dk.notes(s, "Welcome. Kick-off on 13 January 2025 led by Victoria Ashcombe (IBM engagement partner), with "
                "Duncan Ferrier as executive sponsor. Introductions round the table first.")
    dk.fact("speaker_notes", "Speaker notes: kick-off on 13 January 2025 led by Victoria Ashcombe (IBM engagement "
                             "partner).", 1, "notes",
            "Kick-off on 13 January 2025 led by Victoria Ashcombe (IBM engagement partner)", placement="PL-127")
    # 2 agenda
    dk.agenda_slide(["Why we are here", "Business case and objectives", "Approach: strangler fig and waves",
                     "Governance and team", "Roadmap and first 90 days", "Ways of working and risks"],
                    title=f"Agenda ({mt['start_time']}–11:30)")
    # 3 why
    s = dk.new_slide("Why we are here")
    sys01 = W.systems["SYS01"]
    dk.bullets(s, [f"CLARA has run Corvane's claims since {fmt_date(sys01['go_live'])} on COBOL, CICS and DB2",
                   "Scarce mainframe skills and long change lead times",
                   "Rules are buried in code and hard to evidence to the regulator",
                   f"Decommission target for CLARA: {fmt_date(sys01['decommission_target'])}"], size=17)
    dk.fact("general", "CLARA went live on 3 October 1994.", 3, "text", "since 3 October 1994",
            world_ref="SYSTEM:SYS01#go_live")
    dk.fact("general", "CLARA decommission target: 30 September 2027.", 3, "text",
            "Decommission target for CLARA: 30 September 2027", world_ref="SYSTEM:SYS01#decommission_target")
    # 4 business case and objectives
    s = dk.new_slide("Business case and objectives")
    cfo = W.alias_holder("the CFO", d)
    dk.text(s, CONTENT_LEFT, CONTENT_TOP, 5.8, 3.5,
            [f"Business case signed on {fmt_date(C['programme']['business_case_date'])} by the CFO, "
             f"{W.name_of(cfo, d)}", f"Budget: £{C['programme']['budget_gbp_m']}m",
             f"Executive sponsor: {person(W, 'P004', d)}", "Engagement partner: IBM Consulting"],
            size=16, bullets=True, para_space=12)
    dk.text(s, 6.8, CONTENT_TOP, 6.0, 4.8, PH.pick(dk.rng, PH.OBJECTIVES, 5), size=15, bullets=True, para_space=10)
    dk.fact("general", "The Programme Skerry business case was signed on 18 November 2024 by the CFO, Gareth Whitcombe.",
            4, "text", "Business case signed on 18 November 2024 by the CFO, Gareth Whitcombe",
            world_ref="ORG:company#programme.business_case_signed_by")
    dk.fact("general", "Programme Skerry budget: £48.6m.", 4, "text", "Budget: £48.6m",
            world_ref="ORG:company#programme.budget_gbp_m")
    dk.fact("general", "Executive sponsor is Duncan Ferrier (Chief Operating Officer).", 4, "text",
            "Executive sponsor: Duncan Ferrier (Chief Operating Officer)", world_ref="ORG:company#programme.executive_sponsor")
    # 5 approach (connectors)
    s = dk.new_slide("Approach: strangler fig, wave by wave", "Capabilities move one slice at a time")
    clara = dk.box(s, 0.6, 2.3, 2.6, 2.2, "CLARA", fill=GREY_LT, line=GREY, size=18, bold=True, name="app-clara")
    slices = ["FNOL and triage", "Assessment and reserves", "Fraud and settlement", "Recoveries"]
    sb = [dk.box(s, 4.6, 1.6 + i * 1.05, 3.2, 0.8, sl, size=13, bold=True, name=f"slice-{i + 1}")
          for i, sl in enumerate(slices)]
    hub = dk.box(s, 9.6, 2.3, 2.8, 2.2, "Claims Hub", fill=NAVY, line=None, color=WHITE, size=18, bold=True,
                 name="app-hub")
    for i, b in enumerate(sb):
        dk.connect(s, clara, b, 3, 1, width_pt=1.0, color=GREY)
        dk.connect(s, b, hub, 3, 1, label="MVP" if i == 0 else None, label_w=0.7, label_offset=(0, -0.3), width_pt=1.0)
    dk.text(s, CONTENT_LEFT, 6.1, CONTENT_W, 0.6,
            "CLARA remains the system of record for unmigrated claims until each wave cuts over.", size=13, color=GREY,
            italic=True)
    dk.fact("arrow_only", "The first slice moved to Claims Hub (the MVP) is FNOL and triage.", 5, "connector",
            "FNOL and triage -> Claims Hub [label: MVP]", world_ref="EVENT:EV-020")
    dk.notes(s, "Decision for today (DEC-001): adopt a strangler-fig, wave-based migration. The architecture "
                "decision record follows from the Design Authority.")
    dk.fact("speaker_notes", "Speaker notes: decision DEC-001 – adopt a strangler-fig, wave-based migration.", 5, "notes",
            "adopt a strangler-fig, wave-based migration", world_ref="DECISION:DEC-001")
    # 6 governance (connectors)
    s = dk.new_slide("Governance")
    com3 = W.committees["COM-03"]
    sc = dk.box(s, 4.6, 1.5, 4.0, 0.9, "Programme Skerry Steering Committee", fill=NAVY, line=None, color=WHITE, size=14,
                bold=True, name="gov-sc")
    spn = dk.box(s, 0.6, 1.5, 3.0, 0.9, f"Executive sponsor: {W.name_of('P004', d)}", size=12, bold=True,
                 name="gov-sponsor")
    da = dk.box(s, 9.6, 1.5, 3.0, 0.9, "Design Authority", size=13, bold=True, name="gov-da")
    pdl = dk.box(s, 2.6, 3.3, 3.2, 0.9, f"Programme Delivery Lead: {W.name_of('P048', d)}", size=11, bold=True,
                 name="gov-pdl")
    po = dk.box(s, 7.4, 3.3, 3.2, 0.9, f"Claims Hub Product Owner: {W.name_of('P017', d)}", size=11, bold=True,
                name="gov-po")
    sq = dk.box(s, 4.6, 5.0, 4.0, 0.9, "Joint Corvane and IBM squads", fill=GREY_LT, line=GREY, size=13, bold=True,
                name="gov-squads")
    dk.connect(s, spn, sc, 3, 1, label="chairs", label_w=0.8, label_offset=(0, -0.32))
    dk.connect(s, sc, pdl, 2, 0, label="delivery", label_w=0.9, label_offset=(-0.5, -0.1))
    dk.connect(s, sc, po, 2, 0, label="priorities", label_w=1.0, label_offset=(0.5, -0.1))
    dk.connect(s, da, sc, 1, 3, label="architecture decisions", label_w=1.9, label_offset=(0, -0.32))
    dk.connect(s, pdl, sq, 2, 0)
    dk.connect(s, po, sq, 2, 0)
    dk.text(s, CONTENT_LEFT, 6.1, CONTENT_W, 0.6,
            f"Steering Committee: {com3['cadence']}. Design Authority: {W.committees['COM-05']['cadence']}.",
            size=12, color=GREY)
    dk.fact("arrow_only", "The executive sponsor (Duncan Ferrier) chairs the Programme Skerry Steering Committee.", 6,
            "connector", "Executive sponsor: Duncan Ferrier -> Programme Skerry Steering Committee [label: chairs]",
            world_ref="COMMITTEE:COM-03#chair_history")
    dk.fact("general", "The Steering Committee meets monthly, second Thursday, 14:00 UK time.", 6, "text",
            "Steering Committee: monthly, second Thursday, 14:00 UK time", world_ref="COMMITTEE:COM-03#cadence")
    # 7 team (groups)
    s = dk.new_slide("Who is who")
    ibm = ["P047", "P048", "P049", "P050", "P051", "P052", "P053", "P054"]
    cmi = ["P004", "P005", "P006", "P017", "P032", "P016", "P018"]
    for gi, (gname, pids) in enumerate([("IBM Consulting", ibm), ("Corvane Mutual", cmi)]):
        g = dk.group(s, f"grp-team-{gi + 1}")
        x0 = CONTENT_LEFT + gi * 6.2
        dk.box(s, x0, CONTENT_TOP + 0.05, 6.0, 0.5, gname, shape=MSO_SHAPE.RECTANGLE, fill=NAVY, line=None, color=WHITE,
               size=14, bold=True, group=g, name=f"team-hdr-{gi + 1}")
        for k, pid in enumerate(pids):
            col, row = k % 2, k // 2
            dk.box(s, x0 + col * 3.02, CONTENT_TOP + 0.7 + row * 1.15, 2.95, 1.05,
                   [W.name_of(pid, d), W.title_of(pid, d)], fill=TEAL_LT, line=None, size=12, bold=True, group=g,
                   name=f"team-{pid}")
    dk.fact("visual_only", "IBM team: Callum Fairbairn is the Data Migration Lead.", 7, "group",
            "Callum Fairbairn Data Migration Lead", world_ref="PERSON:P051#titles", shape_name="grp-team-1")
    dk.fact("visual_only", "IBM team: Gordon Sproat is the Mainframe Modernisation SME.", 7, "group",
            "Gordon Sproat Mainframe Modernisation SME", world_ref="PERSON:P052#titles", shape_name="grp-team-1")
    dk.fact("visual_only", "Aisha Siddiqui is the Claims Hub Product Owner (January 2025).", 7, "group",
            "Aisha Siddiqui Claims Hub Product Owner", world_ref="PERSON:P017#titles", shape_name="grp-team-2")
    # 8 roadmap raster
    s = dk.new_slide("Roadmap")
    cv = R.Canvas(1700, 700)
    cv.title("Programme Skerry roadmap (indicative)")
    phases = [("Mobilise", ["Q1 2025", "teams and plan"], R.TEAL),
              ("Foundations", ["platform", "CI/CD, identity"], R.NAVY),
              ("MVP", ["FNOL and triage", "target Nov 2025"], R.TEAL),
              ("Waves", ["by region", "2026–2027"], R.NAVY),
              ("Decommission", ["CLARA", "target Sep 2027"], R.GREY)]
    x = 60
    for i, (ph, sub, col) in enumerate(phases):
        w = 300
        cv.d.polygon([(x, 200), (x + w, 200), (x + w + 40, 280), (x + w, 360), (x, 360), (x + 40, 280)], fill=col)
        cv.text((x + w / 2 + 20, 255), ph, size=30, bold=True, fill=R.WHITE, anchor="ma")
        for j, ln in enumerate(sub):
            cv.text((x + 20, 400 + j * 40), ln, size=26, fill=R.BLACK)
        x += w + 20
    cv.arrow((80, 600), (1620, 600), label="CLARA remains system of record for unmigrated claims", label_size=24,
             color=R.GREY)
    dk.picture(s, cv.png(), CONTENT_LEFT, CONTENT_TOP + 0.1, w=CONTENT_W,
               alt="Roadmap chevrons from mobilisation through MVP and migration waves to CLARA decommissioning.",
               name="roadmap-image")
    dk.fact("image_text", "Roadmap image: MVP (FNOL and triage) target November 2025.", 8, "image",
            "target Nov 2025", world_ref="TIMELINE:programme#mvp")
    dk.fact("alt_text", "Alt text: roadmap runs from mobilisation through MVP and waves to CLARA decommissioning.", 8,
            "alt_text", "from mobilisation through MVP and migration waves to CLARA decommissioning")
    # 9 first 90 days
    s = dk.new_slide("The first 90 days")
    dk.bullets(s, ["Stand up the Design Authority and record the first architecture decisions",
                   "Agree the target platform and event backbone",
                   "Map CLARA programs, interfaces and rules with the CLARA team",
                   "Shape the MVP backlog with Claims Operations",
                   "Agree the data migration approach and the first wave"], size=16)
    # 10 ways of working
    s = dk.new_slide("Ways of working")
    dk.bullets(s, PH.pick(dk.rng, PH.WAYS_OF_WORKING, 6), size=16)
    # 11 risks
    risks_slide(dk, title="Early risks", k=5)
    # 12 attendees and next steps
    s = dk.new_slide("Today's attendees and next steps")
    rows = [["Attendee", "Role"]] + [[W.name_of(p, d), W.title_of(p, d)] for p in mt["attendees"]]
    dk.table(s, rows, x=CONTENT_LEFT, w=6.4, col_w=[2.6, 3.8], size=12, row_h=0.45, name="Attendees")
    dk.text(s, 7.3, CONTENT_TOP + 0.1, 5.5, 4.5, PH.pick(dk.rng, PH.NEXT_STEPS, 4), size=15, bullets=True,
            para_space=12)
    dk.fact("general", "Gareth Whitcombe (Chief Financial Officer) attended the Programme Skerry kick-off.", 12, "table",
            "Gareth Whitcombe Chief Financial Officer", world_ref="MEETING:MTG-001#attendees")
    return dk
