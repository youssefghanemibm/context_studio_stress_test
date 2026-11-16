"""LD004-LD011: legacy policy wordings, built as DOCX and converted to Word 97 .doc by LibreOffice."""
from __future__ import annotations

import shutil

import docx
from docx.enum.section import WD_ORIENT  # noqa: F401
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

from . import wording_en as EN
from . import wording_extra as XT
from . import wording_no as NO
from . import wording_sv_da as SD
from .common import CACHE, W, Facts, anchor, guard, long_date, out_path, person, placements, util

SPEC = {
    "LD004": {"lang": "en", "kind": "motor", "product": "PRD-MOT-UK", "version": "MOT-UK-2012"},
    "LD005": {"lang": "en", "kind": "home", "product": "PRD-HOM-UK", "version": "HOM-UK-2014"},
    "LD006": {"lang": "en", "kind": "commercial", "product": "PRD-COM-UK", "version": "COM-UK-2011"},
    "LD007": {"lang": "en", "kind": "liability", "product": "PRD-LIA-UK", "version": "LIA-UK-2013"},
    "LD008": {"lang": "sv", "kind": "home", "product": "PRD-HOM-SE", "version": "HOM-SE-2016"},
    "LD009": {"lang": "no", "kind": "motor", "product": "PRD-MOT-NO", "version": "MOT-NO-2015"},
    "LD010": {"lang": "da", "kind": "home", "product": "PRD-HOM-DK", "version": "HOM-DK-2016"},
    "LD011": {"lang": "no", "kind": "home", "product": "PRD-HOM-NO", "version": "HOM-NO-2017"},
}

TEAL = RGBColor(0x0B, 0x4F, 0x6C)

L10N = {
    "en": {"contents": "Contents", "docinfo": "Document information", "wording": "Policy wording",
           "ref": "Wording reference", "product": "Product code", "edition": "Edition date", "prepared": "Prepared by",
           "status": "Status", "status_v": "Issued for new business and renewals", "page": "Page",
           "defs": "Definitions", "excl": "General exclusions", "cond": "General conditions",
           "claims": "Claims conditions", "cancel": "Cancelling your policy", "complaints": "Making a complaint",
           "data": "How we use your information", "law": "Law, language and regulation", "summary": None,
           "issuer": "Corvane Mutual Insurance Society Limited"},
    "no": {"contents": "Innhold", "docinfo": "Dokumentinformasjon", "wording": "Forsikringsvilkår",
           "ref": "Vilkårsreferanse", "product": "Produktkode", "edition": "Gjelder fra", "prepared": "Utarbeidet av",
           "status": "Status", "status_v": "Gjeldende for nytegning og fornyelse", "page": "Side",
           "defs": "Definisjoner", "excl": "Generelle unntak", "safety": "Sikkerhetsforskrifter",
           "excess": "Egenandel", "settle": "Skadeoppgjør", "notify": "Melding om skade (skademelding)",
           "other": "Andre bestemmelser", "summary": "English summary", "intro": "Innledning",
           "issuer": "Corvane Mutual Norge"},
    "sv": {"contents": "Innehåll", "docinfo": "Dokumentinformation", "wording": "Försäkringsvillkor",
           "ref": "Villkorsreferens", "product": "Produktkod", "edition": "Gäller från", "prepared": "Upprättat av",
           "status": "Status", "status_v": "Gäller för nyteckning och förnyelse", "page": "Sida",
           "defs": "Definitioner", "excl": "Allmänna undantag", "safety": "Säkerhetsföreskrifter",
           "excess": "Självrisk", "settle": "Skadevärdering och ersättning", "notify": "Anmälan av skada",
           "other": "Allmänna bestämmelser", "summary": "English summary", "intro": "Inledning",
           "issuer": "Corvane Mutual Sverige"},
    "da": {"contents": "Indhold", "docinfo": "Dokumentoplysninger", "wording": "Forsikringsbetingelser",
           "ref": "Betingelsesreference", "product": "Produktkode", "edition": "Gælder fra", "prepared": "Udarbejdet af",
           "status": "Status", "status_v": "Gælder for nytegning og fornyelse", "page": "Side",
           "defs": "Definitioner", "excl": "Generelle undtagelser", "safety": "Sikkerhedsforskrifter",
           "excess": "Selvrisiko", "settle": "Skadeopgørelse", "notify": "Anmeldelse af skade",
           "other": "Fælles bestemmelser", "summary": "English summary", "intro": "Indledning",
           "issuer": "Corvane Mutual Danmark"},
}

NO_EXCL_TITLE = {"no": "Generelle unntak", "sv": "Allmänna undantag", "da": "Generelle undtagelser"}


def _wording(prod_id, version):
    prod = W.get(f"PRODUCT:{prod_id}")
    for w in prod["wordings"]:
        if w["version"] == version:
            return prod, w
    raise KeyError(version)


# ---------------------------------------------------------------------------------------------
# Block assembly
# ---------------------------------------------------------------------------------------------

def _defs_blocks(defs, lang):
    out = []
    for term, txt in sorted(defs, key=lambda x: x[0].lower()):
        out.append(("def", term, txt))
    return out


def assemble(fid):
    sp = SPEC[fid]
    lang, kind = sp["lang"], sp["kind"]
    prod, wd = _wording(sp["product"], sp["version"])
    L = L10N[lang]
    guard(fid, f"PRODUCT:{sp['product']}", f"wordings.{sp['version']}")
    sections = []   # (h1 title, blocks)
    if lang == "en":
        sections.append(("Introduction", EN.INTRO + EN.IMPORTANT_INFO))
        if kind == "motor":
            defs, secs, schedule, claims = EN.motor(wd["excess"]["standard"], wd["excess"]["windscreen"],
                                                    wd["notification_condition"], wd["acknowledgement_promise"])
            gen_extra = []
        elif kind == "home":
            defs, secs, schedule, claims = EN.home(wd["excess"]["standard"], wd["excess"]["escape_of_water"],
                                                   wd["excess"]["subsidence"], wd["notification_condition"])
            gen_extra = []
        elif kind == "commercial":
            defs, secs, schedule, claims, gen_extra = EN.commercial(wd["excess"]["standard"],
                                                                    wd["bi_indemnity_period_months"],
                                                                    wd["notification_condition"])
        else:
            defs, secs, schedule, claims = EN.liability(wd["limits"]["public_liability"],
                                                        wd["limits"]["employers_liability"],
                                                        wd["excess"]["property_damage"],
                                                        wd["notification_condition"])
            gen_extra = []
        sections.append((L["defs"], [("p", "The following words and phrases have the meanings shown below wherever "
                                           "they appear in this policy.")] + _defs_blocks(EN.GENERAL_DEFS + defs, lang)))
        for title, blocks in secs:
            sections.append((title, blocks))
        if schedule:
            sections.append(("Schedule of excesses" if kind == "motor" else "Schedule", schedule))
        sections.append((L["excl"], [("p", "These exclusions apply to every section of this policy.")] +
                         [x for t, txt in EN.GENERAL_EXCLUSIONS for x in (("h3", t), ("p", txt))]))
        conds = EN.GENERAL_CONDITIONS + gen_extra + EN.EXTRA_CONDITIONS
        sections.append((L["cond"], [("p", "These conditions apply to every section of this policy.")] +
                         [x for t, txt in conds for x in (("h3", t), ("p", txt))]))
        sections.append((L["claims"], claims))
        ext = XT.en_extra(kind)
        sections.append(ext["how_to_claim"])
        sections.append(ext["endorsements"])
        sections.append(ext["fraud"])
        sections.append(ext["care"])
        sections.append((L["cancel"], EN.CANCELLATION))
        sections.append((L["complaints"], EN.COMPLAINTS))
        sections.append((L["data"], EN.DATA))
        sections.append((L["law"], EN.LAW))
    else:
        if lang == "no":
            if kind == "motor":
                defs, secs, egen, sikk, notify = NO.motor(wd["excess"]["standard"], wd["excess"]["windscreen"],
                                                          wd["notification_condition"])
                summary = NO.ENGLISH_SUMMARY_MOTOR
            else:
                defs, secs, egen, sikk, notify = NO.home(wd["excess"]["standard"], wd["notification_condition"])
                summary = NO.ENGLISH_SUMMARY_HOME
            intro, excl, settle, notif_items, slutt = (NO.FELLES_INNLEDNING, NO.FELLES_UNNTAK, NO.SKADEOPPGJOR,
                                                       NO.SKADEMELDING, NO.FELLES_SLUTT)
            notify_par = (f"Sikrede skal {notify}. Skademelding sendes til selskapet på selskapets skademeldingsskjema, "
                          "elektronisk eller per telefon. Sikrede skal i tillegg:")
            excl_intro = "Selskapet svarer ikke for skade eller tap som skyldes eller står i sammenheng med:"
        elif lang == "sv":
            defs, secs = SD.SV_DEF, SD.SV_MOMENT
            egen = [("p", f"Självrisken är {wd['excess']['standard']:,}".replace(",", " ") +
                          " kronor vid varje skadetillfälle om inget annat anges i försäkringsbrevet."),
                    ("p", "Om flera moment berörs av samma skadehändelse dras endast en självrisk, den högsta."),
                    ("p", "Har en säkerhetsföreskrift inte följts kan ersättningen dessutom sättas ned enligt "
                          "reglerna i försäkringsavtalslagen."),
                    ("p", "För naturskador och ansvarsskydd gäller den självrisk som anges i försäkringsbrevet.")]
            sikk, summary = SD.SV_SAKERHET, SD.SV_ENGLISH
            intro, settle, notif_items, slutt = SD.SV_INLEDNING, SD.SV_SKADEVARDERING, SD.SV_ANMALAN, SD.SV_ALLMANT
            excl = ["Krig, krigsliknande händelser, inbördeskrig, revolution eller uppror.",
                    "Atomkärnprocess eller radioaktiv strålning.",
                    "Terrorhandling, i den utsträckning som anges i försäkringsbrevet.",
                    "Skada som den försäkrade orsakat med uppsåt.",
                    "Skada som uppkommit före försäkringstiden.",
                    "Indirekta förluster, om inte annat anges i villkoren."]
            notify_par = (f"Den försäkrade ska {wd['notification_condition']}. Anmälan görs till bolaget per "
                          "telefon, skriftligen eller elektroniskt. Den försäkrade ska dessutom:")
            excl_intro = "Försäkringen gäller inte för skada eller förlust som orsakats av eller står i samband med:"
        else:
            defs, secs = SD.DA_DEF, SD.DA_DAEKNINGER
            amt = f"{wd['excess']['standard']:,}".replace(",", ".")
            egen = [("p", f"Selvrisikoen er {amt} kr. pr. skade, medmindre andet fremgår af policen."),
                    ("p", "Rammer samme skadebegivenhed flere dækninger, betales kun én selvrisiko."),
                    ("p", "Er en sikkerhedsforskrift ikke overholdt, kan erstatningen nedsættes efter reglerne i "
                          "forsikringsaftaleloven."),
                    ("p", "For ansvars- og retshjælpsforsikring gælder den selvrisiko, der fremgår af policen.")]
            sikk, summary = SD.DA_SIKKERHED, SD.DA_ENGLISH
            intro, settle, notif_items, slutt = SD.DA_INDLEDNING, SD.DA_SKADEOPGORELSE, SD.DA_ANMELDELSE, SD.DA_FAELLES
            excl = ["Krig, krigslignende handlinger, borgerkrig, oprør eller uroligheder.",
                    "Atomkernereaktioner eller radioaktiv stråling.",
                    "Terrorhandlinger, medmindre andet følger af lovgivningen.",
                    "Skade, som sikrede har forvoldt med forsæt.",
                    "Skade, der er sket før forsikringens ikrafttræden.",
                    "Driftstab og andre indirekte tab, medmindre andet er nævnt."]
            notify_par = (f"Sikrede skal {wd['notification_condition']}. Anmeldelse til selskabet kan ske skriftligt, "
                          "elektronisk eller pr. telefon. Sikrede skal desuden:")
            excl_intro = "Forsikringen dækker ikke skade eller tab, som skyldes eller står i forbindelse med:"
        ext = XT.nordic_extra(lang, kind)
        sections.append((L["summary"], summary))
        sections.append((L["intro"], intro))
        sections.append(ext["overview"])
        sections.append((L["defs"], _defs_blocks(defs, lang)))
        for title, blocks in secs:
            sections.append((title, blocks))
        sections.append(ext["extra"])
        sections.append((NO_EXCL_TITLE[lang], [("p", excl_intro), ("ul", excl if lang != "no" else NO.FELLES_UNNTAK)]))
        sections.append((L["safety"], [("p", {"no": "Sikrede skal overholde følgende sikkerhetsforskrifter. Overholdes "
                                                    "de ikke, kan selskapets ansvar falle bort eller bli redusert, jf. "
                                                    "forsikringsavtaleloven.",
                                              "sv": "Den försäkrade ska följa nedanstående säkerhetsföreskrifter. Om de "
                                                    "inte följs kan ersättningen sättas ned.",
                                              "da": "Sikrede skal overholde følgende sikkerhedsforskrifter. Overholdes "
                                                    "de ikke, kan erstatningen nedsættes eller bortfalde."}[lang]),
                                       ("ol", sikk)]))
        sections.append((L["excess"], egen))
        sections.append((L["settle"], settle))
        sections.append(ext["table"])
        sections.append((L["notify"], [("p", notify_par), ("ul", notif_items)]))
        sections.append(ext["steps"])
        sections.append(ext["premium"])
        sections.append(ext["duty"])
        sections.append((L["other"], slutt))
        sections.append(ext["words"])
    return prod, wd, sections


# ---------------------------------------------------------------------------------------------
# DOCX rendering
# ---------------------------------------------------------------------------------------------

def _field(paragraph, instr):
    run = paragraph.add_run()
    b = OxmlElement("w:fldChar")
    b.set(qn("w:fldCharType"), "begin")
    t = OxmlElement("w:instrText")
    t.set(qn("xml:space"), "preserve")
    t.text = instr
    s = OxmlElement("w:fldChar")
    s.set(qn("w:fldCharType"), "separate")
    v = OxmlElement("w:t")
    v.text = "1"
    e = OxmlElement("w:fldChar")
    e.set(qn("w:fldCharType"), "end")
    run._r.append(b)
    run._r.append(t)
    run._r.append(s)
    run._r.append(v)
    run._r.append(e)


def _shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def _setup(doc, font_size):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Mm(148), Mm(210)
    sec.left_margin = sec.right_margin = Mm(17)
    sec.top_margin, sec.bottom_margin = Mm(20), Mm(18)
    sec.header_distance, sec.footer_distance = Mm(8), Mm(8)
    st = doc.styles["Normal"]
    st.font.name = "Arial"
    st.font.size = Pt(font_size)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    pf = st.paragraph_format
    pf.space_after = Pt(5)
    pf.line_spacing = 1.18
    for name, size, bold, italic in (("Heading 1", 15, True, False), ("Heading 2", 11.5, True, False),
                                     ("Heading 3", font_size, True, True)):
        h = doc.styles[name]
        h.font.name = "Arial"
        h.font.size = Pt(size)
        h.font.bold = bold
        h.font.italic = italic
        h.font.color.rgb = TEAL
        h.paragraph_format.space_before = Pt(10 if name != "Heading 3" else 6)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
    doc.styles["Heading 1"].paragraph_format.page_break_before = True


def render(fid, prod, wd, sections, font_size=10.5):
    sp = SPEC[fid]
    lang = sp["lang"]
    L = L10N[lang]
    an = anchor(fid)
    when = an["date"]
    author_n, author_t = person(an["author"], when)
    doc = docx.Document()
    _setup(doc, font_size)
    util.set_core_props(doc.core_properties, an["title"], author_n, __import__("datetime").date.fromisoformat(when),
                        subject=f"{L['wording']} {sp['version']}", keywords=f"{sp['version']}; {prod['code']}")
    sec = doc.sections[0]
    hp = sec.header.paragraphs[0]
    hp.text = f"{L['issuer']} – {an['title']} – {sp['version']}"
    hp.runs[0].font.size = Pt(7.5)
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run(f"{sp['version']}  |  {L['page']} ")
    r.font.size = Pt(7.5)
    _field(fp, "PAGE")
    # cover
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(60)
    r = p.add_run(L["issuer"])
    r.font.size, r.font.bold, r.font.color.rgb = Pt(13), True, TEAL
    p = doc.add_paragraph()
    r = p.add_run(an["title"])
    r.font.size, r.font.bold = Pt(22), True
    p = doc.add_paragraph()
    r = p.add_run(f"{L['wording']} – {sp['version']}")
    r.font.size = Pt(13)
    p = doc.add_paragraph()
    r = p.add_run(f"{L['edition']}: {long_date(when) if lang == 'en' else when}")
    r.font.size = Pt(11)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(120)
    r = p.add_run("Corvane Mutual Insurance Society Limited – Corvane House, 14 Tallowgate, London EC3N 9ZZ")
    r.font.size = Pt(8)
    # document information
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)
    doc.add_paragraph(L["docinfo"], style="Heading 2")
    rows = [(L["ref"], sp["version"]), (L["product"], f"{prod['code']} ({prod['name']})"),
            (L["edition"], long_date(when) if lang == "en" else when),
            (L["prepared"], f"{author_n}, {author_t}"), (L["status"], L["status_v"])]
    t = doc.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    for a, b in rows:
        cells = t.add_row().cells
        cells[0].text, cells[1].text = a, b
        _shade(cells[0], "DCEBF2")
    doc.add_paragraph()
    doc.add_paragraph(L["contents"], style="Heading 2")
    for i, (title, _) in enumerate(sections, 1):
        doc.add_paragraph(f"{i}.  {title}")
    # body
    tables = {}
    for i, (title, blocks) in enumerate(sections, 1):
        doc.add_paragraph(f"{i}  {title}", style="Heading 1")
        for b in blocks:
            kind = b[0]
            if kind == "h2":
                doc.add_paragraph(b[1], style="Heading 2")
            elif kind == "h3":
                doc.add_paragraph(b[1], style="Heading 3")
            elif kind == "p":
                doc.add_paragraph(b[1])
            elif kind == "def":
                p = doc.add_paragraph()
                rr = p.add_run(b[1])
                rr.bold = True
                p.add_run(f" – {b[2]}")
            elif kind == "ul":
                for it in b[1]:
                    doc.add_paragraph(it, style="List Bullet")
            elif kind == "ol":
                for it in b[1]:
                    doc.add_paragraph(it, style="List Number")
            elif kind == "table":
                _, ttl, trows, widths = b
                doc.add_paragraph(ttl, style="Heading 3")
                t = doc.add_table(rows=0, cols=len(trows[0]))
                t.style = "Table Grid"
                t.alignment = WD_TABLE_ALIGNMENT.CENTER
                for ri, row in enumerate(trows):
                    cells = t.add_row().cells
                    for ci, val in enumerate(row):
                        cells[ci].text = str(val)
                        if widths:
                            cells[ci].width = Mm(widths[ci])
                        if ri == 0:
                            for run in cells[ci].paragraphs[0].runs:
                                run.bold = True
                            _shade(cells[ci], "DCEBF2")
                tables[ttl] = trows
            elif kind == "pb":
                doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    return doc


# ---------------------------------------------------------------------------------------------

def _convert(fid, doc):
    out = out_path(fid)
    stem = out.stem
    work = CACHE / "wordings"
    work.mkdir(parents=True, exist_ok=True)
    src = work / f"{stem}.docx"
    doc.save(str(src))
    produced = util.soffice_convert(src, "doc", work / "doc", profile_key=f"ld_regulatory_{fid}")
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(produced, out)
    pdf = util.soffice_convert(out, "pdf", work / "pdf", profile_key=f"ld_regulatory_{fid}")
    import pymupdf
    with pymupdf.open(str(pdf)) as d:
        pages = d.page_count
    (CACHE / f"{stem}.pages").write_text(str(pages))
    return out, pages


def _locate(path):
    """Paragraph texts and table cells of the .doc as the verifier sees it (LibreOffice round trip)."""
    from harness import extract as X
    conv = X._as_docx(path)
    d = docx.Document(str(conv))
    paras = [p.text for p in d.paragraphs]
    tabs = []
    for ti, t in enumerate(d.tables):
        for ri, row in enumerate(t.rows):
            for ci, cell in enumerate(row.cells):
                tabs.append((ti, ri, ci, cell.text))
    heads = [(i, p.text, p.style.name) for i, p in enumerate(d.paragraphs) if p.style is not None and
             p.style.name.lower().startswith("heading")]
    return X, paras, tabs, heads


def _para_loc(X, paras, heads, needle, after=None):
    for i, t in enumerate(paras):
        if after is not None and i < after:
            continue
        if X.match(needle, t):
            sec, h1 = None, None
            for hi, ht, hs in heads:
                if hi <= i and ht.strip():
                    sec = ht.strip()
                    if hs.endswith("1"):
                        h1 = ht.strip()
            loc = {"kind": "docx_para", "para_index": i}
            if sec:
                loc["section"] = sec
            return loc, f"{h1} / {sec}"
    raise RuntimeError(f"needle not found in converted document: {needle!r}")


def _table_loc(X, tabs, needle):
    for ti, ri, ci, txt in tabs:
        if X.match(needle, txt):
            return {"kind": "docx_table", "table_index": ti, "row": ri, "col": ci}
    raise RuntimeError(f"needle not found in converted tables: {needle!r}")


def _count(X, paras, tabs, needle):
    return sum(1 for t in paras if X.match(needle, t)) + sum(1 for *_, t in tabs if X.match(needle, t))


def build(fid):
    sp = SPEC[fid]
    prod, wd, sections = assemble(fid)
    font = 10.5
    for attempt in range(6):
        doc = render(fid, prod, wd, sections, font_size=font)
        out, pages = _convert(fid, doc)
        if 25 <= pages <= 45:
            break
        font = font + 0.5 if pages < 25 else font - 0.5
    if not 25 <= pages <= 45:
        raise RuntimeError(f"{fid}: {pages} pages, outside 25-45")
    facts = Facts(fid)
    X, paras, tabs, heads = _locate(out)
    pls = placements(fid)
    lang = sp["lang"]

    def para_fact(kind, statement, needle, world_ref=None, exclusive=False, pl=None, expect_section=None, **kw):
        loc, sec = _para_loc(X, paras, heads, needle)
        if expect_section and (not sec or expect_section.lower() not in sec.lower()):
            raise RuntimeError(f"{fid}: {needle!r} found under {sec!r}, expected {expect_section!r}")
        if pl:
            return facts.placement(pl, needle, loc, statement=statement, **kw)
        return facts.add(kind, statement, needle, loc, world_ref=world_ref, exclusive=exclusive, **kw)

    def table_fact(statement, needle, pl=None, kind="needle", world_ref=None, **kw):
        loc = _table_loc(X, tabs, needle)
        if pl:
            return facts.placement(pl, needle, loc, statement=statement, **kw)
        return facts.add(kind, statement, needle, loc, world_ref=world_ref, **kw)

    ref = f"PRODUCT:{sp['product']}#wordings.{sp['version']}"
    if fid == "LD004":
        para_fact(None, "Motor UK 2012 wording: 'we will acknowledge your claim within 5 working days'.",
                  "we will acknowledge your claim within 5 working days", pl=pls["ld4_ack"],
                  expect_section="Claims conditions", notes="Claims conditions section; contradicted by BR-FNOL-001 v3 (C11)")
        table_fact("Motor UK 2012 wording: compulsory excess £150.", "£150 each claim", pl=pls["ld4_excess"],
                   notes="Schedule of excesses table, row 'Compulsory excess'; the windscreen excess (£75) is in the next row")
        loc = _table_loc(X, tabs, "£75 each replacement")
        facts.add("needle", "Motor UK 2012 wording: windscreen excess £75.", "£75 each replacement", loc, world_ref=ref + ".excess.windscreen",
                  exclusive=True, notes="second half of PL-030 (same table)", placement_key="ld4_excess")
        para_fact("needle", "Motor UK 2012 wording: notify us as soon as possible and in any event within 30 days.",
                  "notify us as soon as possible and in any event within 30 days", world_ref=ref + ".notification_condition")
    elif fid == "LD005":
        para_fact(None, "Home UK 2014 wording: escape of water excess £350; subsidence excess £1,000.",
                  "an escape of water excess of £350", pl=pls["ld5_eow"], expect_section="Section 1 excesses",
                  notes="same paragraph also states the subsidence excess of £1,000 and the standard excess of £200")
        para_fact("needle", "Home UK 2014 wording: subsidence excess £1,000 (Section 1 excesses).",
                  "a subsidence excess of £1,000", world_ref=ref + ".excess.subsidence", exclusive=True,
                  expect_section="Section 1 excesses", placement_key="ld5_eow")
        para_fact("needle", "Home UK 2014 wording: standard buildings excess £200.", "the standard excess of £200",
                  world_ref=ref + ".excess.standard", exclusive=True, expect_section="Section 1 excesses")
        para_fact("needle", "Home UK 2014 wording: tell us within 30 days of discovering the damage.",
                  "tell us within 30 days of discovering the damage", world_ref=ref + ".notification_condition")
    elif fid == "LD006":
        para_fact(None, "Commercial Property 2011 wording: notify the Insurer within 14 days; business interruption "
                        "indemnity period 12 months.", "notify the Insurer within 14 days", pl=pls["ld6_bi"],
                  expect_section="General conditions",
                  notes="General conditions: 'Claims - notification'; the BI indemnity period condition follows")
        para_fact("needle", "Commercial Property 2011 wording: maximum business interruption indemnity period 12 months.",
                  "the maximum indemnity period is 12 months", world_ref=ref + ".bi_indemnity_period_months",
                  expect_section="General conditions", placement_key="ld6_bi")
        table_fact("Commercial Property 2011 wording: Section 1 excess £750 each and every loss.",
                   "£750 each and every loss", world_ref=ref + ".excess.standard")
    elif fid == "LD007":
        table_fact("SME Liability 2013 wording: public liability limit of indemnity £2,000,000.",
                   "£2,000,000 any one occurrence", pl=pls["ld7_pl"], notes="Schedule table, public liability row")
        table_fact("SME Liability 2013 wording: employers' liability limit of indemnity £10,000,000.",
                   "£10,000,000 any one occurrence", world_ref=ref + ".limits.employers_liability", exclusive=True,
                   notes="same Schedule table (part of the exclusive limits field)")
        table_fact("SME Liability 2013 wording: property damage excess £250.", "£250 each claim for damage to property",
                   world_ref=ref + ".excess.property_damage")
        para_fact("needle", "SME Liability 2013 wording: notify the Insurer immediately of any claim or circumstance.",
                  "notify the Insurer immediately of any claim or circumstance", world_ref=ref + ".notification_condition")
    elif fid == "LD008":
        para_fact(None, "Hem Sverige 2016 wording: självrisk SEK 1,500.", "Självrisken är 1 500 kronor",
                  pl=pls["ld8_sjalvrisk"], expect_section="Självrisk",
                  notes="Swedish thousands separator is a space; contradicted by 2026 product terms SEK 2,000 (C17)")
        para_fact("needle", "Hem Sverige 2016 wording: report the claim as soon as possible (anmäla skadan snarast).",
                  "anmäla skadan snarast", world_ref=ref + ".notification_condition")
        para_fact("terminology", "The Swedish wording calls the Claims Assessor 'besiktningsman'.",
                  "Bolaget har rätt att besiktiga skadad egendom och kan utse en besiktningsman",
                  world_ref="GLOSSARY:G-001")
        para_fact("terminology", "The Swedish wording uses 'regress' for subrogation.",
                  "övertar den försäkrades rätt till skadestånd", world_ref="GLOSSARY:G-004")
    elif fid == "LD009":
        para_fact(None, "Motor Norge 2015 wording: egenandel NOK 4,000.",
                  "Ordinær egenandel ved skade på kjøretøyet er NOK 4 000", pl=pls["ld9_egenandel"],
                  expect_section="Egenandel", notes="Norwegian thousands separator is a space")
        para_fact("needle", "Motor Norge 2015 wording: glasskade egenandel NOK 1,500.",
                  "Egenandel ved glasskade er NOK 1 500", world_ref=ref + ".excess.windscreen", exclusive=True,
                  expect_section="Egenandel", placement_key="ld9_egenandel")
        para_fact("needle", "Motor Norge 2015 wording: report the claim without undue delay (uten ugrunnet opphold).",
                  "melde skaden uten ugrunnet opphold", world_ref=ref + ".notification_condition")
        para_fact("terminology", "The Norwegian wording calls the Claims Assessor 'skadetakstmann'.",
                  "Selskapet kan utpeke en skadetakstmann til å besiktige skaden", world_ref="GLOSSARY:G-001")
    elif fid == "LD010":
        para_fact(None, "Hjem Danmark 2016 wording: selvrisiko DKK 1,200.", "Selvrisikoen er 1.200 kr.",
                  pl=pls["ld10_selvrisiko"], expect_section="Selvrisiko",
                  notes="Danish thousands separator is a full stop")
        para_fact("needle", "Hjem Danmark 2016 wording: report the claim as quickly as possible (anmelde skaden hurtigst muligt).",
                  "anmelde skaden hurtigst muligt", world_ref=ref + ".notification_condition")
        para_fact("terminology", "The Danish wording calls the Claims Assessor 'taksator'.",
                  "Selskabet kan udpege en taksator til at besigtige skaden", world_ref="GLOSSARY:G-001")
    elif fid == "LD011":
        para_fact(None, "Hjem Norge 2017 wording: egenandel NOK 4,000.",
                  "Ordinær egenandel for skade på bygning og innbo er NOK 4 000", pl=pls["ld11_frost"],
                  expect_section="Egenandel",
                  notes="PL-037 part 1 (Egenandel section); frost cover is stated in the Dekning section (next fact)")
        para_fact("needle", "Hjem Norge 2017 wording: frost damage (frostskade) to building and contents is covered.",
                  "Forsikringen dekker frostskade på bygning og innbo", world_ref=ref + ".frost_damage_covered",
                  exclusive=True, expect_section="Dekning", placement_key="ld11_frost",
                  notes="PL-037 part 2 (Dekning section)")
        para_fact("needle", "Hjem Norge 2017 wording: report the claim without undue delay.",
                  "melde skaden uten ugrunnet opphold", world_ref=ref + ".notification_condition", exclusive=False,
                  notes="the same statutory phrase is the notification condition of the Motor Norge 2015 wording (LD009)")
        para_fact("terminology", "The Norwegian home wording calls the Claims Assessor 'skadetakstmann'.",
                  "Selskapet kan utpeke en skadetakstmann til å besiktige skaden", world_ref="GLOSSARY:G-001")
    # ---- facts common to every wording (all non-exclusive)
    an = anchor(fid)
    a_name, a_title = person(an["author"], an["date"])
    kind_p = "temporal" if an["author"] == "P005" else "general"
    table_fact(f"The {sp['version']} wording was prepared by {a_name}, {a_title} (as of {an['date']}).",
               f"{a_name}, {a_title}", kind=kind_p, world_ref=f"PERSON:{an['author']}#titles",
               notes="document information table" + ("; P005's maiden name, she became Ingrid Ashby on 2025-08-23"
                                                     if an["author"] == "P005" else ""))
    table_fact(f"The {sp['version']} wording applies to product {prod['code']} ({prod['name']}).",
               f"{prod['code']} ({prod['name']})", kind="general", world_ref=f"PRODUCT:{sp['product']}#code",
               notes="document information table")
    if lang == "en":
        para_fact("terminology", "UK wordings call the first notice of loss a 'notification of loss'.",
                  "Step 2 – Give us notification of loss", world_ref="GLOSSARY:G-005")
        para_fact("terminology", "UK wordings use 'loss adjuster' for an independent (external) Claims Assessor.",
                  "we may appoint a loss adjuster, who is an independent specialist acting on our behalf",
                  world_ref="GLOSSARY:G-001")
    else:
        table_fact("The wording's bilingual word list maps the local assessor term to 'Claims Assessor (loss adjuster)'.",
                   "Claims Assessor (loss adjuster)", kind="terminology", world_ref="GLOSSARY:G-001",
                   notes="word list table at the end of the wording")
        table_fact("The wording's word list translates regress/regres as 'Subrogation / recovery'.",
                   "Subrogation / recovery", kind="terminology", world_ref="GLOSSARY:G-004")
        if lang == "no":
            para_fact("terminology", "Norwegian wordings call the notification of loss 'skademelding'.",
                      "Melding om skade (skademelding)", world_ref="GLOSSARY:G-005")
            para_fact("general", "Corvane Mutual Norge (branch of Corvane Mutual Insurance Society Limited) is at "
                                 "Fjordporten 4, 0150 Oslo.", "Fjordporten 4, 0150 Oslo", world_ref="LOC:LOC-OSL#address")
    # header fact (every wording)
    from harness import extract as X2
    hdr = X2.resolve(out, {"kind": "docx_header", "section_index": 0})
    if sp["version"] not in hdr:
        raise RuntimeError(f"{fid}: header does not carry {sp['version']}: {hdr!r}")
    facts.add("header", f"Every page header of the {sp['version']} wording names the wording reference {sp['version']}.",
              sp["version"], {"kind": "docx_header", "section_index": 0},
              world_ref=f"PRODUCT:{sp['product']}#wordings.{sp['version']}.version")
    # exclusivity inside the file: each exclusive needle appears once only
    for e in facts.items:
        if e["exclusive"] and e["kind"] != "header":
            n = _count(X, paras, tabs, e["needle"])
            if n != 1:
                raise RuntimeError(f"{fid}: exclusive needle {e['needle']!r} appears {n} times")
    return out, facts
