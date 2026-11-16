"""LD021: Claims Assessor Field Guide and Photo Atlas (2025 edition): image-heavy PDF, 25-40 MB.

Layout: A4 portrait, reportlab platypus. Photographs are procedural JPEGs (atlas_img) embedded as
DCT streams, so the PDF size is essentially the sum of the JPEG sizes. Three exclusive facts exist only
inside raster images (verified with Apple Vision OCR via harness/extract.py):
    PL-060  Plate 4.4 caption: gradual-leak moisture threshold (BR-ASM-011 v1)
    PL-062  Plate 7.3 caption: subsidence crack width referral (BR-ASM-012 v1)
    PL-061  Table B.1 image: Norrvik Skadetaxering fee schedule (VEN-02 fees)
"""
from __future__ import annotations

import datetime as dt
import shutil

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)

from . import atlas_img as AI
from . import atlas_text as AT
from .common import CACHE, W, Deck, Facts, anchor, guard, long_date, out_path, person, placements, util

FID = "LD021"
PAGE_W, PAGE_H = A4
ML = MR = 18 * mm
MT, MB = 22 * mm, 20 * mm
FW = PAGE_W - ML - MR
FH = PAGE_H - MT - MB
TEAL = colors.HexColor("#0B4F6C")
INK = colors.HexColor("#1B1B1B")
GREY = colors.HexColor("#5C5C5C")
TARGET_MB = (25.0, 40.0)
PLATE_H = 1050          # 2-up plates: 1800 x 1050 photos (+ caption band)
QUALITY = 70

WORK = CACHE / "atlas"


def _styles():
    s = {}
    s["body"] = ParagraphStyle("body", fontName="Helvetica", fontSize=9.6, leading=13.4, spaceAfter=5, textColor=INK)
    s["ul"] = ParagraphStyle("ul", parent=s["body"], leftIndent=14, bulletIndent=3, spaceAfter=2.5)
    s["h1"] = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=19, leading=23, spaceBefore=6, spaceAfter=8,
                             textColor=TEAL)
    s["h2"] = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=14.5, spaceBefore=8,
                             spaceAfter=4, textColor=TEAL)
    s["cap"] = ParagraphStyle("cap", fontName="Helvetica-Oblique", fontSize=8.2, leading=10.4, spaceBefore=2,
                              spaceAfter=7, textColor=GREY)
    s["rule"] = ParagraphStyle("rule", fontName="Helvetica", fontSize=9.2, leading=12.4, textColor=INK)
    s["cell"] = ParagraphStyle("cell", fontName="Helvetica", fontSize=8.8, leading=11.2)
    s["cellb"] = ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8.8, leading=11.2, textColor=colors.white)
    s["toc"] = ParagraphStyle("toc", fontName="Helvetica", fontSize=10.5, leading=18)
    s["toc_b"] = ParagraphStyle("toc_b", parent=s["toc"], fontName="Helvetica-Bold")
    s["note"] = ParagraphStyle("note", parent=s["body"], fontName="Helvetica-Oblique", textColor=GREY)
    return s


# ---------------------------------------------------------------------------------------------
# World values
# ---------------------------------------------------------------------------------------------

def _rule(rid, when):
    v = W.rule_version(rid, when)
    ref = f"{rid}@v{v['version']}"
    if not W.may_state(FID, ref, "text"):
        raise RuntimeError(f"{FID} may not state {ref}")
    return {"id": rid, "version": v["version"], "text": v["text"], "ref": ref,
            "box": f"<b>{rid} (v{v['version']})</b> – {v['text']}"}


def world_values(when):
    V = {}
    gl = next(g for g in (W.glossary.values() if isinstance(W.glossary, dict) else W.glossary) if g["id"] == "G-001")
    d = gl["definition"]
    V["assessor_def"] = "a " + d[0].lower() + d[1:]
    V["t06"], V["t07"] = W.team_name("T06", when), W.team_name("T07", when)
    for vid, key in (("VEN-01", "ven01"), ("VEN-02", "ven02"), ("VEN-04", "ven04"), ("VEN-09", "ven09")):
        guard(FID, f"VENDOR:{vid}", "role")
        V[key] = W.vendors[vid]["name"]
    V["ven02_full"] = W.vendors["VEN-02"]["name"]
    V["ven02_loc"] = W.vendors["VEN-02"]["location"]
    c = W.vendors["VEN-02"]["contact"]
    V["ven02_contact"] = f"{W.name_of(c, when)}, {W.title_of(c, when)}"
    V["portal"] = W.system_name("SYS17", when)
    ren = W.systems["SYS17"]["renames"][0]
    assert ren["date"] <= when
    V["portal_old"], V["portal_rename"] = ren["from_name"], long_date(ren["date"])
    V["vault"] = W.system_name("SYS05", when)
    V["vault_old"] = W.systems["SYS05"]["renames"][0]["from_name"]
    V["gateway"] = W.system_name("SYS13", when)
    rules = {}
    for i in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19):
        rid = f"BR-ASM-{i:03d}"
        rules[rid] = _rule(rid, when)
        V[f"r_asm{i:03d}"] = rules[rid]["box"]
    V["_rules"] = rules
    return V


# ---------------------------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------------------------

class ImgStore:
    def __init__(self):
        if WORK.exists():
            shutil.rmtree(WORK)
        WORK.mkdir(parents=True)
        self.n = 0
        self.jpegs = []   # (path, PIL image) kept for re-encoding if the size target is missed

    def jpeg(self, name, img):
        p = WORK / f"{name}.jpg"
        AI.save_jpeg(img, p, quality=QUALITY)
        self.jpegs.append((p, img))
        return p

    def png(self, name, img):
        p = WORK / f"{name}.png"
        AI.save_png(img, p)
        return p

    def total(self):
        return sum(p.stat().st_size for p in WORK.iterdir())

    def requality(self, q):
        for p, img in self.jpegs:
            AI.save_jpeg(img, p, quality=q)


def _flow_img(path, width_mm):
    from PIL import Image as PI
    with PI.open(path) as im:
        w, h = im.size
    return Image(str(path), width=width_mm * mm, height=width_mm * mm * h / w)


# ---------------------------------------------------------------------------------------------
# Figures (diagrams and tables as images)
# ---------------------------------------------------------------------------------------------

def make_figures(V, store):
    R = V["_rules"]
    F = {}
    F["fig1_1"] = ("Figure 1.1  The assessment journey", AI.flow_diagram(
        "The assessment journey", [
            ("tri", (0.03, 0.18, 0.25, 0.36), "Triage", "start"),
            ("app", (0.37, 0.18, 0.63, 0.36), "Appoint Claims Assessor", None),
            ("ins", (0.74, 0.18, 0.97, 0.36), "Inspect or desk-assess", None),
            ("rep", (0.74, 0.58, 0.97, 0.76), "Assessor report", None),
            ("dec", (0.37, 0.58, 0.63, 0.76), "Coverage decision", "decision"),
            ("est", (0.03, 0.58, 0.25, 0.76), "Estimate and recovery potential", "end"),
        ], [("tri", "app", "Tier-2 > £10,000: panel"), ("app", "ins", "5 business days"),
            ("ins", "rep", "report in 5 business days"), ("rep", "dec", "3 business days"), ("dec", "est", None)]),
        "fig")
    F["fig3_1"] = ("Figure 3.1  Wide, mid and close-up sequence", AI.flow_diagram(
        "Photo sequence for each area of damage", [
            ("w", (0.03, 0.3, 0.3, 0.6), "1. Wide shot: whole room or elevation", "start"),
            ("m", (0.37, 0.3, 0.63, 0.6), "2. Mid shot: item in context", None),
            ("c", (0.7, 0.3, 0.97, 0.6), "3. Close-up with scale reference", "end"),
        ], [("w", "m", None), ("m", "c", None)], size=(1800, 700)), "fig")
    F["fig4_1"] = ("Figure 4.1  Moisture meter probe positions", AI.wall_diagram(
        "Moisture meter probe positions (wall elevation)", [
            ("A", (0.62, 0.95), "skirting below the pipe run"), ("B", (0.62, 0.55), "wall at mid height"),
            ("C", (0.62, 0.15), "wall below the ceiling"), ("D", (0.35, 0.95), "skirting at the door"),
            ("E", (0.08, 0.95), "reference: unaffected skirting"), ("F", (0.9, 0.95), "corner at the outside wall")]),
        "fig")
    F["fig5_1"] = ("Figure 5.1  V-pattern pointing to the origin", AI.vpattern_diagram(
        "Burn pattern on a wall (V-pattern)", ["The V narrows towards the origin.", "Deepest charring at the base.",
                                               "Smoke spreads at ceiling level.", "Photograph the pattern in full.",
                                               "Retain items found at the origin."]), "fig")
    F["fig7_1"] = ("Figure 7.1  Typical subsidence crack pattern", AI.house_diagram(
        "Typical subsidence crack pattern (front elevation)", [
            "Diagonal cracks from window corners", "Cracks taper along their length", "Same crack inside and out",
            "Doors and windows stick", "Check trees and drains nearby"]), "fig")
    F["fig9_1"] = ("Figure 9.1  Vehicle panel identification", AI.car_diagram(
        "Vehicle panel identification (nearside)", [
            ("P1", (260, 560), "front bumper"), ("P2", (480, 450), "front wing"), ("P3", (740, 480), "front door"),
            ("P4", (1030, 480), "rear door"), ("P5", (1400, 520), "rear quarter"), ("P6", (1600, 600), "rear bumper"),
            ("P7", (820, 330), "roof"), ("P8", (980, 640), "sill")]), "fig")
    F["fig10_1"] = ("Figure 10.1  Nordic home claims: when an on-site takst is needed", AI.flow_diagram(
        "Nordic home claims: on-site takst", [
            ("n", (0.03, 0.35, 0.27, 0.6), "Nordic home claim notified", "start"),
            ("q", (0.37, 0.3, 0.63, 0.65), "Claim above NOK 120,000?", "decision"),
            ("y", (0.73, 0.12, 0.97, 0.38), "On-site takst required", "end"),
            ("o", (0.73, 0.6, 0.97, 0.86), "Route by claim type", None),
        ], [("n", "q", None), ("q", "y", "Yes"), ("q", "o", "No")], size=(1800, 850)), "fig")
    assert R["BR-ASM-009"]["text"].find("120000") >= 0 or True
    F["tab2_1"] = ("Table 2.1  Site hazard checklist", AI.table_image(
        "Site hazard checklist", [
            ("Hazard", "Signs", "Action"),
            ("Weakened ceiling", "Sagging, bulging or saturated boards", "Do not enter; ask for the ceiling to be made safe"),
            ("Unsafe floor", "Charring, missing boards, soft spots", "Keep to the edges; do not enter if in doubt"),
            ("Electrical", "Wet sockets, burnt cables, tripped supply", "Ask for the supply to be isolated"),
            ("Contamination", "Flood water, sewage, mould", "Gloves, wash before eating, limit time on site"),
            ("Possible asbestos", "Old textured coatings, insulation boards", "Do not disturb; photograph from a distance"),
            ("Working at height", "Roof damage, high ceilings", "Do not climb; use a pole camera"),
            ("People and animals", "Aggression, loose dogs", "Leave; arrange a joint visit"),
        ], [22, 34, 44]), "tab")
    F["tab3_1"] = ("Table 3.1  Minimum photo set by type of loss", AI.table_image(
        "Minimum photo set by type of loss", [
            ("Type of loss", "Photographs expected"),
            ("Every report", f"At least {R['BR-ASM-004']['text'].split('at least ')[1].split(' ')[0]} photos, "
                             "including wide, mid and close-up views"),
            ("Escape of water", "Source of the escape, staining, meter displays, flooring and voids"),
            ("Fire and smoke", "Origin, burn patterns, smoke spread, appliances at the origin"),
            ("Storm", "Each elevation, roof slopes, displaced materials, neighbouring properties"),
            ("Subsidence", "Each crack with a gauge, door and window frames, trees and drains"),
            ("Theft", "Point of entry, tool marks, locks, damaged frames"),
            ("Motor", "Four corners, damage close-ups, odometer, VIN plate, third-party damage"),
        ], [28, 72]), "tab")
    F["tab4_2"] = ("Table 4.2  Drying monitoring record", AI.table_image(
        "Drying monitoring record", [
            ("Visit", "Date", "Location", "Reading", "Equipment", "Initials"),
            ("1", "", "", "", "", ""), ("2", "", "", "", "", ""), ("3", "", "", "", "", ""),
            ("4", "", "", "", "", ""), ("5", "", "", "", "", ""), ("6", "", "", "", "", ""),
        ], [10, 16, 26, 16, 20, 12], note=f"{R['BR-ASM-019']['text']} Record each reading against the same "
                                          "location on every visit."), "tab")
    F["tab6_1"] = ("Table 6.1  Storm and flood evidence record", AI.table_image(
        "Storm and flood evidence record", [
            ("Item", "Record"),
            ("Date and time of loss", "As stated by the customer"),
            ("Weather records", "Source checked and summary of conditions"),
            ("Flood depth inside", "Measured from finished floor level"),
            ("Flood depth outside", "Measured from ground level"),
            ("Source of water", "River, surface water, drain or other"),
            ("Neighbouring properties", "Similar damage observed: yes or no"),
            ("Condition before loss", "Wear and tear, previous repairs"),
        ], [36, 64]), "tab")
    F["tab7_2"] = ("Table 7.2  Crack monitoring record", AI.table_image(
        "Crack monitoring record", [
            ("Crack ref", "Location", "Date", "Width", "Length", "Direction", "Initials"),
            ("C1", "", "", "", "", "", ""), ("C2", "", "", "", "", "", ""), ("C3", "", "", "", "", "", ""),
            ("C4", "", "", "", "", "", ""), ("C5", "", "", "", "", "", ""),
        ], [12, 24, 14, 12, 12, 14, 12], note="Measure at the marked point with a crack width gauge. Record the widest "
                                             "point and photograph the gauge in place."), "tab")
    r8, r17 = R["BR-ASM-008"], R["BR-ASM-017"]
    F["tab9_1"] = ("Table 9.1  Motor assessment routes", AI.table_image(
        "Motor assessment routes", [
            ("Situation", "Route"),
            ("Windscreen claim", R["BR-ASM-001"]["text"]),
            ("Estimate below £3,000", "Desk assessment from at least 6 photos received through the "
                                      f"{V['gateway']}"),
            ("Own-damage repair", R["BR-ASM-007"]["text"]),
            ("Repair cost above 65% of market value", "Total loss"),
            ("Structural damage suspected", "Physical inspection"),
        ], [36, 64]), "tab")
    assert "3,000" in r8["text"] and "65%" in r17["text"]
    F["tab11_1"] = ("Table 11.1  Assessment timescales", AI.table_image(
        "Assessment timescales", [
            ("Step", "Timescale", "Rule"),
            ("External Claims Assessor appointed (Tier-2 property above £10,000)", "Within 2 business days of triage",
             "BR-ASM-002"),
            ("Site inspection", "Within 5 business days of appointment (Tier-3: 72 hours)", "BR-ASM-005"),
            ("Assessor report", "Within 5 business days of inspection", "BR-ASM-006"),
            ("Coverage decision letter", "Within 3 business days of the assessor report", "BR-ASM-013"),
            ("Re-inspection", "When the estimate rises by more than 25%", "BR-ASM-014"),
        ], [34, 52, 14]), "tab")
    for k, v in (("BR-ASM-002", "within 2 business days"), ("BR-ASM-005", "(Tier-3: 72 hours)"),
                 ("BR-ASM-006", "5 business days"), ("BR-ASM-013", "3 business days"), ("BR-ASM-014", "25%"),
                 ("BR-ASM-009", "120000"), ("BR-ASM-004", "at least 6 photos")):
        assert v in R[k]["text"], (k, v)
    out = {}
    for k, (cap, img, kind) in F.items():
        out[k] = (cap, store.png(k, img))
    return out


# ---------------------------------------------------------------------------------------------
# Exclusive raster facts
# ---------------------------------------------------------------------------------------------

def exclusive_captions():
    r11 = W.rule_version("BR-ASM-011", "2025-11-03")
    r12 = W.rule_version("BR-ASM-012", "2025-11-03")
    wme = r11["parameters"]["moisture_wme_pct"]
    mm_ = r12["parameters"]["crack_width_mm"]
    leak = (f"Pin meter reading in skirting timber beside the shower tray. A moisture reading of {wme}% WME or more "
            f"indicates a gradual leak, not a sudden escape of water. Photograph the meter display.")
    crack = (f"Diagonal crack above the kitchen window, measured with a crack width gauge. Subsidence cracks wider "
             f"than {mm_} mm require referral to a structural engineer before cover is confirmed.")
    return {"GRADUAL_LEAK_PLATE": ("Pin meter reading at skirting level beside a shower tray", leak,
                                   f"a moisture reading of {wme}% WME or more indicates a gradual leak", wme),
            "CRACK_REFERRAL_PLATE": ("Diagonal crack above a kitchen window", crack,
                                     f"Subsidence cracks wider than {mm_} mm require referral to a structural engineer",
                                     mm_)}


def norrvik_table():
    v = W.vendors["VEN-02"]
    f = v["fees"]
    rows = [("Service", "Country", "Fee per instruction"),
            ("Desk assessment", "Sweden", f"SEK {f['desk_assessment_sek']:,}"),
            ("Site visit", "Sweden", f"SEK {f['site_visit_sek']:,}"),
            ("Site visit", "Norway", f"NOK {f['site_visit_nok']:,}")]
    img = AI.table_image(f"{v['name']} – fee schedule", rows, [40, 25, 35], font_px=44,
                         note="Fees per instruction as agreed in the panel contract.")
    needles = {"desk": f"SEK {f['desk_assessment_sek']:,}", "site_se": f"SEK {f['site_visit_sek']:,}",
               "site_no": f"NOK {f['site_visit_nok']:,}"}
    return img, needles


# ---------------------------------------------------------------------------------------------
# Reference collection (Part B) phrase banks
# ---------------------------------------------------------------------------------------------

REF_BANK = {
    "water_stain": (["Ceiling below a bathroom", "Kitchen ceiling", "Landing ceiling", "Bedroom wall",
                     "Hall ceiling", "Utility room wall", "Stairwell wall", "Ceiling below a cold tank"],
                    ["staining with a single sharp edge", "faint tide marks at the edge of the stain",
                     "staining spreading from a light fitting", "a stain following the line of a joist",
                     "discolouration around a ceiling rose", "bubbled paint over damp plaster",
                     "a brown stain with a darker outer ring"]),
    "fire_char": (["Kitchen wall", "Lounge door lining", "Stair stringer", "Loft timbers", "Garage roof"],
                  ["deep charring with cracked surface", "shallow charring and heat discolouration",
                   "charring heaviest at low level", "blistered paint around the charred area"]),
    "smoke": (["Lounge ceiling", "Bedroom ceiling", "Hall ceiling", "Kitchen ceiling"],
              ["light smoke deposit", "heavy soot along the joist lines", "smoke staining from a doorway",
               "oily soot from burning plastics"]),
    "crack": (["Bedroom wall", "Hall wall", "Kitchen wall", "Stairwell wall", "Lounge ceiling"],
              ["hairline crack in the plaster finish", "crack running from a door head",
               "crack with fresh dust on the sill", "crack following a board joint"]),
    "brick": (["Rear elevation", "Side elevation", "Front elevation", "Garden wall"],
              ["stepped cracking through the mortar joints", "cracked brick below a window sill",
               "open perpend joints", "crack widening towards the eaves"]),
    "flood": (["Ground-floor hall", "Kitchen", "Garage", "Lounge"],
              ["tide line with silt deposit", "staining up to the window sill level",
               "plaster blown below the tide line"]),
    "roof": (["Front roof slope", "Rear roof slope", "Garage roof", "Porch roof"],
             ["displaced tiles along the eaves", "slipped slates with broken nails", "lifted ridge tiles",
              "moss growth on old tiles"]),
    "door": (["Back door", "Patio door frame", "Garage side door", "Front door"],
             ["splintered lining at the lock", "jemmy marks on the frame", "damaged keep and screws pulled out"]),
    "floor": (["Kitchen floor", "Bathroom floor", "Hall floor", "Dining room floor"],
              ["cupped boards", "stained board edges", "swollen chipboard sheets"]),
    "panel": (["Nearside front wing", "Offside rear door", "Tailgate", "Bonnet", "Roof panel", "Front bumper"],
              ["dent with paint creasing", "scrape with paint transfer", "dent without paint damage",
               "deep scratch through the clear coat", "panel misalignment"]),
    "glass": (["Windscreen", "Rear screen", "Nearside front window", "Sunroof"],
              ["star chip with short cracks", "long crack from the edge", "shattered toughened glass"]),
    "debris": (["Back garden", "Driveway", "Lounge floor", "Loft"],
               ["debris after a partial collapse", "fallen plaster", "storm debris against a fence"]),
}

REF_PERIL = {"water_stain": "escape of water", "fire_char": "fire", "smoke": "smoke", "crack": "cracking",
             "brick": "structural movement", "flood": "flood", "roof": "storm", "door": "forced entry",
             "floor": "water damage", "panel": "motor", "glass": "glass", "debris": "debris"}


# ---------------------------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------------------------

def _rule_box(text, S):
    t = Table([[Paragraph(text, S["rule"])]], colWidths=[FW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E7F1F5")),
                           ("LINEBEFORE", (0, 0), (0, -1), 3, TEAL), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return [t, Spacer(1, 6)]


def _table(rows, widths, S):
    data = [[Paragraph(str(c), S["cellb"] if i == 0 else S["cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), TEAL), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9BB7C4")),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def build():
    """Build LD021. Images are embedded without ASCII85 so the PDF size tracks the JPEG sizes."""
    from reportlab import rl_config
    old = rl_config.useA85
    rl_config.useA85 = 0
    try:
        return _build()
    finally:
        rl_config.useA85 = old


def _build():
    an = anchor(FID)
    when = an["date"]
    S = _styles()
    V = world_values(when)
    deck = Deck("LD021:text")
    store = ImgStore()
    figs = make_figures(V, store)
    excl = exclusive_captions()
    chaps = AT.chapters(V)
    author_n, author_t = person(an["author"], when)
    appr_n, appr_t = person("P011", when)
    nordic_n, nordic_t = person("P034", when)

    story = []
    plate_index = []     # (label, title, chapter)
    marks = {}           # tag -> label to find later

    # ---- cover (drawn by the page template) and document control
    cover_img = store.jpeg("cover", AI.photo("cover", "water_stain", "", None, size=(1800, 1630), grain_sigma=4.5))
    story += [NextPageTemplate("body"), PageBreak()]
    story.append(Paragraph("Document control", S["h1"]))
    ctl = [("Title", an["title"]), ("Edition", "2025 edition (replaces the 2022 edition)"),
           ("Approved", long_date(when)), ("Status", "Approved"),
           ("Document owner", f"{author_n}, {author_t}"), ("Approved by", f"{appr_n}, {appr_t}"),
           ("Nordic content", f"{nordic_n}, {nordic_t}"),
           ("Distribution", f"{V['t06']}; {V['t07']}; panel firms {V['ven01']} and {V['ven02']}"),
           ("Classification", "Internal – may be shared with panel firms")]
    t = Table([[Paragraph(f"<b>{a}</b>", S["cell"]), Paragraph(b, S["cell"])] for a, b in ctl],
              colWidths=[38 * mm, FW - 38 * mm])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#9BB7C4")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story += [t, Spacer(1, 12), Paragraph("Edition history", S["h2"])]
    story.append(_table([("Edition", "Summary of changes"),
                         ("2020 edition", "Field guide for internal and panel Claims Assessors, including the subsidence "
                                          "chapter (chapter 7)."),
                         ("2022 edition", "Escape of water chapter (chapter 4) revised with guidance on distinguishing "
                                          "sudden escapes from gradual leaks."),
                         ("2025 edition", f"Photo atlas plates added to every chapter. References updated to the "
                                          f"{V['portal']} and {V['vault']}. Nordic chapter expanded.")],
                        [32, FW / mm - 32], S))
    story += [Spacer(1, 12), Paragraph("Using this guide", S["h2"]),
              Paragraph("The guide is reviewed when assessment rules change. Plate captions are part of the guidance. "
                        "Where a rule is quoted, the rule identifier and version are shown so that assessors can check "
                        "the current version with their team leader.", S["body"]),
              PageBreak()]
    # ---- contents (filled on the second pass)
    toc_pos = len(story)
    story.append("__TOC__")
    story.append(PageBreak())

    # ---- chapters
    for ch in chaps:
        n = ch["num"]
        story.append(Spacer(1, 1))
        hero = store.jpeg(f"hero_{n}", AI.hero(f"hero{n}", ch["hero"]))
        story.append(_flow_img(hero, FW / mm))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Chapter {n}  {ch['title']}", S["h1"]))
        marks[f"ch{n}"] = f"Chapter {n}  {ch['title']}"
        for p in ch["intro"]:
            story.append(Paragraph(p, S["body"]))
        for h2, blocks in ch["sections"]:
            story.append(CondPageBreak(40 * mm))
            story.append(Paragraph(h2, S["h2"]))
            for b in blocks:
                if b[0] == "p":
                    story.append(Paragraph(b[1], S["body"]))
                elif b[0] == "ul":
                    for it in b[1]:
                        story.append(Paragraph(it, S["ul"], bulletText="•"))
                elif b[0] == "rule":
                    story += _rule_box(b[1], S)
        for kind, key in ch["figures"]:
            cap, path = figs[key]
            story.append(CondPageBreak(120 * mm))
            story.append(Spacer(1, 6))
            story.append(_flow_img(path, FW / mm))
            story.append(Paragraph(cap, S["cap"]))
        # plates
        plates = ch["plates"]
        k = 0
        pending = []
        for i, (tex, title, cap, opt) in enumerate(plates, 1):
            label = f"Plate {n}.{i}"
            if title in excl:
                ttl, cap, needle, _ = excl[title]
                marks[title] = label
                title = ttl
            plate_index.append((label, title, n))
            if opt.get("single") or i % 3 == 0:
                img = AI.photo(f"p{n}_{i}", tex, label, cap, overlay=opt.get("overlay"), meter=opt.get("meter"),
                               marker=opt.get("marker"), size=(AI.PHOTO_W, 1200), grain_sigma=4.5)
                path = store.jpeg(f"plate_{n}_{i}", img)
                notes = [deck.pick(AT.NOTES_BANK) for _ in range(3)]
                story += [PageBreak(), _flow_img(path, FW / mm), Paragraph(f"{label}  {title}", S["cap"]),
                          Paragraph("Assessor's notes", S["h2"])]
                story += [Paragraph(t_, S["ul"], bulletText="•") for t_ in notes]
                continue
            img = AI.photo(f"p{n}_{i}", tex, label, cap, overlay=opt.get("overlay"), meter=opt.get("meter"),
                           marker=opt.get("marker"), size=(AI.PHOTO_W, PLATE_H), grain_sigma=4.5)
            pending.append((store.jpeg(f"plate_{n}_{i}", img), label, title))
            if len(pending) == 2:
                story.append(PageBreak())
                for path, lab, ttl in pending:
                    story += [_flow_img(path, 160), Paragraph(f"{lab}  {ttl}", S["cap"])]
                pending = []
        if pending:
            story.append(PageBreak())
            for path, lab, ttl in pending:
                story += [_flow_img(path, 160), Paragraph(f"{lab}  {ttl}", S["cap"])]
        if n in AT.CASE_STUDIES:
            ttl, tex, paras = AT.CASE_STUDIES[n]
            img = AI.photo(f"case{n}", tex, f"Case study {n}", None, size=(AI.PHOTO_W, 1000), grain_sigma=4.5)
            story += [PageBreak(), Paragraph(f"Case study {n}  {ttl}", S["h1"]),
                      _flow_img(store.jpeg(f"case_{n}", img), FW / mm), Spacer(1, 8)]
            story += [Paragraph(p_, S["body"]) for p_ in paras]
        items = [it for _, blocks in ch["sections"] for b in blocks if b[0] == "ul" for it in b[1]][:8]
        if n >= 2 and items:
            rows = [("Check", "Done")] + [(it, "☐") for it in items]
            cimg = AI.table_image(f"Chapter {n} checklist: {ch['title']}", rows, [88, 12], font_px=32)
            story += [PageBreak(), Paragraph(f"Checklist  {ch['title']}", S["h1"]),
                      _flow_img(store.png(f"check_{n}", cimg), FW / mm),
                      Paragraph(f"Checklist {n}  Use on site or when reviewing the report", S["cap"])]
        story.append(PageBreak())

    # ---- Part B: reference collection (4-up grids)
    story.append(Paragraph("Reference collection", S["h1"]))
    marks["refs"] = "Reference collection"
    story.append(Paragraph("The reference collection contains further examples of damage grouped by peril. Each "
                           "photograph carries a short description. The collection is intended for comparison on site "
                           "and in training; the chapter guidance and plate captions take precedence.", S["body"]))
    rr = util.rng("LD021:refs")
    textures = list(REF_BANK)
    ref_n = 0
    grid = []
    for gi in range(REF_COUNT):
        tex = textures[gi % len(textures)]
        locs, obs = REF_BANK[tex]
        ref_n += 1
        label = f"R.{ref_n}"
        cap = f"{rr.choice(locs)}: {rr.choice(obs)}."
        img = AI.photo(f"ref{ref_n}", tex, label, cap, size=(1500, 1000), grain_sigma=4.5)
        grid.append((store.jpeg(f"ref_{ref_n}", img), label, f"{REF_PERIL[tex].capitalize()}"))
    for gi in range(0, len(grid), 2):
        story.append(PageBreak())
        for path, lab, per in grid[gi:gi + 2]:
            story += [_flow_img(path, 150), Paragraph(f"Reference plate {lab}  {per}", S["cap"])]
    story.append(PageBreak())

    # ---- appendices
    story.append(Paragraph("Appendix A  Measurement and conversion", S["h1"]))
    marks["appA"] = "Appendix A  Measurement and conversion"
    conv = AI.table_image("Units used in assessment reports", [
        ("Quantity", "Unit in reports", "Conversion"),
        ("Length", "millimetres (mm), metres (m)", "1 inch = 25.4 mm; 1 foot = 0.3048 m"),
        ("Area", "square metres (m²)", "1 square foot = 0.0929 m²"),
        ("Volume", "litres, cubic metres", "1 gallon (UK) = 4.546 litres"),
        ("Temperature", "degrees Celsius", "°F = °C × 9/5 + 32"),
        ("Moisture", "% WME (pin meter)", "Relative units on pinless meters"),
        ("Currency", "GBP, NOK, SEK, DKK", "As shown on the instruction"),
    ], [22, 34, 44])
    story += [_flow_img(store.png("tabA_1", conv), FW / mm), Paragraph("Table A.1  Units and conversions", S["cap"])]
    room = AI.table_image("Room measurement record", [
        ("Room", "Length (m)", "Width (m)", "Height (m)", "Floor area (m²)", "Notes"),
        ("", "", "", "", "", ""), ("", "", "", "", "", ""), ("", "", "", "", "", ""), ("", "", "", "", "", ""),
        ("", "", "", "", "", ""), ("", "", "", "", "", ""),
    ], [22, 14, 14, 14, 16, 20])
    story += [CondPageBreak(110 * mm), _flow_img(store.png("tabA_2", room), FW / mm),
              Paragraph("Table A.2  Room measurement record", S["cap"]), PageBreak()]

    story.append(Paragraph("Appendix B  Panel arrangements", S["h1"]))
    marks["appB"] = "Appendix B  Panel arrangements"
    story += [Paragraph(f"External Claims Assessors are appointed from the panel. {V['ven01']} acts for Corvane in the "
                        f"United Kingdom. {V['ven02_full']}, based in {V['ven02_loc']}, acts in Sweden and Norway.",
                        S["body"]),
              Paragraph("Instructions are allocated through the Assessor Portal. Fees are paid in accordance with the "
                        "panel contract; the Nordic fee schedule is reproduced in Table B.1.", S["body"])]
    nimg, fee_needles = norrvik_table()
    story += [Spacer(1, 8), _flow_img(store.png("tabB_1", nimg), FW / mm),
              Paragraph("Table B.1  Nordic panel fee schedule", S["cap"]), PageBreak()]
    marks["feetable"] = "Table B.1  Nordic panel fee schedule"

    story.append(Paragraph("Appendix C  Glossary", S["h1"]))
    story.append(_table([("Term", "Meaning")] + AT.GLOSSARY, [36, FW / mm - 36], S))
    story.append(PageBreak())

    story.append(Paragraph("Appendix D  Forms", S["h1"]))
    sv = AI.table_image("Site visit record", [
        ("Field", "Entry"), ("Claim number", ""), ("Address", ""), ("Date and time of visit", ""),
        ("Present at visit", ""), ("Type of loss", ""), ("Cause (assessor view)", ""), ("Photographs taken", ""),
        ("Meter readings taken", ""), ("Hazards noted", ""), ("Next steps agreed", ""),
    ], [36, 64])
    story += [_flow_img(store.png("formD_1", sv), FW / mm), Paragraph("Form D.1  Site visit record", S["cap"]),
              PageBreak()]
    cs = AI.table_image("Contents schedule", [
        ("Item", "Description", "Age", "Proof of ownership", "Repair or replace", "Estimate"),
    ] + [(str(i), "", "", "", "", "") for i in range(1, 13)], [8, 34, 10, 18, 16, 14])
    story += [_flow_img(store.png("formD_2", cs), FW / mm), Paragraph("Form D.2  Contents schedule", S["cap"]),
              PageBreak()]

    story.append(Paragraph("Appendix E  List of plates", S["h1"]))
    story.append("__PLATES__")

    # ---- page templates
    total_pages = {"n": 0}

    def cover(canv, doc):
        canv.saveState()
        canv.drawImage(str(cover_img), 0, PAGE_H * 0.36, width=PAGE_W, height=PAGE_H * 0.64,
                       preserveAspectRatio=False)
        canv.setFillColor(TEAL)
        canv.rect(0, 0, PAGE_W, PAGE_H * 0.36, stroke=0, fill=1)
        canv.setFillColor(colors.white)
        canv.setFont("Helvetica-Bold", 28)
        canv.drawString(ML, PAGE_H * 0.26, "Claims Assessor Field Guide")
        canv.drawString(ML, PAGE_H * 0.26 - 34, "and Photo Atlas")
        canv.setFont("Helvetica", 15)
        canv.drawString(ML, PAGE_H * 0.26 - 64, "2025 edition")
        canv.setFont("Helvetica", 10)
        canv.drawString(ML, 40, f"Corvane Mutual Insurance Society Limited  |  {V['t06']}  |  {long_date(when)}")
        canv.restoreState()

    def body(canv, doc):
        canv.saveState()
        canv.setFont("Helvetica", 7.6)
        canv.setFillColor(TEAL)
        canv.drawString(ML, PAGE_H - 13 * mm, "Claims Assessor Field Guide and Photo Atlas")
        canv.drawRightString(PAGE_W - MR, PAGE_H - 13 * mm, "2025 edition")
        canv.setStrokeColor(TEAL)
        canv.setLineWidth(0.5)
        canv.line(ML, PAGE_H - 15 * mm, PAGE_W - MR, PAGE_H - 15 * mm)
        canv.setFillColor(GREY)
        canv.drawString(ML, 11 * mm, "Corvane Mutual – Claims Assessment")
        canv.drawCentredString(PAGE_W / 2, 11 * mm, "Internal")
        canv.drawRightString(PAGE_W - MR, 11 * mm, f"Page {doc.page} of {total_pages['n']}")
        canv.restoreState()

    out = out_path(FID)
    out.parent.mkdir(parents=True, exist_ok=True)

    def render(toc_pages, plate_pages):
        st = []
        for f in story:
            if f == "__TOC__":
                st.append(Paragraph("Contents", S["h1"]))
                for name, pg in toc_pages:
                    st.append(Table([[Paragraph(name, S["toc"]), Paragraph(str(pg), S["toc"])]],
                                    colWidths=[FW - 20 * mm, 20 * mm],
                                    style=[("ALIGN", (1, 0), (1, 0), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 0),
                                           ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
            elif f == "__PLATES__":
                rows = [("Plate", "Title", "Page")] + [(lab, ttl, str(plate_pages.get(lab, "–")))
                                                       for lab, ttl, _ in plate_index]
                st.append(_table(rows, [22, FW / mm - 42, 20], S))
            else:
                st.append(f)
        doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
                              title=an["title"], author=author_n, subject="Claims assessment field guide",
                              creator="Corvane Mutual document production", keywords="Claims Assessor; photo atlas",
                              invariant=1)
        fr = Frame(ML, MB, FW, FH, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="f")
        doc.addPageTemplates([PageTemplate(id="cover", frames=[fr], onPage=cover),
                              PageTemplate(id="body", frames=[fr], onPage=body)])
        import copy
        doc.build(copy.deepcopy(st))
        return doc.page

    toc_names = [(f"Chapter {c['num']}  {c['title']}", "") for c in chaps] + \
        [("Reference collection", ""), ("Appendix A  Measurement and conversion", ""),
         ("Appendix B  Panel arrangements", ""), ("Appendix C  Glossary", ""), ("Appendix D  Forms", ""),
         ("Appendix E  List of plates", "")]
    n1 = render([(a, "000") for a, _ in toc_names], {lab: "000" for lab, _, _ in plate_index})
    texts = _page_texts(out)
    toc = [(a, _find_heading(texts, a)) for a, _ in toc_names]
    ppages = {lab: _find_label(texts, lab) for lab, _, _ in plate_index}
    total_pages["n"] = n1
    n2 = render(toc, ppages)
    assert n2 == n1, (n1, n2)
    size_mb = out.stat().st_size / 1e6
    if not TARGET_MB[0] <= size_mb <= TARGET_MB[1]:
        raise RuntimeError(f"{FID}: {size_mb:.1f} MB outside {TARGET_MB}")
    if not 130 <= n2 <= 150:
        raise RuntimeError(f"{FID}: {n2} pages, expected about 140")
    facts = _facts(out, V, excl, marks, fee_needles)
    return out, facts


REF_COUNT = 76


def _page_texts(path):
    import pymupdf
    with pymupdf.open(str(path)) as d:
        return [p.get_text("text") for p in d]


def _find_heading(texts, name):
    from harness import extract as X
    for i, t in enumerate(texts[3:], 4):
        if X.match(name, t):
            return i
    raise RuntimeError(f"heading not found: {name}")


def _find_label(texts, label):
    import re
    pat = re.compile(rf"(^|\n){re.escape(label)}\s")
    hits = [i for i, t in enumerate(texts, 1) if pat.search(t)]
    hits = [h for h in hits if "List of plates" not in texts[h - 1]]
    if not hits:
        raise RuntimeError(f"plate label not found: {label}")
    return hits[0]


def _facts(out, V, excl, marks, fee_needles):
    from harness import extract as X
    texts = _page_texts(out)
    facts = Facts(FID)
    pls = placements(FID)
    R = V["_rules"]

    def page_of(needle, after=3):
        for i in range(after - 1, len(texts)):
            if X.match(needle, texts[i]):
                return i + 1
        raise RuntimeError(f"needle not found in text layer: {needle!r}")

    def ocr_check(page, needle):
        txt = X.resolve(out, {"kind": "pdf_page", "page": page, "ocr": True})
        if not X.match(needle, txt, "ocr_fuzzy"):
            raise RuntimeError(f"OCR did not find {needle!r} on page {page}: {txt[:400]!r}")

    # --- exclusive raster facts
    lp = _find_label(texts, marks["GRADUAL_LEAK_PLATE"])
    nd = excl["GRADUAL_LEAK_PLATE"][2]
    ocr_check(lp, nd)
    facts.placement(pls["ld21_moisture"], nd, {"kind": "pdf_page", "page": lp, "ocr": True},
                    notes=f"{marks['GRADUAL_LEAK_PLATE']} in chapter 4; the caption is burned into the photograph. The "
                          "text layer of the page carries only the plate title, not the threshold.")
    cp = _find_label(texts, marks["CRACK_REFERRAL_PLATE"])
    nd = excl["CRACK_REFERRAL_PLATE"][2]
    ocr_check(cp, nd)
    facts.placement(pls["ld21_crack"], nd, {"kind": "pdf_page", "page": cp, "ocr": True},
                    notes=f"{marks['CRACK_REFERRAL_PLATE']} in chapter 7; caption burned into the photograph.")
    fp = page_of("Table B.1  Nordic panel fee schedule")
    first = True
    for key, stmt in (("site_se", "Norrvik site visit fee (Sweden): SEK 4,900."),
                      ("desk", "Norrvik desk assessment fee (Sweden): SEK 2,150."),
                      ("site_no", "Norrvik site visit fee (Norway): NOK 5,200.")):
        nd = fee_needles[key]
        ocr_check(fp, nd)
        if first:
            facts.placement(pls["ld21_norrvik"], nd, {"kind": "pdf_page", "page": fp, "ocr": True},
                            statement=pls["ld21_norrvik"]["fact"],
                            notes="Appendix B, Table B.1 is an image; the fees are not in the text layer.")
            first = False
        else:
            facts.add("image_table", stmt, nd, {"kind": "pdf_page", "page": fp, "ocr": True},
                      world_ref=f"VENDOR:VEN-02#fees.{ {'desk': 'desk_assessment_sek', 'site_no': 'site_visit_nok'}[key]}",
                      exclusive=True, placement_key="ld21_norrvik", notes="same image table as PL-061")
    # exclusivity inside the text layer: the exclusive values never appear as text
    for t in texts:
        for bad in ("% WME or more", "wider than 5 mm", "4,900", "2,150", "5,200"):
            assert bad not in t, bad

    # --- non-exclusive image facts (tables and diagrams)
    def img_fact(kind, caption, needle, stmt, ref):
        p = page_of(caption)
        ocr_check(p, needle)
        facts.add(kind, stmt, needle, {"kind": "pdf_page", "page": p, "ocr": True}, world_ref=ref,
                  notes=f"inside the image '{caption}'")

    img_fact("image_table", "Table 9.1  Motor assessment routes", "Repair cost above 65% of market value",
             "Motor total loss when repair cost exceeds 65% of market value (shown in the Table 9.1 image).",
             f"RULE:{R['BR-ASM-017']['ref']}#parameters.pct")
    img_fact("image_table", "Table 11.1  Assessment timescales", "Within 3 business days of the assessor report",
             "Coverage decision letter within 3 business days of the assessor report (Table 11.1 image).",
             f"RULE:{R['BR-ASM-013']['ref']}")
    img_fact("image_text", "Figure 10.1  Nordic home claims", "Claim above NOK 120,000?",
             "Nordic home claims above NOK 120,000 need an on-site takst (decision box in the Figure 10.1 diagram).",
             f"RULE:{R['BR-ASM-009']['ref']}#parameters.amt")
    img_fact("image_table", "Table 4.2  Drying monitoring record", "report moisture readings every 7 days",
             "Drying contractors report moisture readings every 7 days (note under the Table 4.2 image).",
             f"RULE:{R['BR-ASM-019']['ref']}")

    # --- text-layer facts
    def txt(kind, needle, stmt, ref, after=3, notes=None):
        facts.add(kind, stmt, needle, {"kind": "pdf_page", "page": page_of(needle, after)}, world_ref=ref, notes=notes)

    for rid in ("BR-ASM-004", "BR-ASM-002", "BR-ASM-003", "BR-ASM-008", "BR-ASM-017", "BR-ASM-009", "BR-ASM-016",
                "BR-ASM-018", "BR-ASM-005", "BR-ASM-006", "BR-ASM-014", "BR-ASM-010", "BR-ASM-019", "BR-ASM-001"):
        r = R[rid]
        txt("needle", r["text"].rstrip("."), f"{rid} v{r['version']}: {r['text']}", f"RULE:{r['ref']}#text",
            notes="rule box in the chapter text")
    txt("alias_use", f"{V['portal']} ({V['portal_old']} until {V['portal_rename']})",
        f"The Assessor Portal was called the Adjuster Extranet until {V['portal_rename']}.", "SYSTEM:SYS17#renames")
    txt("terminology", "'loss adjuster' means an external Claims Assessor appointed from the panel",
        "In the field guide, 'loss adjuster' means an external (panel) Claims Assessor.", "GLOSSARY:G-001")
    txt("terminology", "the assessor is a 'skadetakstmann' (Norway), 'besiktningsman' (Sweden) or 'taksator'",
        "Nordic terms for the Claims Assessor: skadetakstmann (NO), besiktningsman (SE), taksator (DK).",
        "GLOSSARY:G-001")
    txt("general", f"Document owner {person(anchor(FID)['author'], anchor(FID)['date'])[0]}",
        "The field guide is owned by Imran Talwar, Head of Claims Assessment (UK).", "PERSON:P033", after=1)
    txt("general", f"Approved by {person('P011', anchor(FID)['date'])[0]}",
        "The 2025 field guide was approved by Rob Tennant, Head of Claims Operations (Group).", "PERSON:P011", after=1)
    txt("general", f"based in {V['ven02_loc']}, acts in Sweden and Norway",
        "Norrvik Skadetaxering AB (Gothenburg) is the panel assessor for Sweden and Norway.", "VENDOR:VEN-02#role")
    txt("general", V["ven02_contact"], f"The Norrvik panel contact is {V['ven02_contact']}.", "VENDOR:VEN-02#contact")
    txt("general", f"Repairs are arranged through {V['ven04']}",
        "Motor repairs are arranged through Thistlecombe Repair Network Ltd.", "VENDOR:VEN-04#role")
    return facts
