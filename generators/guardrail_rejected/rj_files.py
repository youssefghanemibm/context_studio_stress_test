"""Rejected-format files RJ001-RJ010 (corpus/rejected/).

Each file carries exactly one exclusive episode fact (EP-001..EP-010) that no accepted file states.
Locators use what harness/extract.py supports for these formats: text_lines over the derived plain
text (.vsdx .msg .eml .rtf .odt), xml_xpath (.bpmn .svg), image_ocr (.png .jpg) and zip_member.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import datetime as _dt
import email.policy
import email.utils
import os
import shutil
from email.message import EmailMessage
from xml.sax.saxutils import escape as xesc

from generators.common import util
from generators.guardrail_rejected import ole_msg, whiteboard
from generators.guardrail_rejected.common import (
    COMPANY, COMPANY_SHORT, RJ_DIR, W, Facts, Person, X, adate, anchor, dt_of, find_line, guard, line_loc,
    long_date, normalize_zip, pick, placement, system_name, text_lines_of, write_zip,
)

CACHE = util.BUILD / "cache" / "guardrail_rejected"


def _q(s: str) -> str:
    return xesc(s, {'"': "&quot;"})


# =============================================================================================
# RJ001 – Visio draft of the SIU triage flow (.vsdx, hand-built OPC package)
# =============================================================================================

V_NS = "http://schemas.microsoft.com/office/visio/2012/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XML_HEAD = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'


def _core_xml(title: str, creator: str, when: _dt.datetime, subject: str = "") -> bytes:
    iso = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    return (XML_HEAD +
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<dc:title>{_q(title)}</dc:title><dc:subject>{_q(subject)}</dc:subject>"
            f"<dc:creator>{_q(creator)}</dc:creator><cp:lastModifiedBy>{_q(creator)}</cp:lastModifiedBy>"
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{iso}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{iso}</dcterms:modified>'
            "</cp:coreProperties>").encode("utf-8")


def _vsdx_shape(sid: int, text: str, x: float, y: float, w: float, h: float, kind: str = "rect") -> str:
    if kind == "diamond":
        pts = [(0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5), (0.5, 0)]
    elif kind == "none":
        pts = []
    else:
        pts = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    geom = ""
    if pts:
        rows = "".join(
            f'<Row T="{"RelMoveTo" if i == 0 else "RelLineTo"}" IX="{i + 1}"><Cell N="X" V="{px}"/>'
            f'<Cell N="Y" V="{py}"/></Row>' for i, (px, py) in enumerate(pts))
        geom = ('<Section N="Geometry" IX="0"><Cell N="NoFill" V="0"/><Cell N="NoLine" V="0"/>'
                f'<Cell N="NoShow" V="0"/><Cell N="NoSnap" V="0"/>{rows}</Section>')
    return (f'<Shape ID="{sid}" NameU="{kind.title()}.{sid}" Name="{kind.title()}.{sid}" Type="Shape" '
            'LineStyle="0" FillStyle="0" TextStyle="0">'
            f'<Cell N="PinX" V="{x}"/><Cell N="PinY" V="{y}"/><Cell N="Width" V="{w}"/><Cell N="Height" V="{h}"/>'
            f'<Cell N="LocPinX" V="{w / 2}" F="Width*0.5"/><Cell N="LocPinY" V="{h / 2}" F="Height*0.5"/>'
            '<Cell N="Angle" V="0"/><Cell N="FlipX" V="0"/><Cell N="FlipY" V="0"/>'
            f'<Section N="Character"><Row IX="0"><Cell N="Size" V="0.1111"/></Row></Section>'
            f"{geom}<Text>{_q(text)}</Text></Shape>")


def _vsdx_connector(cid: int, a: tuple, b: tuple, text: str = "") -> str:
    (x1, y1), (x2, y2) = a, b
    t = f"<Text>{_q(text)}</Text>" if text else ""
    return (f'<Shape ID="{cid}" NameU="Dynamic connector.{cid}" Name="Dynamic connector.{cid}" Type="Shape" '
            'LineStyle="0" FillStyle="0" TextStyle="0">'
            f'<Cell N="ObjType" V="2"/><Cell N="BeginX" V="{x1}"/><Cell N="BeginY" V="{y1}"/>'
            f'<Cell N="EndX" V="{x2}"/><Cell N="EndY" V="{y2}"/><Cell N="EndArrow" V="4"/>'
            '<Section N="Geometry" IX="0"><Row T="MoveTo" IX="1"><Cell N="X" V="0"/><Cell N="Y" V="0"/></Row>'
            f'<Row T="LineTo" IX="2"><Cell N="X" V="{round(x2 - x1, 4)}"/><Cell N="Y" V="{round(y2 - y1, 4)}"/>'
            f"</Row></Section>{t}</Shape>")


def build_rj001() -> Facts:
    fid = "RJ001"
    a, d = anchor(fid), adate(fid)
    path = RJ_DIR / a["filename"]
    F = Facts(fid, path)
    pl = placement(fid)
    author = Person(fid, a["author"], d)
    assert author.title.startswith("SIU Investigations Manager")
    sentinel = system_name(fid, "SYS03", d)
    scm = system_name(fid, "SYS22", d)
    fact_text = "Escalate to SIU Investigations Manager – referral untriaged after 2 business days"
    init = author.name.split()[0][0] + ". " + author.name.split()[-1]

    shapes = [
        (1, f"SIU triage flow – DRAFT v0.3 – {init} – {d.strftime('%d/%m/%Y')}", 5.85, 7.75, 6.0, 0.4,
         "none"),
        (2, f"New fraud referral received ({sentinel} alert or claim handler referral)", 1.6, 6.6, 2.4, 0.8, "rect"),
        (3, f"Referral logged in {scm}", 4.3, 6.6, 2.0, 0.8, "rect"),
        (4, "SIU triage: review referral pack and claim file", 7.0, 6.6, 2.2, 0.8, "rect"),
        (5, "Triaged?", 7.0, 4.9, 1.6, 1.1, "diamond"),
        (6, fact_text, 10.0, 4.9, 2.6, 1.0, "rect"),
        (7, "Assign investigator and open SIU case", 7.0, 3.0, 2.2, 0.8, "rect"),
        (8, "No further action – return to claim handler", 4.3, 3.0, 2.2, 0.8, "rect"),
        (9, "DRAFT – not approved. Wording and timings subject to review.", 5.85, 1.2, 5.0, 0.4, "none"),
    ]
    centre = {s[0]: (s[2], s[3]) for s in shapes}
    conns = [
        (20, 2, 3, ""), (21, 3, 4, ""), (22, 4, 5, ""),
        (23, 5, 7, "Yes – investigate"), (24, 5, 8, "Yes – no case"),
        (25, 5, 6, "No – still untriaged"), (26, 6, 4, "returned to triage"),
    ]
    body = "".join(_vsdx_shape(*s) for s in shapes)
    body += "".join(_vsdx_connector(cid, centre[f], centre[t], txt) for cid, f, t, txt in conns)
    connects = "".join(
        f'<Connect FromSheet="{cid}" FromCell="BeginX" FromPart="9" ToSheet="{f}" ToCell="PinX" ToPart="3"/>'
        f'<Connect FromSheet="{cid}" FromCell="EndX" FromPart="12" ToSheet="{t}" ToCell="PinX" ToPart="3"/>'
        for cid, f, t, _ in conns)
    page1 = (XML_HEAD + f'<PageContents xmlns="{V_NS}" xmlns:r="{R_NS}" xml:space="preserve">'
             f"<Shapes>{body}</Shapes><Connects>{connects}</Connects></PageContents>")
    pages = (XML_HEAD + f'<Pages xmlns="{V_NS}" xmlns:r="{R_NS}" xml:space="preserve">'
             '<Page ID="0" NameU="Page-1" Name="SIU triage flow" ViewScale="1" ViewCenterX="5.85" ViewCenterY="4.13">'
             '<PageSheet LineStyle="0" FillStyle="0" TextStyle="0"><Cell N="PageWidth" V="11.69" U="MM"/>'
             '<Cell N="PageHeight" V="8.27" U="MM"/><Cell N="PageScale" V="1" U="MM"/>'
             '<Cell N="DrawingScale" V="1" U="MM"/><Cell N="DrawingSizeType" V="0"/>'
             '<Cell N="DrawingScaleType" V="0"/><Cell N="PrintPageOrientation" V="2"/></PageSheet>'
             '<Rel r:id="rId1"/></Page></Pages>')
    document = (XML_HEAD + f'<VisioDocument xmlns="{V_NS}" xmlns:r="{R_NS}" xml:space="preserve">'
                '<DocumentSettings TopPage="0" DefaultTextStyle="0" DefaultLineStyle="0" DefaultFillStyle="0" '
                'DefaultGuideStyle="0"><GlueSettings>9</GlueSettings><SnapSettings>65847</SnapSettings>'
                '<SnapExtensions>34</SnapExtensions><DynamicGridEnabled>1</DynamicGridEnabled>'
                '<ProtectStyles>0</ProtectStyles><ProtectShapes>0</ProtectShapes><ProtectMasters>0</ProtectMasters>'
                '<ProtectBkgnds>0</ProtectBkgnds></DocumentSettings>'
                '<Colors><ColorEntry IX="24" RGB="#000000"/><ColorEntry IX="25" RGB="#FFFFFF"/>'
                '<ColorEntry IX="26" RGB="#1F4E79"/></Colors>'
                '<FaceNames><FaceName NameU="Calibri" Flags="325"/></FaceNames>'
                '<StyleSheets><StyleSheet ID="0" NameU="No Style" Name="No Style">'
                '<Cell N="EnableLineProps" V="1"/><Cell N="EnableFillProps" V="1"/><Cell N="EnableTextProps" V="1"/>'
                '<Cell N="LineWeight" V="0.01041666666666667"/><Cell N="LineColor" V="0"/>'
                '<Cell N="FillForegnd" V="1"/><Cell N="CharColor" V="0"/></StyleSheet></StyleSheets>'
                '<DocumentSheet NameU="TheDoc" Name="TheDoc" LineStyle="0" FillStyle="0" TextStyle="0">'
                '<Cell N="OutputFormat" V="0"/><Cell N="LockPreview" V="0"/></DocumentSheet></VisioDocument>')
    windows = (XML_HEAD + f'<Windows xmlns="{V_NS}" xmlns:r="{R_NS}" ClientWidth="1600" ClientHeight="900">'
               '<Window ID="0" WindowType="Drawing" WindowState="1073741824" ViewScale="1" ViewCenterX="5.85" '
               'ViewCenterY="4.13" Page="0"/></Windows>')
    ctypes = (XML_HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="xml" ContentType="application/xml"/>'
              '<Override PartName="/visio/document.xml" ContentType="application/vnd.ms-visio.drawing.main+xml"/>'
              '<Override PartName="/visio/pages/pages.xml" ContentType="application/vnd.ms-visio.pages+xml"/>'
              '<Override PartName="/visio/pages/page1.xml" ContentType="application/vnd.ms-visio.page+xml"/>'
              '<Override PartName="/visio/windows.xml" ContentType="application/vnd.ms-visio.windows+xml"/>'
              '<Override PartName="/docProps/core.xml" '
              'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
              '<Override PartName="/docProps/app.xml" '
              'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>')
    rels = (XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/document" '
            'Target="visio/document.xml"/>'
            '<Relationship Id="rId2" '
            'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
            'Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
            'Target="docProps/app.xml"/></Relationships>')
    doc_rels = (XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/pages" '
                'Target="pages/pages.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.microsoft.com/visio/2010/relationships/windows" '
                'Target="windows.xml"/></Relationships>')
    pages_rels = (XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                  '<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/page" '
                  'Target="page1.xml"/></Relationships>')
    app = (XML_HEAD + '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
           'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
           f"<Application>Microsoft Visio</Application><Company>{_q(COMPANY)}</Company>"
           "<Pages>1</Pages></Properties>")
    when = dt_of(d, 16, 20)
    members = [
        ("[Content_Types].xml", ctypes.encode()), ("_rels/.rels", rels.encode()),
        ("docProps/core.xml", _core_xml("SIU triage flow (draft)", author.name, when, "Counter-fraud")),
        ("docProps/app.xml", app.encode()),
        ("visio/document.xml", document.encode()), ("visio/_rels/document.xml.rels", doc_rels.encode()),
        ("visio/windows.xml", windows.encode()),
        ("visio/pages/pages.xml", pages.encode()), ("visio/pages/_rels/pages.xml.rels", pages_rels.encode()),
        ("visio/pages/page1.xml", page1.encode()),
    ]
    write_zip(path, members, when)

    F.add(pl["kind"], "A Visio draft of the SIU triage flow escalates an untriaged referral to the SIU Investigations "
          "Manager after 2 business days.", line_loc(path, "untriaged after 2 business days"),
          "referral untriaged after 2 business days", pl=pl)
    F.add("general", f"The RJ001 Visio draft (v0.3) of the SIU triage flow is by {init}, dated "
          f"{d.strftime('%d/%m/%Y')}.", line_loc(path, "DRAFT v0.3"), f"DRAFT v0.3 – {init}",
          world_ref=f"PERSON:{author.pid}")
    F.add("general", f"In the RJ001 draft, new fraud referrals are logged in {scm}.",
          line_loc(path, f"Referral logged in {scm}"), f"Referral logged in {scm}", world_ref="SYSTEM:SYS22")
    return F


# =============================================================================================
# RJ002 – BPMN 2.0 model of the subrogation process
# =============================================================================================

def build_rj002() -> Facts:
    fid = "RJ002"
    a, d = anchor(fid), adate(fid)
    path = RJ_DIR / a["filename"]
    F = Facts(fid, path)
    pl = placement(fid)
    owner = Person(fid, a["author"], d)
    assert W.owner_of_process("S7", str(d)) == owner.pid
    guard(fid, "S7", "name")
    stage = W.stages["S7"]["name"]
    steps = {}
    for sid in W.stages["S7"]["steps"]:
        guard(fid, sid, "name")
        steps[sid] = W.steps[sid]["name"]
    subtrak = W.systems["SYS24"]
    guard(fid, "SYS24", "name")
    guard(fid, "SYS24", "decommission_target")
    clara = system_name(fid, "SYS01", d)
    guard(fid, "VEN-07", "name")
    solicitor = W.vendors["VEN-07"]["name"]
    team = W.team_name("T08", str(d))
    rehearsal = "2026-12-05"
    ann_text = (f"Planning note ({owner.first[0]}. {owner.name.split()[-1]}): SUBTRAK decommission rehearsal on "
                f"{rehearsal}. {subtrak['name']} retirement target {subtrak['decommission_target']}.")

    # layout: lanes 0 team, 1 head, 2 solicitor
    lane_y = {0: 80, 1: 300, 2: 480}
    lane_h = {0: 220, 1: 180, 2: 160}
    nodes = [  # id, type, name, lane, x
        ("Start_1", "startEvent", "Recovery potential flagged on claim", 0, 150),
        ("Task_Identify", "task", steps["PS-REC-01"], 0, 240),
        ("Gw_Potential", "exclusiveGateway", "Recovery route?", 0, 400),
        ("Task_Salvage", "task", steps["PS-REC-04"], 0, 520),
        ("Task_Open", "task", steps["PS-REC-02"], 0, 680),
        ("Gw_Pursue", "exclusiveGateway", "Pursue?", 0, 840),
        ("Task_Solicitor", "task", steps["PS-REC-03"], 2, 960),
        ("Task_Receipt", "task", steps["PS-REC-05"], 0, 1120),
        ("Task_WriteOff", "task", steps["PS-REC-06"], 1, 1120),
        ("End_Closed", "endEvent", "Recovery case closed", 0, 1320),
        ("End_None", "endEvent", "No recovery", 1, 420),
    ]
    flows = [
        ("Flow_1", "Start_1", "Task_Identify", ""),
        ("Flow_2", "Task_Identify", "Gw_Potential", ""),
        ("Flow_3", "Gw_Potential", "Task_Open", "Third-party recovery"),
        ("Flow_4", "Gw_Potential", "Task_Salvage", "Salvage"),
        ("Flow_5", "Gw_Potential", "End_None", "None"),
        ("Flow_6", "Task_Open", "Gw_Pursue", ""),
        ("Flow_7", "Gw_Pursue", "Task_Solicitor", "Refer to solicitor"),
        ("Flow_8", "Gw_Pursue", "Task_Receipt", "Recover"),
        ("Flow_9", "Gw_Pursue", "Task_WriteOff", "Not pursued"),
        ("Flow_10", "Task_Solicitor", "Task_Receipt", ""),
        ("Flow_11", "Task_Salvage", "Task_Receipt", ""),
        ("Flow_12", "Task_Receipt", "End_Closed", ""),
        ("Flow_13", "Task_WriteOff", "End_Closed", ""),
    ]
    size = {"task": (130, 70), "exclusiveGateway": (50, 50), "startEvent": (36, 36), "endEvent": (36, 36)}
    pos = {}
    for nid, typ, name, lane, x in nodes:
        w, h = size[typ]
        y = lane_y[lane] + lane_h[lane] // 2 - h // 2
        pos[nid] = (x, y, w, h)
    incoming = {n[0]: [f[0] for f in flows if f[2] == n[0]] for n in nodes}
    outgoing = {n[0]: [f[0] for f in flows if f[1] == n[0]] for n in nodes}

    def el(nid, typ, name):
        inner = "".join(f"<bpmn:incoming>{f}</bpmn:incoming>" for f in incoming[nid])
        inner += "".join(f"<bpmn:outgoing>{f}</bpmn:outgoing>" for f in outgoing[nid])
        if nid == "Task_Open":
            inner += ('<bpmn:dataOutputAssociation id="DataOut_Open"><bpmn:targetRef>DataStore_Subtrak'
                      '</bpmn:targetRef></bpmn:dataOutputAssociation>')
        if nid == "Task_Receipt":
            inner += ('<bpmn:dataOutputAssociation id="DataOut_Receipt"><bpmn:targetRef>DataStore_Clara'
                      '</bpmn:targetRef></bpmn:dataOutputAssociation>')
        return f'<bpmn:{typ} id="{nid}" name="{_q(name)}">{inner}</bpmn:{typ}>'

    lanes = [("Lane_Team", team, 0), ("Lane_Head", owner.title, 1), ("Lane_Solicitor", f"{solicitor} (external)", 2)]
    lane_xml = "".join(
        f'<bpmn:lane id="{lid}" name="{_q(name)}">'
        + "".join(f"<bpmn:flowNodeRef>{n[0]}</bpmn:flowNodeRef>" for n in nodes if n[3] == li)
        + "</bpmn:lane>" for lid, name, li in lanes)
    proc = (f'<bpmn:process id="Process_Subrogation" name="{_q(stage)}" isExecutable="false">'
            f'<bpmn:documentation>{_q(stage)} (stage S7). Process owner: {_q(owner.name)}, {_q(owner.title)}. '
            f'Model version 1.2, {d.isoformat()}. Systems: {_q(subtrak["name"])} (SUBTRAK) and {_q(clara)}.'
            '</bpmn:documentation>'
            f'<bpmn:laneSet id="LaneSet_1">{lane_xml}</bpmn:laneSet>'
            + "".join(el(n[0], n[1], n[2]) for n in nodes)
            + "".join(f'<bpmn:sequenceFlow id="{fid_}" name="{_q(lbl)}" sourceRef="{s}" targetRef="{t}"/>'
                      if lbl else f'<bpmn:sequenceFlow id="{fid_}" sourceRef="{s}" targetRef="{t}"/>'
                      for fid_, s, t, lbl in flows)
            + f'<bpmn:dataStoreReference id="DataStore_Subtrak" name="{_q(subtrak["name"])} (SUBTRAK)"/>'
            + f'<bpmn:dataStoreReference id="DataStore_Clara" name="{_q(clara)}"/>'
            + f'<bpmn:textAnnotation id="TextAnnotation_Rehearsal"><bpmn:text>{_q(ann_text)}</bpmn:text>'
              "</bpmn:textAnnotation>"
            + '<bpmn:association id="Association_1" sourceRef="TextAnnotation_Rehearsal" '
              'targetRef="DataStore_Subtrak"/>'
            + "</bpmn:process>")
    # diagram interchange
    di = []
    di.append('<bpmndi:BPMNShape id="Participant_1_di" bpmnElement="Participant_1" isHorizontal="true">'
              '<dc:Bounds x="80" y="80" width="1340" height="560"/></bpmndi:BPMNShape>')
    for lid, _, li in lanes:
        di.append(f'<bpmndi:BPMNShape id="{lid}_di" bpmnElement="{lid}" isHorizontal="true">'
                  f'<dc:Bounds x="110" y="{lane_y[li]}" width="1310" height="{lane_h[li]}"/></bpmndi:BPMNShape>')
    for nid, (x, y, w, h) in pos.items():
        extra = ' isMarkerVisible="true"' if nid.startswith("Gw") else ""
        di.append(f'<bpmndi:BPMNShape id="{nid}_di" bpmnElement="{nid}"{extra}>'
                  f'<dc:Bounds x="{x}" y="{y}" width="{w}" height="{h}"/></bpmndi:BPMNShape>')
    di.append('<bpmndi:BPMNShape id="DataStore_Subtrak_di" bpmnElement="DataStore_Subtrak">'
              '<dc:Bounds x="700" y="16" width="50" height="50"/></bpmndi:BPMNShape>')
    di.append('<bpmndi:BPMNShape id="DataStore_Clara_di" bpmnElement="DataStore_Clara">'
              '<dc:Bounds x="1160" y="16" width="50" height="50"/></bpmndi:BPMNShape>')
    di.append('<bpmndi:BPMNShape id="TextAnnotation_Rehearsal_di" bpmnElement="TextAnnotation_Rehearsal">'
              '<dc:Bounds x="820" y="4" width="300" height="60"/></bpmndi:BPMNShape>')
    for fid_, s, t, _ in flows:
        sx, sy, sw, sh = pos[s]
        tx, ty, tw, th = pos[t]
        di.append(f'<bpmndi:BPMNEdge id="{fid_}_di" bpmnElement="{fid_}">'
                  f'<di:waypoint x="{sx + sw}" y="{sy + sh // 2}"/><di:waypoint x="{tx}" y="{ty + th // 2}"/>'
                  "</bpmndi:BPMNEdge>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
        'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_Subrogation" '
        'targetNamespace="http://corvane-mutual.example/bpmn/recoveries" exporter="Process modeller" '
        'exporterVersion="5.2">\n'
        f'<bpmn:collaboration id="Collaboration_1"><bpmn:participant id="Participant_1" '
        f'name="{_q(COMPANY_SHORT)} – {_q(stage)}" processRef="Process_Subrogation"/></bpmn:collaboration>\n'
        f"{proc}\n"
        '<bpmndi:BPMNDiagram id="BPMNDiagram_1"><bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Collaboration_1">'
        + "".join(di) + "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n</bpmn:definitions>\n")
    path.write_text(xml, encoding="utf-8")

    F.add(pl["kind"], "The BPMN model of the subrogation process names a SUBTRAK decommission rehearsal on 2026-12-05.",
          {"kind": "xml_xpath",
           "xpath": "//*[local-name()='textAnnotation'][@id='TextAnnotation_Rehearsal']/*[local-name()='text']"},
          "SUBTRAK decommission rehearsal on 2026-12-05", pl=pl)
    F.add("general", f"The RJ002 subrogation model (v1.2, {d.isoformat()}) names {owner.name}, {owner.title}, as "
          "process owner.", {"kind": "xml_xpath", "xpath": "//*[local-name()='process']/*[local-name()='documentation']"},
          f"Process owner: {owner.name}", world_ref="PROCESS:S7#owner_history")
    F.add("general", f"In the RJ002 model the write-off step ('{steps['PS-REC-06']}') sits in the {owner.title} lane.",
          {"kind": "xml_xpath", "xpath": "//*[local-name()='lane'][@id='Lane_Head']"}, "Task_WriteOff",
          world_ref="PROCESS:PS-REC-06")
    return F


# =============================================================================================
# RJ003 – Outlook message: write-off approval (.msg, see ole_msg.py)
# =============================================================================================

def build_rj003() -> Facts:
    fid = "RJ003"
    a, d = anchor(fid), adate(fid)
    path = RJ_DIR / a["filename"]
    F = Facts(fid, path)
    pl = placement(fid)
    r = util.rng(f"{fid}:prose")
    freya = Person(fid, a["author"], d)
    sq = Person(fid, "P014", d)
    guard(fid, "LOC-STO", "address")
    guard(fid, "SYS24", "name")
    subtrak = "SUBTRAK"  # the alias staff use for the Subrogation Tracker (SYS24)
    claim = "CLM-UK-2025-118204"
    cest = _dt.timezone(_dt.timedelta(hours=2))
    bst = _dt.timezone(_dt.timedelta(hours=1))
    sent = _dt.datetime(d.year, d.month, d.day, 11, 42, 0, tzinfo=cest)
    req = _dt.datetime(d.year, d.month, d.day - 1, 16, 5, 0, tzinfo=bst)
    subject_req = f"Write-off approval request – {claim}"
    reason = pick(r, [
        "The demand and two follow-ups have gone unanswered and the solicitor's view is that further action would "
        "cost more than it could recover.",
        "We have exhausted the recovery options: the third party has not responded to the demand or the reminders, "
        "and the solicitor advises against proceedings.",
        "After the demand and reminders, the solicitor's advice is that litigation is not proportionate, so I am "
        "recommending we close the recovery.",
    ])
    body = "\n".join([
        f"Hi {sq.first},",
        "",
        pick(r, ["Thanks for pulling the file together. I have read your summary and the solicitor's note, and I "
                 "agree there is nothing further to pursue.",
                 "Thanks for the summary. Having read it with the solicitor's note, I agree we should stop here.",
                 "Thanks – the summary and the solicitor's note are clear, and I agree with your recommendation."]),
        "",
        f"I approve the write-off of £12,480 on claim {claim}.",
        "",
        f"Please record the approval on the recovery case and close it in {subtrak}.",
        "",
        "Kind regards,",
        freya.first,
        "",
        freya.name,
        freya.title,
        COMPANY,
        W.locations["LOC-STO"]["address"],
        "",
        "-----Original Message-----",
        f"From: {sq.name}",
        f"Sent: {long_date(req.date())} 16:05",
        f"To: {freya.name}",
        f"Subject: {subject_req}",
        "",
        f"{freya.first},",
        "",
        f"Requesting your approval to write off the outstanding recovery on {claim}. {reason}",
        "",
        "Amount to write off: £12,480. The case summary is on the recovery file.",
        "",
        "Thanks,",
        sq.first,
        f"{sq.name} | {sq.title} | {W.locations[sq.location]['city']}",
        "",
    ])
    headers = "\n".join([
        f"From: {freya.name} <{freya.email}>",
        f"To: {sq.name} <{sq.email}>",
        f"Subject: RE: {subject_req}",
        f"Date: {email.utils.format_datetime(sent)}",
        f"Message-ID: <{util.stable_hash(fid, 'msgid', n=16)}@corvane-mutual.example>",
        "MIME-Version: 1.0",
        "Content-Type: text/plain; charset=\"utf-8\"",
        "",
    ])
    data = ole_msg.build_msg(subject=f"RE: {subject_req}", body=body, sender_name=freya.name,
                             sender_email=freya.email, to_name=sq.name, to_email=sq.email, sent=sent,
                             headers=headers)
    path.write_bytes(data)

    # The harness reads .msg via olefile when installed, else via a `strings`-style fallback; the line
    # numbers differ, so the range is chosen to contain the needle under both readers.
    needle = f"12,480 on claim {claim}"
    a_lines = X.msg_text(path).splitlines()
    b_lines = X.strings_text(data).splitlines()
    ia, ib = find_line(a_lines, needle), find_line(b_lines, needle)
    F.add(pl["kind"], "Freya Lindahl approved the write-off of £12,480 on claim CLM-UK-2025-118204 on 2026-08-14.",
          {"kind": "text_lines", "start": min(ia, ib), "end": max(ia, ib)}, needle, pl=pl,
          notes="ASCII needle so it also resolves when olefile is absent (strings fallback splits at the pound sign).")
    n2 = f"{sq.name} | {sq.title.split(' – ')[0]}"   # ASCII part of the signature line
    ia2, ib2 = find_line(a_lines, n2), find_line(b_lines, n2)
    F.add("general", f"{sq.name} is {sq.title} (signature of the original request in RJ003).",
          {"kind": "text_lines", "start": min(ia2, ib2), "end": max(ia2, ib2)}, n2,
          world_ref=f"PERSON:{sq.pid}#titles")
    return F


# =============================================================================================
# RJ004 – RFC 5322 email: Norrvik fee notice (.eml)
# =============================================================================================

def build_rj004() -> Facts:
    fid = "RJ004"
    a, d = anchor(fid), adate(fid)
    path = RJ_DIR / a["filename"]
    F = Facts(fid, path)
    pl = placement(fid)
    r = util.rng(f"{fid}:prose")
    sig = Person(fid, a["author"], d)
    guard(fid, "VEN-02", "name")
    ven = W.vendors["VEN-02"]
    assert ven["contact"] == sig.pid
    to = Person(fid, "P034", d)
    cc = Person(fid, "P033", d)
    cet = _dt.timezone(_dt.timedelta(hours=1))
    sent = _dt.datetime(d.year, d.month, d.day, 14, 12, 0, tzinfo=cet)
    # VEN-02 fees are LD021's exclusive fact (PL-061, guarded): the current fee is not restated here.
    assert not W.may_state(fid, "VENDOR:VEN-02", "fees")
    body = "\n".join([
        f"Hej {to.first},",
        "",
        pick(r, ["Following our call earlier this week, I can confirm the change to our fee schedule for "
                 f"{COMPANY_SHORT}.",
                 f"As promised, here is written confirmation of the fee change we discussed for {COMPANY_SHORT}.",
                 f"Further to our conversation this week, this email confirms the fee change for {COMPANY_SHORT}."]),
        "",
        "With effect from 1 January 2027 (2027-01-01), Norrvik's site-visit fee for Swedish claims rises to "
        "SEK 5,150 per visit.",
        "",
        pick(r, ["I will send the updated schedule separately so that you have it on file.",
                 "The updated schedule will follow under separate cover for your records.",
                 "A copy of the revised schedule will follow separately."]),
        "",
        pick(r, ["Please let me know if you need this notice in another format for your procurement records.",
                 "If your procurement colleagues need anything further, just let me know.",
                 "Happy to send a signed copy if that helps your records."]),
        "",
        "Med vänliga hälsningar / Best regards,",
        "",
        sig.name,
        sig.title,
        f"{ven['name']}, {ven['location']}",
        sig.phone,
        "",
    ])
    msg = EmailMessage(policy=email.policy.SMTP)
    msg["From"] = f"{sig.name} <{sig.email}>"
    msg["To"] = f"{to.name} <{to.email}>"
    msg["Cc"] = f"{cc.name} <{cc.email}>"
    msg["Subject"] = "Norrvik fee schedule from 1 January 2027 – Swedish site visits"
    msg["Date"] = email.utils.format_datetime(sent)
    msg["Message-ID"] = f"<{util.stable_hash(fid, 'msgid', n=20)}@norrvik.example>"
    msg["X-Mailer"] = "Norrvik Mail Gateway"
    msg.set_content(body, subtype="plain", charset="utf-8", cte="quoted-printable")
    path.write_bytes(msg.as_bytes(policy=email.policy.SMTP))

    F.add(pl["kind"], "Sigrid Nyhus confirmed that Norrvik's Swedish site-visit fee rises to SEK 5,150 on 2027-01-01.",
          line_loc(path, "rises to SEK 5,150"), "site-visit fee for Swedish claims rises to SEK 5,150", pl=pl,
          notes="Deviation: the placement also quotes the old fee (SEK 4,900); that value is LD021's exclusive "
                "fact (PL-061, VENDOR:VEN-02#fees), so it is not restated here.")
    F.add("general", f"RJ004 is an email from {sig.name}, {sig.title} at {ven['name']}, to {to.name}.",
          line_loc(path, "From:"), sig.email, world_ref=f"PERSON:{sig.pid}")
    return F


# =============================================================================================
# RJ005 – Motor Fleet UK policy wording 2009 (.rtf)
# =============================================================================================

def _rtf_escape(s: str) -> str:
    out = []
    for ch in s:
        if ch in "\\{}":
            out.append("\\" + ch)
        elif ord(ch) > 126:
            out.append(f"\\u{ord(ch) if ord(ch) < 32768 else ord(ch) - 65536}?")
        else:
            out.append(ch)
    return "".join(out)


def build_rj005() -> Facts:
    fid = "RJ005"
    a, d = anchor(fid), adate(fid)
    path = RJ_DIR / a["filename"]
    F = Facts(fid, path)
    pl = placement(fid)
    r = util.rng(f"{fid}:prose")
    author = Person(fid, a["author"], d)

    def para(text, style="body"):
        fmt = {"title": r"\pard\qc\sb120\sa120\b\fs32 ", "subtitle": r"\pard\qc\sa200\fs22 ",
               "h": r"\pard\sb240\sa80\b\fs24 ", "body": r"\pard\sa120\fs20 ",
               "note": r"\pard\sa160\box\brdrs\brdrw10\brsp60\i\fs18 ", "item": r"\pard\li360\fi-200\sa80\fs20 "}[style]
        return "{" + fmt + _rtf_escape(text) + r"\par}" + "\n"

    sections = [
        ("title", f"{COMPANY}"),
        ("subtitle", "Motor Fleet UK – Policy Wording – Edition June 2009"),
        ("note", "ARCHIVE COPY. Motor Fleet UK was closed to new business in 2015; this wording is retained for "
                 "reference on run-off claims only."),
        ("body", f"Prepared for claims use by {author.name}, {author.title}. Effective for policies incepting or "
                 f"renewing on or after {long_date(d)}."),
        ("h", "1. About this policy"),
        ("body", pick(r, [
            "This policy is a contract between you and us. It covers the vehicles listed in the fleet schedule for the "
            "sections shown as operative in the schedule.",
            "This wording, the schedule and any endorsements form one contract. Cover applies to the vehicles named "
            "in the fleet schedule and only for the sections the schedule shows as operative.",
        ])),
        ("h", "2. Definitions"),
        ("item", "• Fleet schedule: the list of insured vehicles we hold for you, as amended from time to time."),
        ("item", "• Insured vehicle: any vehicle shown in the fleet schedule."),
        ("item", "• Excess: the part of each claim that you must pay yourself."),
        ("item", "• You, your: the policyholder named in the schedule. We, us, our: " + COMPANY + "."),
        ("h", "3. Section A – Loss of or damage to insured vehicles"),
        ("body", pick(r, [
            "We will pay for loss of or damage to an insured vehicle, and its accessories while fitted to it, caused by "
            "accident, fire, theft or attempted theft.",
            "We cover accidental loss of or damage to any insured vehicle, including fire, theft and attempted theft, "
            "together with accessories while fitted to the vehicle.",
        ])),
        ("body", "We may repair the vehicle, replace it or pay for the loss in cash."),
        ("h", "4. Section B – Liability to third parties"),
        ("body", pick(r, [
            "We will cover your legal liability for death of or injury to any person, and for damage to property, "
            "arising from the use of an insured vehicle on a road or in a public place.",
            "We will indemnify you against legal liability for injury to any person and for damage to third-party "
            "property arising out of the use of an insured vehicle.",
        ])),
        ("h", "5. The excess"),
        ("body", "Under Section A you must pay an excess of £500 per vehicle for each and every claim. Where one "
                 "incident damages more than one insured vehicle, the excess applies to each vehicle."),
        ("h", "6. General exceptions"),
        ("body", pick(r, [
            "This policy does not cover any vehicle while it is being driven by a person who does not hold a valid "
            "licence to drive it, or who is not permitted to drive it under the schedule.",
            "We will not pay any claim arising while an insured vehicle is driven by anyone not entitled to drive it "
            "under the schedule or not holding a valid licence.",
        ])),
        ("body", "Wear and tear, mechanical or electrical breakdown and loss of use are not covered."),
        ("h", "7. Claims conditions"),
        ("body", pick(r, [
            "Tell us as soon as possible about any incident that may lead to a claim, and send us any letter, claim "
            "form or legal document unanswered.",
            "You must report any incident that could give rise to a claim promptly, and pass to us unanswered every "
            "communication you receive about it.",
        ])),
        ("body", "You must not admit liability or offer to settle any claim without our written agreement."),
        ("h", "8. Cancellation"),
        ("body", "You or we may cancel this policy by giving written notice. Any refund of premium is set out in the "
                 "schedule."),
    ]
    rtf = ("{\\rtf1\\ansi\\ansicpg1252\\deff0\\uc1\n"
           "{\\fonttbl{\\f0\\fswiss\\fcharset0 Arial;}{\\f1\\froman\\fcharset0 Times New Roman;}}\n"
           "{\\colortbl;\\red0\\green0\\blue0;\\red31\\green78\\blue121;}\n"
           "{\\info{\\title Motor Fleet UK Policy Wording June 2009}{\\author " + _rtf_escape(author.name) + "}"
           "{\\company " + _rtf_escape(COMPANY) + "}"
           f"{{\\creatim\\yr{d.year}\\mo{d.month}\\dy{d.day}\\hr9\\min0}}}}\n"
           "\\paperw11906\\paperh16838\\margl1440\\margr1440\\margt1440\\margb1440\n"
           "{\\header\\pard\\qr\\fs16 Motor Fleet UK \\endash  Edition June 2009\\par}\n"
           "{\\footer\\pard\\qc\\fs16 " + _rtf_escape(COMPANY) + " \\endash  Page {\\field{\\*\\fldinst PAGE}"
           "{\\fldrslt 1}}\\par}\n"
           + "".join(para(t, s) for s, t in sections) + "}\n")
    path.write_text(rtf, encoding="ascii")

    F.add(pl["kind"], "The discontinued Motor Fleet UK product (closed to new business in 2015) carried a £500 "
          "per-vehicle excess.", line_loc(path, "excess of £500 per vehicle"), "excess of £500 per vehicle",
          pl=pl, also_in=[])
    F.add(pl["kind"], "The archive note on the RJ005 wording says Motor Fleet UK was closed to new business in 2015.",
          line_loc(path, "closed to new business in 2015"), "closed to new business in 2015",
          world_ref=pl["world_ref"], exclusive=True,
          notes="Second half of the same episode (EP-005) as RJ005-F001. Deviation: the 2015 archive stamp postdates "
                "the 2009 document date; it is presented as a later archive annotation.")
    return F


# =============================================================================================
# RJ006 – Nordic offsite notes (.odt, built as DOCX and converted with LibreOffice)
# =============================================================================================

def build_rj006() -> Facts:
    from docx import Document
    from docx.shared import Pt

    fid = "RJ006"
    a, d = anchor(fid), adate(fid)
    path = RJ_DIR / a["filename"]
    F = Facts(fid, path)
    pl = placement(fid)
    r = util.rng(f"{fid}:prose")
    chair = Person(fid, a["author"], d)
    att = [chair, Person(fid, "P034", d), Person(fid, "P046", d)]
    guard(fid, "CT-FRO", "name")
    frost = W.raw["claim_types"]["claim_types"]
    frost = next(c for c in frost if c["id"] == "CT-FRO")["name"]
    guard(fid, "WAVE:MW-0", "date")
    mw0 = W.waves["MW-0"]
    mw0_date = _dt.date.fromisoformat(str(mw0["date"]))
    assert mw0_date > d  # still upcoming on the meeting date

    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10.5)
    doc.add_heading("Nordic claims offsite – notes", level=0)
    doc.add_paragraph(f"Date: {long_date(d)}    Venue: Gothenburg    Notes: {chair.name}")
    doc.add_paragraph("Attendees: " + "; ".join(f"{p.name} ({p.title})" for p in att)
                      + "; team leads from the Norwegian, Swedish and Danish claims teams.")
    doc.add_heading("1. Winter season review", level=1)
    doc.add_paragraph(pick(r, [
        "Each country walked through what worked and what did not during the last winter season. Common themes were "
        "inconsistent first-visit questions and late requests for photographs.",
        "The group reviewed the winter season country by country. The recurring issues were uneven questioning at "
        "first contact and photographs being requested too late.",
        "A round-table on last winter showed the same two gaps in every country: first-contact questions vary, and "
        "photographs are often asked for late.",
    ]))
    doc.add_heading(f"2. {frost} handling", level=1)
    doc.add_paragraph(pick(r, [
        f"{frost.capitalize()} claims are handled differently in each country today. The group compared the three local "
        "checklists line by line and merged them.",
        f"Today every country uses its own list for {frost.lower()} claims. The lists were compared side by side and "
        "combined into one.",
        f"The three national {frost.lower()} checklists were laid out together and consolidated, as the differences "
        "were mostly wording.",
    ]))
    doc.add_paragraph("Decision: the teams agreed a shared frost-damage checklist, FRO-CHK-3, to be used by the "
                      "Norwegian, Swedish and Danish claims teams.")
    doc.add_heading("3. Assessor coordination", level=1)
    doc.add_paragraph(pick(r, [
        "Assessors asked for the checklist to be available before site visits so that questions are not repeated.",
        "The assessment leads want the checklist shared ahead of visits to avoid asking customers the same questions "
        "twice.",
        "It was agreed that assessors should see the checklist before they visit, so customers are not asked twice.",
    ]))
    doc.add_heading("4. Any other business", level=1)
    doc.add_paragraph(f"{mw0['name']} is due to go live on {long_date(mw0_date)}; the Danish team will share lessons "
                      "learned at the next Nordic call.")
    doc.add_heading("Actions", level=1)
    doc.add_paragraph("Circulate FRO-CHK-3 to all Nordic claims teams and assessors.", style="List Bullet")
    doc.add_paragraph("Collect feedback on the checklist after the first month of use.", style="List Bullet")
    util.set_core_props(doc.core_properties, title="Nordic claims offsite – notes", author=chair.name,
                        when=dt_of(d, 17, 0), subject="Nordic claims offsite", keywords="Nordic; claims; offsite")
    CACHE.mkdir(parents=True, exist_ok=True)
    src = CACHE / (path.stem + ".docx")
    doc.save(str(src))
    normalize_zip(src, dt_of(d, 17, 0), core_dt=dt_of(d, 17, 0))
    outdir = CACHE / "odt_out"
    if outdir.exists():
        shutil.rmtree(outdir)
    produced = util.soffice_convert(src, "odt", outdir, profile_key="guardrail_rejected")
    _pin_odt(produced, dt_of(d, 17, 0))
    os.replace(produced, path)

    F.add(pl["kind"], "The Nordic claims offsite in Gothenburg on 2026-05-20 agreed a shared frost-damage checklist, "
          "FRO-CHK-3.", line_loc(path, "FRO-CHK-3"), "shared frost-damage checklist, FRO-CHK-3", pl=pl)
    F.add("general", f"The RJ006 offsite was held in Gothenburg on {long_date(d)}, notes by {chair.name}.",
          line_loc(path, "Venue: Gothenburg"), f"{long_date(d)}    Venue: Gothenburg".replace("    ", " "),
          world_ref=pl["world_ref"])
    F.add("general", f"{mw0['name']} was due to go live on {long_date(mw0_date)} (as of {long_date(d)}).",
          line_loc(path, "is due to go live"), f"{mw0['name']} is due to go live on {long_date(mw0_date)}",
          world_ref="WAVE:MW-0#date")
    return F


def _pin_odt(path: pathlib.Path, when: _dt.datetime) -> None:
    """Pin LibreOffice's volatile metadata (dates, editing time, generator) for reruns."""
    import re
    import zipfile
    iso = when.strftime("%Y-%m-%dT%H:%M:%S")
    with zipfile.ZipFile(path) as z:
        members = [(i, z.read(i.filename)) for i in z.infolist()]
    out = []
    for info, data in members:
        if info.filename == "meta.xml":
            t = data.decode("utf-8")
            t = re.sub(r"<meta:creation-date>[^<]*</meta:creation-date>", f"<meta:creation-date>{iso}</meta:creation-date>", t)
            t = re.sub(r"<dc:date>[^<]*</dc:date>", f"<dc:date>{iso}</dc:date>", t)
            t = re.sub(r"<meta:editing-duration>[^<]*</meta:editing-duration>", "<meta:editing-duration>PT0S</meta:editing-duration>", t)
            t = re.sub(r"<meta:generator>[^<]*</meta:generator>", "<meta:generator>LibreOffice</meta:generator>", t)
            data = t.encode("utf-8")
        elif info.filename == "settings.xml":
            t = data.decode("utf-8")
            t = re.sub(r'(config:name="(?:RsidRoot|Rsid)" config:type="int">)\d+<', r"\g<1>100000<", t)
            data = t.encode("utf-8")
        out.append((info, data))
    tmp = path.with_name(path.name + ".tmp")
    stamp = (when.year, when.month, when.day, when.hour, when.minute, when.second)
    with zipfile.ZipFile(tmp, "w") as z:
        for info, data in out:
            zi = zipfile.ZipInfo(info.filename, date_time=stamp)
            zi.compress_type = info.compress_type
            zi.external_attr = 0o644 << 16
            zi.create_system = 3
            z.writestr(zi, data)
    os.replace(tmp, path)


# =============================================================================================
# RJ007 / RJ008 – whiteboard photos (.png / .jpg), verified by OCR
# =============================================================================================

def build_rj007() -> Facts:
    fid = "RJ007"
    a, d = anchor(fid), adate(fid)
    path = RJ_DIR / a["filename"]
    F = Facts(fid, path)
    pl = placement(fid)
    author = Person(fid, a["author"], d)
    clara = system_name(fid, "SYS01", d)
    guard(fid, "SYS01", "batch_window")
    now_window = W.systems["SYS01"]["batch_window"].split(" ")[0].replace("–", "-")
    guard(fid, "WAVE:MW-2", "date")
    mw2 = _dt.date.fromisoformat(str(W.waves["MW-2"]["date"]))
    lines = [
        dict(text=f"{clara} batch window", x=110, y=90, size=74, colour="black", underline=True),
        dict(text=f"now: {now_window}", x=140, y=260, size=64, colour="blue"),
        dict(text="post-Wave 2 target: 23:30-03:30", x=140, y=420, size=64, colour="red", box=True),
        dict(text=f"Wave 2 = {mw2.day} {mw2.strftime('%b')} {mw2.year}", x=140, y=600, size=58, colour="blue"),
        dict(text=f"{author.initials} {d.strftime('%d/%m')}", x=1150, y=800, size=52, colour="black"),
    ]
    img = whiteboard.render(lines, (1600, 1000), f"{fid}:board")
    img.save(path, format="PNG", optimize=True)
    F.add(pl["kind"], "A whiteboard photo sets the post-Wave-2 CLARA batch window target at 23:30–03:30.",
          {"kind": "image_ocr"}, "post-Wave 2 target: 23:30-03:30", pl=pl)
    F.add("image_text", f"The RJ007 whiteboard gives today's {clara} batch window as {now_window}.",
          {"kind": "image_ocr"}, f"now: {now_window}", world_ref="SYSTEM:SYS01#batch_window")
    return F


def build_rj008() -> Facts:
    fid = "RJ008"
    a, d = anchor(fid), adate(fid)
    path = RJ_DIR / a["filename"]
    F = Facts(fid, path)
    pl = placement(fid)
    author = Person(fid, a["author"], d)
    guard(fid, "COM-01", "name")
    com = W.committees["COM-01"]["name"]
    lines = [
        dict(text="Reserving - Q3 close", x=110, y=90, size=72, colour="black", underline=True),
        dict(text="IBNR Sept 2026 = £648.2m", x=140, y=280, size=70, colour="green", box=True),
        dict(text=f"{com} pack: draft Fri", x=140, y=470, size=56, colour="blue"),
        dict(text=f"{author.initials} {d.strftime('%d/%m')}", x=1150, y=800, size=52, colour="black"),
    ]
    img = whiteboard.render(lines, (1600, 1000), f"{fid}:board")
    img.save(path, format="JPEG", quality=86, optimize=True)
    F.add(pl["kind"], "A photo of the Reserving team whiteboard shows IBNR for September 2026 as £648.2m.",
          {"kind": "image_ocr"}, "IBNR Sept 2026 = £648.2m", pl=pl)
    F.add("image_text", f"The RJ008 whiteboard notes the {com} pack is due in draft on Friday.",
          {"kind": "image_ocr"}, f"{com} pack", world_ref="COMMITTEE:COM-01")
    return F


# =============================================================================================
# RJ009 – SVG diagram of the CIS login flow
# =============================================================================================

def build_rj009() -> Facts:
    fid = "RJ009"
    a, d = anchor(fid), adate(fid)
    path = RJ_DIR / a["filename"]
    F = Facts(fid, path)
    pl = placement(fid)
    author = Person(fid, a["author"], d)
    cis = system_name(fid, "SYS16", d)
    hub = system_name(fid, "SYS02", d)
    init = f"{author.name.split()[0][0]}. {author.name.split()[-1]}"
    cols = [("User (browser)", 120), (f"{hub} web UI", 400), (f"{cis} (CIS)", 700), (f"{hub} API", 1000)]
    steps = [
        (0, 1, "1. Open Claims Hub"),
        (1, 2, "2. Redirect to CIS sign-in (OIDC authorisation request)"),
        (0, 2, "3. Sign in with Corvane credentials"),
        (2, 1, "4. Authorisation code (redirect back)"),
        (1, 2, "5. Exchange code for tokens"),
        (2, 1, "6. ID token + access token"),
        (1, 3, "7. API call with bearer access token"),
        (3, 1, "8. Response"),
    ]
    el = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="820" viewBox="0 0 1180 820" '
        'font-family="Arial, Helvetica, sans-serif">',
        f"<title>CIS login flow – {_q(hub)} (draft)</title>",
        f"<desc>Sequence of the sign-in flow between the browser, the {_q(hub)} web UI, {_q(cis)} and the "
        f"{_q(hub)} API. Draft by {_q(author.name)}, {_q(author.title)}, {d.isoformat()}.</desc>",
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="8" markerHeight="8" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1f2933"/></marker></defs>',
        '<rect x="0" y="0" width="1180" height="820" fill="#ffffff"/>',
        f'<text id="title" x="40" y="44" font-size="22" font-weight="bold" fill="#1f2933">CIS login flow – '
        f'{_q(hub)}</text>',
    ]
    for i, (name, x) in enumerate(cols):
        el.append(f'<g id="actor-{i}"><rect x="{x - 110}" y="80" width="220" height="54" rx="6" fill="#e7ecf3" '
                  f'stroke="#2f4f75" stroke-width="1.5"/><text x="{x}" y="113" font-size="15" text-anchor="middle" '
                  f'fill="#1f2933">{_q(name)}</text>'
                  f'<line x1="{x}" y1="134" x2="{x}" y2="700" stroke="#9aa5b1" stroke-dasharray="6 5"/></g>')
    y = 180
    for k, (s, t, label) in enumerate(steps):
        x1, x2 = cols[s][1], cols[t][1]
        el.append(f'<g id="step-{k + 1}"><line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#1f2933" '
                  f'stroke-width="1.6" marker-end="url(#arrow)"/>'
                  f'<text x="{(x1 + x2) / 2}" y="{y - 8}" font-size="13" text-anchor="middle" fill="#1f2933">'
                  f"{_q(label)}</text></g>")
        y += 62
    el.append('<g id="note-token"><rect x="760" y="560" width="380" height="58" rx="4" fill="#fff6d6" '
              'stroke="#b08900"/><text id="lbl-token-lifetime" x="950" y="595" font-size="16" text-anchor="middle" '
              'fill="#1f2933">Access token lifetime: 15 minutes</text></g>')
    el.append(f'<text id="footer" x="40" y="780" font-size="12" fill="#52606d">Draft – {_q(init)}, '
              f'{_q(author.title)} – {long_date(d)}</text>')
    el.append("</svg>")
    path.write_text("\n".join(el) + "\n", encoding="utf-8")

    F.add(pl["kind"], "The SVG diagram of the CIS login flow labels the access-token lifetime as 15 minutes.",
          {"kind": "xml_xpath", "xpath": "//*[local-name()='text'][@id='lbl-token-lifetime']"},
          "Access token lifetime: 15 minutes", pl=pl)
    F.add("general", f"In the RJ009 diagram the {hub} web UI redirects users to CIS for an OIDC authorisation request.",
          {"kind": "xml_xpath", "xpath": "//*[local-name()='g'][@id='step-2']"},
          "Redirect to CIS sign-in (OIDC authorisation request)", world_ref="SYSTEM:SYS16#description")
    F.add("general", f"The RJ009 CIS login flow is a draft by {init}, {author.title}, dated {long_date(d)}.",
          {"kind": "xml_xpath", "xpath": "//*[local-name()='text'][@id='footer']"}, f"{init}, {author.title}",
          world_ref=f"PERSON:{author.pid}#titles")
    return F


# =============================================================================================
# RJ010 – ZIP archive with a 2019 DB2 capacity report
# =============================================================================================

def build_rj010() -> Facts:
    fid = "RJ010"
    a, d = anchor(fid), adate(fid)
    path = RJ_DIR / a["filename"]
    F = Facts(fid, path)
    pl = placement(fid)
    dba = Person(fid, a["author"], d)
    clara = system_name(fid, "SYS01", d)
    guard(fid, "SYS01", "db2_subsystem")
    db2 = W.systems["SYS01"]["db2_subsystem"]
    guard(fid, "TABLE:CLR.T_RESERVE_MOVEMENT", "name")
    tbl = "CLR.T_RESERVE_MOVEMENT"
    rows = 412_906_118
    base = "legacy_archive_2019/"
    report_name = f"{base}capacity/{db2}_capacity_report_20191231.txt"
    csv_name = f"{base}capacity/reserve_movement_rowcount_20191231.csv"
    readme = "\n".join([
        "LEGACY ARCHIVE 2019 - CLARA DB2 capacity material",
        "",
        f"Archived : {d.strftime('%d/%m/%Y')}",
        f"Owner    : {dba.name}, {dba.title} ({W.locations[dba.location]['city']})",
        "",
        "Contents",
        f"  {report_name[len(base):]:<52} year-end row count, reserve movement audit table",
        f"  {csv_name[len(base):]:<52} the same figure, machine-readable",
        "",
        "Retention: keep with the CLARA technical archive.",
        "",
    ])
    report = "\n".join([
        f"{COMPANY.upper()}",
        f"{clara} DB2 CAPACITY REPORT - YEAR END",
        "=" * 60,
        f"Subsystem   : {db2}",
        f"As at       : {d.isoformat()}",
        f"Prepared by : {dba.name}, {dba.title}",
        "Source      : catalogue statistics collected after the year-end statistics run",
        "",
        f"{'TABLE':<26}{'DESCRIPTION':<34}{'ROWS':>14}",
        f"{'-' * 24:<26}{'-' * 32:<34}{'-' * 14:>14}",
        f"{tbl:<26}{'Audit trail of reserve changes':<34}{rows:>14,}",
        "",
        "Scope: this extract covers the reserve movement audit table only.",
        f"Row count on {d.isoformat()}: {tbl} {rows:,} rows.",
        "",
        "-- end of report --",
        "",
    ])
    csv_text = f"as_at,subsystem,table_name,row_count\n{d.isoformat()},{db2},{tbl},{rows}\n"
    write_zip(path, [(f"{base}README.txt", readme.encode()), (report_name, report.encode()),
                     (csv_name, csv_text.encode())], dt_of(d, 18, 30))

    lines = report.splitlines()
    i = find_line(lines, f"{tbl} {rows:,} rows")
    F.add(pl["kind"], "A 2019 DB2 capacity report in the archive gives CLR.T_RESERVE_MOVEMENT 412,906,118 rows on "
          "2019-12-31.", {"kind": "zip_member", "member": report_name,
                          "inner": {"kind": "text_lines", "start": i, "end": i}},
          f"{tbl} {rows:,} rows", pl=pl)
    F.add(pl["kind"], f"The RJ010 archive's CSV gives {tbl} {rows} rows as at {d.isoformat()} ({db2}).",
          {"kind": "zip_member", "member": csv_name, "inner": {"kind": "csv_row", "row": 1}},
          f"{tbl} | row_count: {rows}", world_ref=pl["world_ref"], exclusive=True,
          notes="Same episode (EP-010) as RJ010-F001, machine-readable copy inside the same archive.")
    F.add("general", f"The RJ010 archive was assembled by {dba.name}, {dba.title}.",
          {"kind": "zip_member", "member": f"{base}README.txt", "inner": {"kind": "text_lines", "start": 4, "end": 4}},
          f"{dba.name}, {dba.title}", world_ref=f"PERSON:{dba.pid}#titles")
    return F


BUILDERS = {
    "RJ001": build_rj001, "RJ002": build_rj002, "RJ003": build_rj003, "RJ004": build_rj004, "RJ005": build_rj005,
    "RJ006": build_rj006, "RJ007": build_rj007, "RJ008": build_rj008, "RJ009": build_rj009, "RJ010": build_rj010,
}
