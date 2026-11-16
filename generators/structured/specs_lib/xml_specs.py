"""XML files ST035-ST042."""
from __future__ import annotations

import pathlib
import re

from lxml import etree

from generators.common import util

from .core import (W, Built, Facts, DOC_PREFIX, add_business_days, fauthor, fdate, fstatus, ftitle, may, need,
                   pname, ptitle, pemail, rule_params_ok, rule_text_ok, rule_ver, svcname, sysname, team_name,
                   version_history, team_exists, jcl_jobs_as_of, interface_exists)
from . import phrases
from . import fr1_data
from .json_specs import fr1_annex_records, fr1_definitions, fr1_detail


class XB:
    """Tiny namespaced XML builder."""

    def __init__(self, ns: str, root: str, **attrs):
        self.ns = ns
        self.root = etree.Element(self.q(root), nsmap={None: ns, "xsi": "http://www.w3.org/2001/XMLSchema-instance"})
        for k, v in attrs.items():
            self.root.set(k, str(v))

    def q(self, tag: str) -> str:
        return f"{{{self.ns}}}{tag}"

    def sub(self, parent, tag: str, text=None, **attrs):
        el = etree.SubElement(parent, self.q(tag))
        for k, v in attrs.items():
            if v is None:
                continue
            el.set(k.rstrip("_"), str(v).lower() if isinstance(v, bool) else str(v))
        if text is not None:
            el.text = str(text)
        return el

    def comment(self, parent, text: str):
        parent.append(etree.Comment(f" {text} "))

    def bytes(self, header_comment: str | None = None) -> bytes:
        body = etree.tostring(self.root, pretty_print=True, encoding="unicode")
        head = '<?xml version="1.0" encoding="UTF-8"?>\n'
        if header_comment:
            head += f"<!-- {header_comment} -->\n"
        return (head + body).encode("utf-8")


def xloc(xpath: str) -> dict:
    return {"kind": "xml_xpath", "xpath": xpath}


def doc_control(xb: XB, parent, fid: str, approvers: list[str], reviewers: list[str] | None = None,
                history_authors=None, final_label=None):
    on = fdate(fid)
    a = fauthor(fid)
    hist = version_history(fid, history_authors or [a], final_label=final_label)
    dc = xb.sub(parent, "documentControl")
    xb.sub(dc, "documentId", DOC_PREFIX[fid])
    xb.sub(dc, "title", ftitle(fid))
    xb.sub(dc, "version", hist[-1]["version"])
    xb.sub(dc, "status", fstatus(fid))
    xb.sub(dc, "date", on)
    xb.sub(dc, "classification", "Internal")
    o = xb.sub(dc, "owner", personId=a)
    xb.sub(o, "name", pname(a, on))
    xb.sub(o, "title", ptitle(a, on))
    if reviewers:
        rv = xb.sub(dc, "reviewers")
        for p in reviewers:
            xb.sub(rv, "reviewer", pname(p, on), personId=p, title=ptitle(p, on))
    ap = xb.sub(dc, "approvers")
    for p in approvers:
        xb.sub(ap, "approver", pname(p, on), personId=p, title=ptitle(p, on), date=on)
    ch = xb.sub(dc, "changeHistory")
    for h in hist:
        xb.sub(ch, "revision", h["change"], version=h["version"], date=h["date"], author=h["author"])
    return dc


# ---------------------------------------------------------------------------------------------
# ST035 Interface catalogue
# ---------------------------------------------------------------------------------------------

TICKET_IFACE_RX = re.compile(r"CLX-IF-\d{3}")


def system_owner(sid: str, on: str) -> str:
    s = W.systems[sid]
    own = s["owner"]
    for h in s.get("owner_history", []):
        if h["from"] <= on and (h["to"] is None or on <= h["to"]):
            own = h["person"]
    return own


def upstream_hops(iid: str) -> dict[str, list[str]]:
    """Transitive upstream interfaces by hop distance (derived from depends_on)."""
    out: dict[str, list[str]] = {}
    seen = {iid}
    frontier = [iid]
    lvl = 0
    while frontier:
        lvl += 1
        nxt = []
        for x in frontier:
            for d in W.interfaces[x]["depends_on"]:
                if d not in seen:
                    seen.add(d)
                    nxt.append(d)
        if nxt:
            out[str(lvl)] = sorted(nxt)
        frontier = nxt
    return out


def program_detail(xb: XB, pe, fid: str, p: str, on: str) -> None:
    """Description, tables and copybooks of a CLARA program (world data, exclusivity-checked)."""
    pr = W.programs[p]
    ref = f"PROGRAM:{p}"
    if may(fid, ref, "description"):
        xb.sub(pe, "description", pr["description"])
    rd = [t for t in pr["reads_tables"] if may(fid, ref, f"reads_tables:{t}") and str(W.tables[t].get("created") or "") <= on]
    wr = [t for t in pr["writes_tables"] if may(fid, ref, f"writes_tables:{t}") and str(W.tables[t].get("created") or "") <= on]
    if rd and may(fid, ref, "reads_tables"):
        xb.sub(pe, "reads", " ".join(rd))
    if wr and may(fid, ref, "writes_tables"):
        xb.sub(pe, "writes", " ".join(wr))
    if pr["copybooks"] and may(fid, ref, "copybooks"):
        xb.sub(pe, "copybooks", " ".join(pr["copybooks"]))
    if pr.get("owner_team") and team_exists(pr["owner_team"], on):
        xb.sub(pe, "ownerTeam", team_name(pr["owner_team"], on), id=pr["owner_team"])
    if pr.get("replaced_by") and may(fid, ref, "replaced_by"):
        xb.sub(pe, "replacedBy", svcname(pr["replaced_by"], on))


def service_detail(xb: XB, se, fid: str, s: str, on: str) -> None:
    sv = W.services[s]
    ref = f"SERVICE:{s}"
    if may(fid, ref, "description"):
        xb.sub(se, "description", sv["description"])
    own = W.service_owner(s, on)
    if own and team_exists(own["team"], on):
        xb.sub(se, "ownerTeam", team_name(own["team"], on), id=own["team"])
    kt = sv.get("kafka_topics") or {}
    if may(fid, ref, "kafka_topics"):
        if kt.get("produces"):
            xb.sub(se, "produces", " ".join(kt["produces"]))
        if kt.get("consumes"):
            xb.sub(se, "consumes", " ".join(kt["consumes"]))


def build_ST035(out_dir: pathlib.Path) -> Built:
    fid = "ST035"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:catalogue")
    xb = XB("urn:corvane:skerry:interface-catalogue:2", "interfaceCatalogue", schemaVersion="2.3", asOf=on)
    doc_control(xb, xb.root, fid, approvers=["P018", "P032"], reviewers=["P050", "P049", "P016"])
    intro = xb.sub(xb.root, "introduction")
    xb.sub(intro, "para", "This catalogue lists every Corvane claims interface between CLARA, Claims Hub and the "
                          "surrounding systems, with ownership, criticality and dependencies. It is the reference "
                          "for interface change impact assessments (CHUB-144).")
    xb.sub(intro, "para", phrases.paragraph(r, "governance", 3))
    # systems
    sysl = xb.sub(xb.root, "systems")
    for sid, s in W.systems.items():
        se = xb.sub(sysl, "system", id=sid, lifecycle=s["lifecycle"])
        xb.sub(se, "name", sysname(sid, on))
        for rn in s.get("renames", []):
            if rn["date"] <= on:
                xb.sub(se, "formerName", rn["from_name"], renamedOn=rn["date"])
        xb.sub(se, "type", s["type"])
        own = s["owner"]
        for h in s.get("owner_history", []):
            if h["from"] <= on and (h["to"] is None or on <= h["to"]):
                own = h["person"]
        xb.sub(se, "owner", pname(own, on), personId=own)
        if s.get("decommission_target"):
            xb.sub(se, "decommissionTarget", s["decommission_target"])
    # interfaces
    ifl = xb.sub(xb.root, "interfaces", count=len(W.interfaces))
    tickets_by_if: dict[str, list] = {}
    for t in W.tickets.values():
        for m in TICKET_IFACE_RX.findall(t["summary"]):
            if str(t["created"]) <= on:
                tickets_by_if.setdefault(m, []).append(t)
    imp_cache = {}
    for iid, i in W.interfaces.items():
        ref = f"INTERFACE:{iid}"
        status = i["status"]
        el = xb.sub(ifl, "interface", id=iid, status=status, criticality=i["criticality"], since=i["since"])
        xb.sub(el, "name", i["name"])
        xb.sub(el, "summary", f"{i['name']}: {sysname(i['source_system'], on)} to {sysname(i['target_system'], on)} "
                              f"({i['protocol']}). " + phrases.paragraph(r, "interface_ops", 3, iid))
        xb.sub(el, "operationalNotes", phrases.paragraph(r, "error_handling", 3))
        xb.sub(el, "source", sysname(i["source_system"], on), systemId=i["source_system"])
        xb.sub(el, "target", sysname(i["target_system"], on), systemId=i["target_system"])
        tr = xb.sub(el, "transport", protocol=i["protocol"])
        xb.sub(tr, "format", i["format"])
        if i.get("mq_queue") and may(fid, ref, "mq_queue"):
            xb.sub(tr, "mqQueue", i["mq_queue"], queueManager="CLRQM01")
        if i.get("kafka_topic"):
            xb.sub(tr, "kafkaTopic", i["kafka_topic"], cluster="esp-prd")
        if i.get("copybook") and may(fid, ref, "copybook"):
            xb.sub(tr, "copybook", i["copybook"])
        if i.get("dataset") and may(fid, ref, "dataset"):
            xb.sub(tr, "dataset", i["dataset"])
        if i.get("jcl_job") and may(fid, ref, "jcl_job"):
            xb.sub(tr, "batchJob", i["jcl_job"], scheduler="SYS18")
        if may(fid, ref, "schedule"):
            xb.sub(el, "schedule", W.interface_schedule(iid, on))
            if i.get("schedule_history"):
                sh = xb.sub(el, "scheduleHistory")
                for h in i["schedule_history"]:
                    xb.sub(sh, "entry", h["value"], from_=h["from"], to=h.get("to"), ticket=h.get("ticket"))
        xb.sub(el, "volume", i["avg_daily_volume"])
        ow = xb.sub(el, "owner", personId=i["owner"], teamId=W.team_of(i["owner"], on))
        xb.sub(ow, "name", pname(i["owner"], on))
        xb.sub(ow, "title", ptitle(i["owner"], on))
        xb.sub(ow, "email", pemail(i["owner"], on))
        impl = xb.sub(el, "implementation")
        if i["programs"]:
            pp = xb.sub(impl, "programs")
            for p in i["programs"]:
                pr = W.programs[p]
                pe = xb.sub(pp, "program", id=p, type=pr["type"], jclJob=pr["jcl_job"], cicsTransaction=pr["cics_transaction"])
                program_detail(xb, pe, fid, p, on)
        if i["services"]:
            ss = xb.sub(impl, "services")
            for s in i["services"]:
                sv_ = W.services[s]
                st_ = sv_["status"] if str(sv_.get("go_live") or "") <= on else "in development"
                se_ = xb.sub(ss, "service", namespace=sv_["k8s_namespace"], status=st_)
                xb.sub(se_, "name", svcname(s, on))
                service_detail(xb, se_, fid, s, on)
        if i["tables"]:
            tt = xb.sub(impl, "tables")
            for t in i["tables"]:
                xb.sub(tt, "table", name=t, db=W.tables[t]["db"])
        dep = xb.sub(el, "dependsOn")
        for d in i["depends_on"]:
            xb.sub(dep, "interfaceRef", ref=d, name=W.interfaces[d]["name"])
        dnt = xb.sub(el, "dependents")
        for d in i["dependents"]:
            xb.sub(dnt, "interfaceRef", ref=d, name=W.interfaces[d]["name"])
        if i["consumer_teams"]:
            ct = xb.sub(el, "consumerTeams")
            for t in i["consumer_teams"]:
                xb.sub(ct, "team", team_name(t, on), id=t)
        if i["feeds_reports"]:
            fr = xb.sub(el, "feedsReports")
            for rp in i["feeds_reports"]:
                xb.sub(fr, "report", W.reports[rp]["name"], code=rp)
        if i["dependents"]:
            imp = W.impact(iid)
            imp_cache[iid] = imp
            ie = xb.sub(el, "impactAnalysis")
            for lvl, ids in imp["hops"].items():
                xb.sub(ie, "hop", " ".join(ids), level=lvl)
            if imp["systems"]:
                xb.sub(ie, "affectedSystems", ", ".join(sysname(s, on) for s in imp["systems"]))
            if imp["reports"]:
                xb.sub(ie, "affectedReports", ", ".join(imp["reports"]))
            if imp["teams"]:
                xb.sub(ie, "consumerTeams", ", ".join(team_name(t, on) for t in imp["teams"]))
        ups = upstream_hops(iid)
        if ups:
            ln = xb.sub(el, "lineage")
            for lvl, ids in ups.items():
                xb.sub(ln, "upstreamHop", " ".join(ids), level=lvl)
            roots = sorted({W.interfaces[x]["source_system"] for ids in ups.values() for x in ids
                            if not W.interfaces[x]["depends_on"]})
            if roots:
                xb.sub(ln, "originSystems", ", ".join(sysname(s_, on) for s_ in roots))
        # data elements
        de = xb.sub(el, "dataElements")
        layout = None
        if i.get("copybook"):
            layout = i["copybook"]
        elif "RSVMOVE" in i["format"]:
            layout = "RSVMOVE"
        if layout:
            cb = W.copybooks[layout]
            de.set("layout", layout)
            for fd in cb["fields"]:
                if fd["pic"]:
                    xb.sub(de, "element", name=fd["name"], pic=fd["pic"], level=f"{fd['level']:02d}")
        for t in i["tables"]:
            tb = W.tables[t]
            for c in tb["columns"]:
                xb.sub(de, "element", c["description"], name=f"{t}.{c['name']}", type=c["type"],
                       length=c.get("length"), nullable=c["nullable"], pii=c.get("pii", False))
        sec = xb.sub(el, "security", classification="Internal",
                     personalData=any(c.get("pii") for t in i["tables"] for c in W.tables[t]["columns"]))
        xb.sub(sec, "transportSecurity", {"MQ": "TLS on MQ channels", "REST": "HTTPS with CIS-issued tokens",
                                          "SFTP": "SFTP with key-based authentication", "Kafka": "TLS and SASL on esp-prd",
                                          "CICS": "CICS web-service bridge over TLS",
                                          "DB2 unload": "Dataset access controlled by RACF profiles"}[i["protocol"]])
        ctl = xb.sub(el, "controls")
        xb.sub(ctl, "control", phrases.sentence(r, "error_handling"), type="exception-handling")
        xb.sub(ctl, "control", phrases.sentence(r, "interface_ops", i["name"]), type="operations")
        cts = xb.sub(el, "contacts")
        xb.sub(cts, "contact", pname(i["owner"], on), role="interface owner", email=pemail(i["owner"], on))
        tm = W.team_of(i["owner"], on)
        lead = W.team_lead(tm, on) if tm else None
        if lead and lead != i["owner"]:
            xb.sub(cts, "contact", pname(lead, on), role=f"team lead, {team_name(tm, on)}", email=pemail(lead, on))
        for sid_ in dict.fromkeys((i["source_system"], i["target_system"])):
            so = system_owner(sid_, on)
            if so and W.employed(so, on):
                xb.sub(cts, "contact", pname(so, on), role=f"system owner, {sysname(sid_, on)}", email=pemail(so, on))
        rec = xb.sub(el, "reconciliation")
        for s_ in r.sample(phrases.BANKS["reconciliation"], 2):
            xb.sub(rec, "control", s_)
        rb = xb.sub(el, "runbook")
        for k, s_ in enumerate(r.sample(phrases.BANKS["runbook_if"], 4), 1):
            xb.sub(rb, "step", s_, order=k)
        ck = xb.sub(el, "changeImpactChecklist")
        for k, s_ in enumerate(r.sample(phrases.BANKS["impact_checklist"], 5 if i["dependents"] else 4), 1):
            xb.sub(ck, "item", s_, order=k)
        tc = xb.sub(el, "testCases")
        for k, s_ in enumerate(r.sample(phrases.BANKS["tests"], 3), 1):
            xb.sub(tc, "testCase", s_, id=f"{iid}-TC{k:02d}")
        if i["tables"] and i["protocol"] in ("SFTP", "DB2 unload"):
            cols = [c["name"] for c in W.tables[i["tables"][0]]["columns"]]
            xb.sub(el, "sampleHeader", ",".join(cols), table=i["tables"][0])
        if tickets_by_if.get(iid):
            cl = xb.sub(el, "changeLog")
            for t in sorted(tickets_by_if[iid], key=lambda t: str(t["created"])):
                xb.sub(cl, "change", t["summary"], ticket=t["id"], status=t["status"] if str(t.get("resolved") or "9999") <= on else "Open",
                       date=str(t.get("resolved") or t["created"]))
        rh = []
        for sid_ in (i["source_system"], i["target_system"]):
            for rn in W.systems[sid_].get("renames", []):
                if rn["date"] <= on and rn["date"] >= str(i["since"]):
                    rh.append((rn["date"], f"{'Source' if sid_ == i['source_system'] else 'Target'} system renamed "
                                           f"{rn['from_name']} to {rn['to_name']}", rn.get("ticket")))
        if rh:
            he = xb.sub(el, "nameHistory")
            for dte, txt, tk in rh:
                xb.sub(he, "entry", txt, date=dte, ticket=tk)
        if i.get("note"):
            xb.sub(el, "note", i["note"])
    mx = xb.sub(xb.root, "systemInterfaceMatrix")
    for sid in W.systems:
        outs = [i["id"] for i in W.interfaces.values() if i["source_system"] == sid]
        ins = [i["id"] for i in W.interfaces.values() if i["target_system"] == sid]
        if not outs and not ins:
            continue
        se = xb.sub(mx, "system", id=sid, name=sysname(sid, on))
        if outs:
            xb.sub(se, "outbound", " ".join(outs), count=len(outs))
        if ins:
            xb.sub(se, "inbound", " ".join(ins), count=len(ins))
    ed = xb.sub(xb.root, "dependencyEdges")
    for i in W.interfaces.values():
        for d in i["depends_on"]:
            xb.sub(ed, "edge", f"{W.interfaces[d]['name']} -> {i['name']}", upstream=d, downstream=i["id"])
    gl = xb.sub(xb.root, "glossary")
    for term, text in [("Criticality", "Business impact if the interface fails: Critical, High, Medium or Low."),
                       ("Dependent", "An interface that consumes the output of this interface."),
                       ("dependsOn", "An upstream interface whose output this interface needs."),
                       ("Hop", "The number of interface steps between a changed interface and an affected one."),
                       ("Consumer team", "A business team that relies on the data delivered by the interface.")]:
        xb.sub(gl, "term", text, name=term)
    content = xb.bytes("Corvane Mutual - Programme Skerry - Interface Catalogue - Internal")
    F.add("needle", "Interface catalogue: CLX-IF-043, CLX-IF-044, CLX-IF-047 and CLX-IF-049 each have dependsOn CLX-IF-042.",
          xloc("//interface[dependsOn/interfaceRef/@ref='CLX-IF-042']/@id"),
          "CLX-IF-043 CLX-IF-044 CLX-IF-047 CLX-IF-049", world_ref="INTERFACE:CLX-IF-042#dependents",
          placement="PL-172", notes="The CLX-IF-042 schedule is deliberately omitted (exclusive to VS033).")
    F.add("needle", "Interface catalogue: CLX-IF-051 feeds report NISA-TP2; CLX-IF-055 depends on CLX-IF-047; CLX-IF-058 depends on CLX-IF-044.",
          xloc("//interface[@id='CLX-IF-051']/feedsReports"), "NISA-TP2", world_ref="INTERFACE:CLX-IF-051#feeds_reports",
          placement="PL-173")
    F.add("general", "CLX-IF-055 (Monthly Claims Bordereaux) depends on CLX-IF-047.",
          xloc("//interface[@id='CLX-IF-055']/dependsOn"), "CLX-IF-047", world_ref="INTERFACE:CLX-IF-055#depends_on")
    F.add("general", "CLX-IF-058 (Reserve Triangles Extract) depends on CLX-IF-044.",
          xloc("//interface[@id='CLX-IF-058']/dependsOn"), "CLX-IF-044", world_ref="INTERFACE:CLX-IF-058#depends_on")
    F.add("general", "CLX-IF-051 (Technical Provisions Feed) depends on CLX-IF-043.",
          xloc("//interface[@id='CLX-IF-051']/dependsOn"), "CLX-IF-043", world_ref="INTERFACE:CLX-IF-051#depends_on")
    F.add("general", "Impact of CLX-IF-042: hop 2 is CLX-IF-051, CLX-IF-055 and CLX-IF-058.",
          xloc("//interface[@id='CLX-IF-042']/impactAnalysis/hop[@level='2']"), "CLX-IF-051 CLX-IF-055 CLX-IF-058",
          world_ref="INTERFACE:CLX-IF-042#dependents")
    F.add("general", "Impact of CLX-IF-042 reaches report NISA-TP2.",
          xloc("//interface[@id='CLX-IF-042']/impactAnalysis/affectedReports"), "NISA-TP2", world_ref="REPORT:NISA-TP2")
    F.add("general", "CLX-IF-042 is owned by Henrik Vestergaard (Integration Platform Lead), criticality Critical.",
          xloc("//interface[@id='CLX-IF-042']/owner/name"), "Henrik Vestergaard", world_ref="INTERFACE:CLX-IF-042#owner")
    F.add("general", "CLX-IF-042 puts fixed-width RSVMOVE records to queue CLR.RSVMOVE.OUT, written by CLRRS170 in job CLRNRSV3.",
          xloc("//interface[@id='CLX-IF-042']/transport/mqQueue"), "CLR.RSVMOVE.OUT", world_ref="INTERFACE:CLX-IF-042#mq_queue")
    F.add("general", "CLX-IF-042 depends on CLX-IF-027 (Currency rates to CLARA).",
          xloc("//interface[@id='CLX-IF-042']/dependsOn"), "CLX-IF-027", world_ref="INTERFACE:CLX-IF-042#depends_on")
    F.add("temporal", "CLX-IF-043 moved from daily 03:00 to daily 03:45 on 2025-05-09 (CHUB-143).",
          xloc("//interface[@id='CLX-IF-043']/scheduleHistory/entry[2]"), "daily 03:45 from=2025-05-09",
          world_ref="INTERFACE:CLX-IF-043#schedule_history",
          notes="Agrees with the authoritative side of C12; xml text renders children then attributes.")
    F.add("general", "CLX-IF-049 bridges RSVMOVE to Avro on Kafka topic claims.reserve.movement.v1 (schema v3).",
          xloc("//interface[@id='CLX-IF-049']/transport/kafkaTopic"), "claims.reserve.movement.v1",
          world_ref="INTERFACE:CLX-IF-049#kafka_topic")
    F.add("general", "CLX-IF-058 feeds the monthly IBNR run of the Reserving team.",
          xloc("//interface[@id='CLX-IF-058']/note"), "monthly IBNR run of the Reserving team",
          world_ref="INTERFACE:CLX-IF-058#note")
    F.add("general", "CLX-IF-033 (NISA-FR1 fraud referral return) has been live since 2026-07-07.",
          xloc("//interface[@id='CLX-IF-033']/@since"), "2026-07-07", world_ref="INTERFACE:CLX-IF-033#since")
    F.add("general", "CLX-IF-060 (Claims Hub regulatory extracts) is planned, using reporting-feed-svc.",
          xloc("//interface[@id='CLX-IF-060']/@status"), "planned", world_ref="INTERFACE:CLX-IF-060#status")
    F.add("scale", "The interface catalogue lists 60 interfaces (CLX-IF-001 to CLX-IF-060).",
          xloc("//interfaces/@count"), "60", world_ref="INTERFACE:CLX-IF-001")
    F.add("general", "Upstream lineage of CLX-IF-051: hop 1 CLX-IF-043, hop 2 CLX-IF-042, hop 3 CLX-IF-027.",
          xloc("//interface[@id='CLX-IF-051']/lineage/upstreamHop[@level='2']"), "CLX-IF-042",
          world_ref="INTERFACE:CLX-IF-051#depends_on", notes="Derived transitively from depends_on.")
    F.add("general", "CLX-IF-049 is implemented by reserve-engine, which consumes claims.reserve.movement.v1 and triage.completed.v1.",
          xloc("//interface[@id='CLX-IF-049']/implementation/services/service/consumes"), "claims.reserve.movement.v1",
          world_ref="SERVICE:reserve-engine#kafka_topics")
    return Built(fid, content, F.items, f"{len(W.interfaces)} rows")


# ---------------------------------------------------------------------------------------------
# ST036 CLARA program inventory
# ---------------------------------------------------------------------------------------------

PROGRAM_NOTES = {
    "CLRFN030": "Writes the default reserve at FNOL; often missed in reserve-writer lists.",
    "CLRGL090": "Updates RSV_GBP_EQUIV_AMT and RSV_LAST_REVAL_DT on CLR.T_RESERVE without writing CLR.T_RESERVE_MOVEMENT (internal audit finding IA-25-07).",
    "CLRRS150": "Writes reserve movements only; does not update CLR.T_RESERVE.",
    "CLRRS170": "Sets EXTRACTED_FLAG on CLR.T_RESERVE_MOVEMENT and puts RSVMOVE records to queue CLR.RSVMOVE.OUT.",
    "CLRST040": "Sets RSV_OUTSTANDING_AMT to zero on final settlement.",
    "CLRRC050": "Updates RSV_RECOVERY_EST_AMT and RSV_OUTSTANDING_AMT on CLR.T_RESERVE.",
    "CLRFR020": "Endpoint switched to sentinel.corvane.internal under CHUB-119 after INC-2025-0233.",
    "CLRFR040": "Batch sweep reads its referral threshold from a hard-coded working-storage value (WS-REFER-THRESHOLD) instead of CLR.T_PARAM; open defect CHUB-298 (INC-2026-0518).",
    "CLRRS210": "Runs only for the reserve parallel run (2026-03-02 to 2026-08-28) under job CLRDRSV9.",
}


def build_ST036(out_dir: pathlib.Path) -> Built:
    fid = "ST036"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:inventory")
    xb = XB("urn:corvane:skerry:clara-inventory:1", "programInventory", system="CLARA", asOf=on)
    doc_control(xb, xb.root, fid, approvers=["P016"], reviewers=["P023", "P024", "P025"], history_authors=["P052"])
    called_by: dict[str, list[str]] = {}
    for pid, p in W.programs.items():
        for c in p["calls_programs"]:
            called_by.setdefault(c, []).append(pid)
    if_by_prog: dict[str, list[str]] = {}
    for i in W.interfaces.values():
        for p in i["programs"]:
            if_by_prog.setdefault(p, []).append(i["id"])
    rules_by_prog: dict[str, list[str]] = {}
    for rid, rr in W.rules.items():
        v = W.rule_version(rid, on)
        for p in rr["implemented_in"]["programs"]:
            rules_by_prog.setdefault(p, []).append(f"{rid}" + (f" v{v['version']}" if v else " (no version in force)"))
    steps_by_prog: dict[str, list[str]] = {}
    for st in W.steps.values():
        for p in st["programs"]:
            steps_by_prog.setdefault(p, []).append(st["id"])
    progs = [p for p in W.programs.values() if str(p["since"]) <= on]
    summ = xb.sub(xb.root, "summary")
    xb.sub(summ, "programCount", len(progs))
    by_area: dict[str, int] = {}
    for p in progs:
        by_area[p["area"]] = by_area.get(p["area"], 0) + 1
    ba = xb.sub(summ, "byArea")
    for a, n in sorted(by_area.items()):
        xb.sub(ba, "area", n, name=a)
    writers = sorted(p["id"] for p in progs if W.reserve_writers and "CLR.T_RESERVE" in p["writes_tables"])
    assert set(writers) == set(W.reserve_writers), writers
    rw = xb.sub(summ, "reserveTableWriters", table="CLR.T_RESERVE", count=len(writers))
    for w in writers:
        xb.sub(rw, "program", PROGRAM_NOTES.get(w), id=w)
    xb.sub(summ, "movementOnlyWriters", "CLRRS150 writes CLR.T_RESERVE_MOVEMENT but not CLR.T_RESERVE.", table="CLR.T_RESERVE_MOVEMENT")
    xb.sub(summ, "method", "Inventory produced from the source baseline by static analysis of EXEC SQL, CALL and COPY "
                           "statements, then reviewed with the CLARA platform team. " + phrases.sentence(r, "governance"))
    pl = xb.sub(xb.root, "programs")
    for p in progs:
        pid = p["id"]
        status = p["status"]
        if pid == "CLRRS210" and on < "2026-08-28":
            status = "active"
        el = xb.sub(pl, "program", id=pid, type=p["type"], area=p["area"], status=status, since=p["since"], loc=p["loc"])
        if pid == "CLRFR140":
            el.set("disabledOn", "2026-04-01")
        xb.sub(el, "description", p["description"] if pid != "CLRRS210" else
               "Reserve parallel-run reconciliation against reserve-engine")
        xb.sub(el, "runtime", cicsTransaction=p["cics_transaction"], bmsMap=p["bms_map"], jclJob=p["jcl_job"],
               subprogram=p["subprogram"])
        ow = xb.sub(el, "ownership", teamId=p["owner_team"], team=team_name(p["owner_team"], on))
        xb.sub(ow, "developer", pname(p["owner_person"], on), personId=p["owner_person"])
        if p.get("renamed_from"):
            xb.sub(el, "renamedFrom", p["renamed_from"]["old_id"], date=p["renamed_from"]["date"])
        sql = xb.sub(el, "sqlAccess", reads=len(p["reads_tables"]), writes=len(p["writes_tables"]))
        for t in p["reads_tables"]:
            xb.sub(sql, "table", W.tables[t]["description"], name=t, access="read", copybook=W.tables[t].get("copybook"))
        for t in p["writes_tables"]:
            xb.sub(sql, "table", W.tables[t]["description"], name=t, access="write", copybook=W.tables[t].get("copybook"))
        if p["calls_programs"]:
            cs = xb.sub(el, "calls")
            for c in p["calls_programs"]:
                xb.sub(cs, "program", ref=c)
        if called_by.get(pid):
            cb = xb.sub(el, "calledBy")
            for c in sorted(called_by[pid]):
                xb.sub(cb, "program", ref=c)
        cps = xb.sub(el, "copybooks")
        for c in p["copybooks"]:
            cbk = W.copybooks[c]
            xb.sub(cps, "copybook", cbk.get("description"), ref=c, kind=cbk["kind"], table=cbk.get("table"))
        if p["bms_map"] and p["bms_map"] in W.bms_maps:
            bm = W.bms_maps[p["bms_map"]]
            be = xb.sub(el, "screen", map=bm["map"], mapset=bm["mapset"], transaction=bm["transaction"])
            xb.sub(be, "title", bm["title"])
            for fld in bm["fields"]:
                xb.sub(be, "field", name=fld["name"], row=fld["row"], col=fld["col"], length=fld["length"], attr=fld["attr"])
        if if_by_prog.get(pid):
            ii = xb.sub(el, "interfaces")
            for x in if_by_prog[pid]:
                xb.sub(ii, "interface", W.interfaces[x]["name"], ref=x)
        if rules_by_prog.get(pid):
            rr = xb.sub(el, "rules")
            for x in rules_by_prog[pid]:
                xb.sub(rr, "rule", W.rules[x.split(" ")[0]]["title"], ref=x)
        if steps_by_prog.get(pid):
            ss = xb.sub(el, "processSteps")
            for x in steps_by_prog[pid]:
                xb.sub(ss, "step", W.steps[x]["name"], ref=x)
        mig = xb.sub(el, "migration")
        if p["replaced_by"]:
            mig.set("replacedBy", svcname(p["replaced_by"], on))
            mig.set("disposition", "replace")
            mig.text = W.services[p["replaced_by"]]["description"]
        else:
            mig.set("disposition", "retire with CLARA" if p["area"] in ("COMMON", "REPORT") else "retire or absorb")
        xb.sub(el, "profile", (f"{pid} is a{'n' if p['type'] == 'online' else ''} {p['type']} program in the {p['area']} area. "
                               f"It reads {len(p['reads_tables'])} table(s), writes {len(p['writes_tables'])}, calls "
                               f"{len(p['calls_programs'])} program(s) and uses {len(p['copybooks'])} copybook(s)." +
                               (f" It is replaced by {svcname(p['replaced_by'], on)} in Claims Hub." if p["replaced_by"] else "")))
        if PROGRAM_NOTES.get(pid):
            xb.sub(el, "note", PROGRAM_NOTES[pid])
        rv = xb.sub(el, "review", sizeBand=("small" if p["loc"] < 1500 else "medium" if p["loc"] < 4000 else "large"))
        for s_ in r.sample(phrases.BANKS["inventory_review"], 2):
            xb.sub(rv, "comment", s_)
    # table cross-reference (derived from the program entries above)
    ti = xb.sub(xb.root, "tableIndex")
    tabs = sorted({t for p in progs for t in p["reads_tables"] + p["writes_tables"]})
    for t in tabs:
        tb = W.tables[t]
        if str(tb.get("created") or "") > on:
            continue
        te = xb.sub(ti, "table", name=t, db=tb["db"], copybook=tb.get("copybook"))
        xb.sub(te, "description", tb["description"])
        wr = sorted(p["id"] for p in progs if t in p["writes_tables"])
        rd = sorted(p["id"] for p in progs if t in p["reads_tables"])
        if wr:
            xb.sub(te, "writtenBy", " ".join(wr), count=len(wr))
        if rd:
            xb.sub(te, "readBy", " ".join(rd), count=len(rd))
    content = xb.bytes("Corvane Mutual - CLARA program inventory - generated from the CLARA source baseline and reviewed")
    F.add("needle", "Program inventory XML: CLRFR020 renamedFrom FNETCAL1 on 2025-03-01.",
          xloc("//program[@id='CLRFR020']/renamedFrom"), "FNETCAL1 date=2025-03-01",
          world_ref="PROGRAM:CLRFR020#renamed_from", placement="PL-174")
    F.add("general", "Eight programs write CLR.T_RESERVE: CLRFN030, CLRGL090, CLRRC050, CLRRS010, CLRRS020, CLRRS110, CLRRS130, CLRST040.",
          xloc("//summary/reserveTableWriters/program/@id"),
          "CLRFN030 CLRGL090 CLRRC050 CLRRS010 CLRRS020 CLRRS110 CLRRS130 CLRST040",
          world_ref="TABLE:CLR.T_RESERVE#writers")
    F.add("general", "CLRGL090 updates CLR.T_RESERVE without writing a reserve movement (IA-25-07).",
          xloc("//program[@id='CLRGL090']/note"), "without writing CLR.T_RESERVE_MOVEMENT",
          world_ref="PROGRAM:CLRGL090#writes_tables:CLR.T_RESERVE")
    F.add("general", "CLRRS150 writes reserve movements only and does not update CLR.T_RESERVE.",
          xloc("//program[@id='CLRRS150']/note"), "does not update CLR.T_RESERVE", world_ref="PROGRAM:CLRRS150")
    F.add("general", "CLRRS170 (job CLRNRSV3) is the CLX-IF-042 reserve movement extract program.",
          xloc("//program[@id='CLRRS170']/interfaces"), "CLX-IF-042", world_ref="PROGRAM:CLRRS170")
    F.add("general", "CLRFR140 (auto-decline sweep) has status disabled.",
          xloc("//program[@id='CLRFR140']/@status"), "disabled", world_ref="PROGRAM:CLRFR140#status")
    F.add("general", "CLRFR040 batch referral sweep has a hard-coded threshold defect tracked as CHUB-298.",
          xloc("//program[@id='CLRFR040']/note"), "CHUB-298", world_ref="PROGRAM:CLRFR040#hardcoded_constants")
    F.add("general", "CLRFN010 runs under CICS transaction FN01 with BMS map CLRM010.",
          xloc("//program[@id='CLRFN010']/runtime"), "cicsTransaction=FN01", world_ref="PROGRAM:CLRFN010#cics_transaction")
    F.add("scale", f"The CLARA program inventory lists {len(progs)} programs.",
          xloc("//summary/programCount"), str(len(progs)), world_ref="SYSTEM:SYS01")
    F.add("general", "Program inventory table index: CLR.T_RESERVE is written by eight programs.",
          xloc("//tableIndex/table[@name='CLR.T_RESERVE']/writtenBy"),
          "CLRFN030 CLRGL090 CLRRC050 CLRRS010 CLRRS020 CLRRS110 CLRRS130 CLRST040", world_ref="TABLE:CLR.T_RESERVE#writers")
    return Built(fid, content, F.items, f"{len(progs)} rows")


# ---------------------------------------------------------------------------------------------
# ST037 MQ channel and queue definitions
# ---------------------------------------------------------------------------------------------

def build_ST037(out_dir: pathlib.Path) -> Built:
    fid = "ST037"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:mq")
    need(fid, "INTERFACE:CLX-IF-042", "mq_max_depth")
    xb = XB("urn:corvane:skerry:mq-definitions:1", "mqDefinitions", platform="IBM MQ", asOf=on)
    doc_control(xb, xb.root, fid, approvers=["P016", "P032"], reviewers=["P050", "P023"])
    xb.sub(xb.root, "scope", "Queue managers, queues, channels and authority records for the CLARA MQ estate on the "
                             "MQ Backbone (SYS14). Definitions are applied by the Integration Platform team through "
                             "change-controlled MQSC scripts. " + phrases.sentence(r, "governance"))
    qms = xb.sub(xb.root, "queueManagers")
    # queue specs: name, interface, direction, desc, extra
    queues = [
        ("CLR.FNOL.IN", "CLX-IF-001", "inbound", "Portal FNOL submissions (JSON)"),
        ("CLR.EVIDENCE.IN", "CLX-IF-004", "inbound", "Evidence references from EIG (JSON)"),
        ("CLR.SIUREF.OUT", "CLX-IF-011", "outbound", "Fraud referrals to SIU Case Manager (XML)"),
        ("CLR.SIUOUT.IN", "CLX-IF-012", "inbound", "SIU outcomes to CLARA (XML)"),
        ("CLR.SANCTIONS.REQ.OUT", "CLX-IF-017", "outbound", "Sanctions screening requests to WatchScreen (XML)"),
        ("CLR.SANCTIONS.RSP.IN", "CLX-IF-018", "inbound", "Sanctions screening results from WatchScreen (XML)"),
        ("CLR.LLN.OUT", "CLX-IF-031", "outbound", "Large loss notifications to ReCede (XML)"),
        ("CLR.RSVMOVE.OUT", "CLX-IF-042", "outbound", "RSVMOVE reserve movement extract (fixed width)"),
    ]
    q1 = xb.sub(qms, "queueManager", name="CLRQM01", platform="z/OS", host="LPAR PRD1, Leeds Data Centre",
                drHost="LPAR DRP1, Bristol DR Data Centre", owner=pname("P031", on))
    xb.sub(q1, "description", "z/OS queue manager used by CLARA online and batch programs.")
    ql = xb.sub(q1, "queues")
    for name, iid, direction, desc in queues:
        i = W.interfaces[iid]
        qe = xb.sub(ql, "queue", name=name, type="QLOCAL", interface=iid, direction=direction)
        xb.sub(qe, "description", f"{desc}. Interface {iid} {i['name']}.")
        if iid == "CLX-IF-042":
            xb.sub(qe, "maxDepth", W.interfaces[iid]["mq_max_depth"])
            mqsc = (f"DEFINE QLOCAL('{name}') MAXDEPTH({W.interfaces[iid]['mq_max_depth']}) "
                    f"DESCR('{desc[:60]}') DEFPSIST(YES) BOQNAME('{name}.BOQ') SHARE REPLACE")
        else:
            mqsc = (f"DEFINE QLOCAL('{name}') DESCR('{desc[:60]}') DEFPSIST(YES) BOQNAME('{name}.BOQ') SHARE REPLACE")
        xb.sub(qe, "mqsc", mqsc)
        if direction == "outbound":
            xb.sub(qe, "putBy", ", ".join(i["programs"]) or "-")
            cons = [d for d in i["dependents"]] if iid == "CLX-IF-042" else []
            if cons:
                ce = xb.sub(qe, "consumingInterfaces")
                for d in cons:
                    xb.sub(ce, "interfaceRef", W.interfaces[d]["name"], ref=d, target=sysname(W.interfaces[d]["target_system"], on))
            else:
                xb.sub(qe, "consumer", sysname(i["target_system"], on))
        else:
            xb.sub(qe, "getBy", ", ".join(i["programs"]) or "-")
            xb.sub(qe, "producer", sysname(i["source_system"], on))
        if iid != "CLX-IF-042":
            xb.sub(qe, "depthNote", "MAXDEPTH not specified; queue manager default applies.")
        ml = xb.sub(qe, "messageLayout", format=i["format"])
        if i.get("copybook"):
            ml.set("copybook", i["copybook"])
            for fd in W.copybooks[i["copybook"]]["fields"]:
                if fd["pic"]:
                    xb.sub(ml, "field", name=fd["name"], pic=fd["pic"])
        for t in i["tables"]:
            for c in W.tables[t]["columns"]:
                xb.sub(ml, "field", c["description"], name=c["name"].lower(), sourceColumn=f"{t}.{c['name']}", type=c["type"])
        hist = xb.sub(qe, "history")
        xb.sub(hist, "entry", f"Queue in service for {iid} since {i['since']}.", date=i["since"])
        xb.sub(qe, "operations", phrases.sentence(r, "interface_ops", name))
        own = i["owner"]
        xb.sub(qe, "interfaceOwner", pname(own, on), personId=own, title=ptitle(own, on))
        rb = xb.sub(qe, "runbook")
        for k, s_ in enumerate(r.sample(phrases.BANKS["runbook_if"], 4), 1):
            xb.sub(rb, "step", s_, order=k)
        rc = xb.sub(qe, "reconciliation")
        for s_ in r.sample(phrases.BANKS["reconciliation"], 2):
            xb.sub(rc, "control", s_)
        tc = xb.sub(qe, "testCases")
        for k, s_ in enumerate(r.sample(phrases.BANKS["tests"], 3), 1):
            xb.sub(tc, "testCase", s_, id=f"{name}-T{k:02d}")
        bq = xb.sub(ql, "queue", name=f"{name}.BOQ", type="QLOCAL", direction="backout")
        xb.sub(bq, "description", f"Backout queue for {name}.")
        xb.sub(bq, "mqsc", f"DEFINE QLOCAL('{name}.BOQ') DESCR('Backout for {name}') DEFPSIST(YES) REPLACE")
    xq = xb.sub(ql, "queue", name="HUBQM01", type="QLOCAL", usage="XMITQ", direction="transmission")
    xb.sub(xq, "description", "Transmission queue to the distributed queue manager HUBQM01.")
    xb.sub(xq, "mqsc", "DEFINE QLOCAL('HUBQM01') USAGE(XMITQ) TRIGGER TRIGTYPE(FIRST) INITQ('SYSTEM.CHANNEL.INITQ') REPLACE")
    ch = xb.sub(q1, "channels")
    for cname, ctype, desc in [("CLRQM01.TO.HUBQM01", "SDR", "Sender to HUBQM01"),
                               ("HUBQM01.TO.CLRQM01", "RCVR", "Receiver from HUBQM01"),
                               ("CLR.SVRCONN.ADAPTERS", "SVRCONN", "Client connections for integration adapters")]:
        ce = xb.sub(ch, "channel", name=cname, type=ctype)
        xb.sub(ce, "description", desc)
        extra = " XMITQ('HUBQM01') CONNAME('hubqm01.corvane.internal(1414)')" if ctype == "SDR" else ""
        xb.sub(ce, "mqsc", f"DEFINE CHANNEL('{cname}') CHLTYPE({ctype}) TRPTYPE(TCP){extra} SSLCIPH(ANY_TLS12_OR_HIGHER) REPLACE")
    q2 = xb.sub(qms, "queueManager", name="HUBQM01", platform="distributed", host="Corvane private cloud",
                owner=pname("P031", on))
    xb.sub(q2, "description", "Distributed queue manager hosting the adapters for Group Ledger, CDW, ReCede and the Kafka bridge.")
    ch2 = xb.sub(q2, "channels")
    for cname, ctype, desc in [("HUBQM01.TO.CLRQM01", "SDR", "Sender to CLRQM01"),
                               ("CLRQM01.TO.HUBQM01", "RCVR", "Receiver from CLRQM01")]:
        ce = xb.sub(ch2, "channel", name=cname, type=ctype)
        xb.sub(ce, "description", desc)
        xb.sub(ce, "mqsc", f"DEFINE CHANNEL('{cname}') CHLTYPE({ctype}) TRPTYPE(TCP) SSLCIPH(ANY_TLS12_OR_HIGHER) REPLACE")
    ad = xb.sub(q2, "adapters")
    for d in W.interfaces["CLX-IF-042"]["dependents"]:
        i = W.interfaces[d]
        a = xb.sub(ad, "adapter", interface=d, target=sysname(i["target_system"], on))
        xb.sub(a, "description", f"{i['name']}: reads RSVMOVE records for {sysname(i['target_system'], on)}. " +
               phrases.sentence(r, "error_handling"))
    dl = xb.sub(q1, "deadLetter")
    xb.sub(dl, "mqsc", "ALTER QMGR DEADQ('SYSTEM.DEAD.LETTER.QUEUE')")
    xb.sub(dl, "description", "Undeliverable messages go to the system dead-letter queue and are reviewed each morning.")
    li = xb.sub(q1, "listener", name="CLRQM01.LISTENER.TCP", port="1414")
    xb.sub(li, "mqsc", "DEFINE LISTENER('CLRQM01.LISTENER.TCP') TRPTYPE(TCP) PORT(1414) CONTROL(QMGR) REPLACE")
    auth = xb.sub(xb.root, "authorityRecords")
    for prof, grp, perms in [("CLR.FNOL.IN", "CLRPORTL", "PUT"), ("CLR.RSVMOVE.OUT", "CLRBATCH", "PUT"),
                             ("CLR.RSVMOVE.OUT", "INTADAPT", "GET BROWSE INQ"), ("CLR.SIUREF.OUT", "CLRONLN", "PUT"),
                             ("CLR.SIUOUT.IN", "SIUCASE", "PUT"), ("CLR.LLN.OUT", "CLRBATCH", "PUT"),
                             ("CLR.SANCTIONS.REQ.OUT", "CLRBATCH", "PUT"), ("CLR.SANCTIONS.RSP.IN", "WSCREEN", "PUT")]:
        xb.sub(auth, "authRec", f"SET AUTHREC PROFILE('{prof}') OBJTYPE(QUEUE) GROUP('{grp}') AUTHADD({','.join(perms.split())})",
               profile=prof, group=grp)
    notes = xb.sub(xb.root, "operationalNotes")
    for t in ("runbook", "error_handling", "interface_ops"):
        xb.sub(notes, "note", phrases.paragraph(r, t if t != "interface_ops" else "error_handling", 3))
    xb.sub(notes, "note", "INC-2024-0243 (2024-04-01): the MQ channel to Group Ledger stopped after network maintenance "
                          "when the channel retry limit was reached; channel status is now part of the morning checks.")
    content = xb.bytes("Corvane Mutual - MQ Backbone definitions (CLRQM01, HUBQM01) - Internal")
    F.add("needle", "MQ definitions: queue CLR.RSVMOVE.OUT has MAXDEPTH 50000.",
          xloc("//queue[@name='CLR.RSVMOVE.OUT']"), "QLOCAL('CLR.RSVMOVE.OUT') MAXDEPTH(50000)",
          world_ref="INTERFACE:CLX-IF-042#mq_max_depth", exclusive=True, placement="PL-175")
    F.add("general", "Queue CLR.RSVMOVE.OUT is put by CLRRS170 and consumed by interfaces CLX-IF-043, CLX-IF-044, CLX-IF-047 and CLX-IF-049.",
          xloc("//queue[@name='CLR.RSVMOVE.OUT']/consumingInterfaces/interfaceRef/@ref"),
          "CLX-IF-043 CLX-IF-044 CLX-IF-047 CLX-IF-049", world_ref="INTERFACE:CLX-IF-042#dependents")
    F.add("general", "CLARA's z/OS queue manager is CLRQM01; the distributed queue manager is HUBQM01.",
          xloc("//queueManager[@name='CLRQM01']/description"), "z/OS queue manager", world_ref="SYSTEM:SYS14#tech")
    F.add("general", "Queue CLR.SIUREF.OUT carries fraud referrals to SIU Case Manager (CLX-IF-011).",
          xloc("//queue[@name='CLR.SIUREF.OUT']/@interface"), "CLX-IF-011", world_ref="INTERFACE:CLX-IF-011")
    F.add("general", "Large loss notifications to ReCede use queue CLR.LLN.OUT (CLX-IF-031), put by CLRRS160.",
          xloc("//queue[@name='CLR.LLN.OUT']/putBy"), "CLRRS160", world_ref="INTERFACE:CLX-IF-031#programs")
    F.add("general", "The interface owner recorded for queue CLR.RSVMOVE.OUT (CLX-IF-042) is Henrik Vestergaard.",
          xloc("//queue[@name='CLR.RSVMOVE.OUT']/interfaceOwner"), "Henrik Vestergaard", world_ref="INTERFACE:CLX-IF-042#owner")
    return Built(fid, content, F.items, f"{len(queues) * 2 + 1} rows")


# ---------------------------------------------------------------------------------------------
# ST038 NISA-FR1 return 2026Q2
# ---------------------------------------------------------------------------------------------

def build_ST038(out_dir: pathlib.Path) -> Built:
    fid = "ST038"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    rep = W.reports["NISA-FR1"]
    sub = rep["submissions"]["2026Q2"]
    total = sub["referrals"]
    need(fid, "TIMELINE:metrics", "fraud_referrals_count")
    xb = XB("urn:nisa:returns:fr1:2026", "fr1Return", returnCode="NISA-FR1", period="2026Q2", schemaVersion="1.0")
    hd = xb.sub(xb.root, "header")
    xb.sub(hd, "returnName", rep["name"])
    xb.sub(hd, "firmName", W.company["legal_name"])
    xb.sub(hd, "firmReference", W.company["nisa_firm_reference"])
    xb.sub(hd, "periodStart", "2026-04-01")
    xb.sub(hd, "periodEnd", "2026-06-30")
    xb.sub(hd, "dueDate", sub["due"])
    xb.sub(hd, "submittedDate", sub["submitted"])
    xb.sub(hd, "firstReturn", "true")
    xb.sub(hd, "legalBasis", "NISA Circular 2026/04 para 3.4")
    si = xb.sub(hd, "sourceInterfaces")
    for s in rep["source_interfaces"]:
        xb.sub(si, "interface", W.interfaces[s]["name"], id=s)
    xb.sub(hd, "preparedBy", pname(rep["preparer"], on), title=ptitle(rep["preparer"], on))
    xb.sub(hd, "signedBy", pname("P037", on), role=rep["signed_by_role"])
    fig = xb.sub(xb.root, "figures", currency="n/a")
    xb.sub(fig, "referralsTotal", total)
    xb.sub(fig, "referralThreshold", 65, rule="BR-FRD-031 v1", appliesTo="all tiers", effectiveFrom="2026-04-01")
    fq = fr1_data.quarter("2026-04-01", "2026-06-30")
    assert fq["total"] == total, (fq["total"], total)
    bd = {k: fq[k] for k in ("byRegion", "byLine", "byTier", "bySource", "bySystem")}
    for name, vals in bd.items():
        g = xb.sub(fig, name)
        for k, v in vals.items():
            xb.sub(g, "item", v, key=k)
    months = fq["byMonth"]
    mg = xb.sub(fig, "byMonth")
    for k, v in months.items():
        xb.sub(mg, "item", v, key=k)
    cnf = fq["customerNotices"]
    cn = xb.sub(fig, "customerNotices", rule="BR-FRD-032 v2")
    xb.sub(cn, "issuedWithin10BusinessDays", cnf["issuedWithin10BusinessDays"])
    xb.sub(cn, "deferred", cnf["deferred"], rule="BR-FRD-036 v1")
    xb.sub(cn, "pendingAtPeriodEnd", cnf["pendingAtPeriodEnd"])
    xb.sub(fig, "adverseDecisionsOnScoreAlone", 0, rule="BR-FRD-033")
    det = fr1_detail(fq)
    dx = xb.sub(fig, "detail")
    g = xb.sub(dx, "byProduct")
    for x in det["byProduct"]:
        xb.sub(g, "item", x["referrals"], product=x["product"], name=x["name"], region=x["region"])
    g = xb.sub(dx, "byClaimType")
    for x in det["byClaimType"]:
        xb.sub(g, "item", x["referrals"], claimType=x["claimType"], name=x["name"])
    for key in ("byChannel", "noticeTiming"):
        g = xb.sub(dx, key)
        for k, v in det[key].items():
            xb.sub(g, "item", v, key=k)
    for name, rows in (("byRegionAndMonth", bd["byRegion"]), ("byLineAndTier", bd["byLine"])):
        ct = xb.sub(dx, name)
        for rk, cells in fq[name].items():
            row = xb.sub(ct, "row", key=rk, total=rows[rk])
            for ck, v in cells.items():
                xb.sub(row, "cell", v, key=ck)
    wk = xb.sub(dx, "byWeek")
    for x in fq["weekly"]:
        xb.sub(wk, "item", x["referrals"], weekStart=x["weekStart"], weekEnd=x["weekEnd"])
    annex = fr1_annex_records(fq)
    ann = xb.sub(xb.root, "deferralAnnex", rule="BR-FRD-036 v1", records=len(annex),
                 maxDeferralDays=rule_ver("BR-FRD-036", 1)["parameters"]["max_deferral_days"])
    for x in annex:
        rec = xb.sub(ann, "record", claimRef=x["claimRef"], product=x["product"], tier=x["tier"])
        xb.sub(rec, "referralDate", x["referralDate"])
        xb.sub(rec, "noticeDueDate", x["noticeDueDate"], rule="BR-FRD-032 v2")
        xb.sub(rec, "deferral", x["deferredUntil"], days=x["deferralDays"])
        xb.sub(rec, "reason", x["reason"])
    defs = xb.sub(xb.root, "definitions")
    for dd in fr1_definitions(fid, "2026-06-30"):
        xb.sub(defs, "definition", dd["definition"], term=dd["term"], source=dd["source"])
    cts = xb.sub(xb.root, "contacts")
    for role, pid in (("Preparer", rep["preparer"]), ("Signatory", "P037"), ("Counter-Fraud & SIU", "P008")):
        xb.sub(cts, "contact", pname(pid, on), role=role, email=pemail(pid, on), title=ptitle(pid, on))
    dq = xb.sub(xb.root, "dataQualityNotes")
    xb.sub(dq, "note", "INC-2026-0518 (Sev2, 2026-05-12): the nightly CLARA batch fraud sweep used the pre-2026 referral "
                       "threshold; the online referral path was correct. Status at submission: mitigated.",
           incident="INC-2026-0518")
    xb.sub(dq, "note", "First FR1 return under NISA Circular 2026/04; extract program CLRFR090 delivered under CHUB-208.")
    val = xb.sub(xb.root, "validation")
    for k, name in enumerate(["breakdown totals equal referralsTotal", "period dates match the return calendar",
                              "firm reference matches NRH registration", "signatory role matches return definition",
                              "no negative values", "region by month cells reconcile to both breakdowns",
                              "line by tier cells reconcile to both breakdowns", "weekly counts sum to referralsTotal",
                              "deferral annex record count equals deferred notices",
                              "notice timing, deferred and pending counts sum to referralsTotal",
                              "every deferral is within the maximum deferral period",
                              "schema validation against FR1 v1.0"], 1):
        xb.sub(val, "check", "PASS", id=f"V{k:02d}", description=name)
    decl = xb.sub(xb.root, "declaration")
    xb.sub(decl, "text", "I confirm that this return has been prepared in accordance with NISA Circular 2026/04 and "
                         "the return guidance, and that no claim was declined, reduced or repudiated on the basis of an "
                         "automated score alone.")
    content = xb.bytes("NISA-FR1 Quarterly Fraud Referral Return - 2026Q2 - Corvane Mutual - submitted copy")
    vs = [a for a in W.anchors("VS") if a["file_id"] == "VS042"][0]
    F.add("needle", "NISA-FR1 2026Q2 return: 1,488 fraud referrals in Q2 2026.",
          xloc("//figures/referralsTotal"), "1488", world_ref="TIMELINE:metrics#fraud_referrals_count",
          placement="PL-143", also_in=["ST034-F001", f"corpus/upload/visuals/{vs['filename']}"])
    F.add("general", "NISA-FR1 2026Q2 was the first FR1 return: due 2026-07-30, submitted 2026-07-29.",
          xloc("//header/submittedDate"), "2026-07-29", world_ref="REPORT:NISA-FR1#submissions")
    F.add("temporal", "In Q2 2026 the referral threshold was 65 for all tiers (BR-FRD-031 v1, from 2026-04-01).",
          xloc("//figures/referralThreshold"), "65 rule=BR-FRD-031 v1", world_ref="RULE:BR-FRD-031@v1#parameters.threshold")
    F.add("general", "The FR1 Q2 return notes INC-2026-0518: the batch fraud sweep used the pre-2026 threshold.",
          xloc("//dataQualityNotes/note[@incident='INC-2026-0518']"), "pre-2026 referral threshold",
          world_ref="INCIDENT:INC-2026-0518")
    F.add("general", "NISA-FR1 is fed by interface CLX-IF-033.", xloc("//header/sourceInterfaces/interface/@id"),
          "CLX-IF-033", world_ref="REPORT:NISA-FR1#source_interfaces")
    F.add("general", "FR1 Q2 deferral annex: notices may be deferred up to 60 days under BR-FRD-036 v1.",
          xloc("//deferralAnnex/@maxDeferralDays"), "60", world_ref="RULE:BR-FRD-036@v1#parameters.max_deferral_days")
    F.add("general", f"NISA-FR1 2026Q2: {cnf['deferred']} customer notices were deferred under BR-FRD-036 v1 (the deferral annex "
                     f"lists {len(annex)} records); {cnf['issuedWithin10BusinessDays']:,} were issued within 10 business days and "
                     f"{cnf['pendingAtPeriodEnd']} were pending at period end.",
          xloc("//figures/customerNotices/deferred"), str(cnf["deferred"]), world_ref="RULE:BR-FRD-036@v1",
          notes="Computed from the ST015 referral data model (notice_deferred = Y for Q2 2026 referrals).")
    return Built(fid, content, F.items, f"{sum(len(v) for v in bd.values()) + 3} rows")


# ---------------------------------------------------------------------------------------------
# ST039 NISA-TP2 return 2026Q2
# ---------------------------------------------------------------------------------------------

def build_ST039(out_dir: pathlib.Path) -> Built:
    fid = "ST039"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:tp2")
    rep = W.reports["NISA-TP2"]
    need(fid, "REPORT:NISA-TP2", "source_interfaces")
    cfo = W.alias_holder("the CFO", on)
    xb = XB("urn:nisa:returns:tp2:2026", "tp2Return", returnCode="NISA-TP2", period="2026Q2", schemaVersion="3.2",
            unit="GBP thousands")
    hd = xb.sub(xb.root, "header")
    xb.sub(hd, "returnName", rep["name"])
    xb.sub(hd, "firmName", W.company["legal_name"])
    xb.sub(hd, "firmReference", W.company["nisa_firm_reference"])
    xb.sub(hd, "periodEnd", "2026-06-30")
    xb.sub(hd, "dueDate", "2026-08-04")
    xb.sub(hd, "dueRule", rep["due"])
    xb.sub(hd, "submittedDate", "2026-08-04")
    si = xb.sub(hd, "sourceInterfaces")
    for s in rep["source_interfaces"]:
        xb.sub(si, "interface", W.interfaces[s]["name"], id=s, source=sysname(W.interfaces[s]["source_system"], on),
               target=sysname(W.interfaces[s]["target_system"], on))
    xb.sub(hd, "reportingSystem", sysname(rep["system"], on), systemId=rep["system"])
    xb.sub(hd, "preparedBy", pname(rep["preparer"], on), title=ptitle(rep["preparer"], on))
    xb.sub(hd, "signedBy", pname(cfo, on), role=rep["signed_by_role"])
    lin = xb.sub(xb.root, "dataLineage")
    chain = ["CLX-IF-042", "CLX-IF-043", "CLX-IF-051"]
    for k, iid in enumerate(chain, 1):
        i = W.interfaces[iid]
        xb.sub(lin, "step", f"{i['name']}: {sysname(i['source_system'], on)} to {sysname(i['target_system'], on)}",
               order=k, interface=iid)
    xb.sub(lin, "note", "Case reserve movements flow from CLARA through the MQ Backbone into Group Ledger journals; "
                        "the Technical Provisions Feed delivers the TP2 cells to the NISA Reporting Hub.")
    cells = xb.sub(xb.root, "cells")
    combos = [("Motor", "UK", 1.0), ("Home", "UK", 0.62), ("Commercial Property", "UK", 0.38), ("SME Liability", "UK", 0.55),
              ("Motor", "NO", 0.16), ("Home", "NO", 0.12), ("Motor", "SE", 0.13), ("Home", "SE", 0.11),
              ("Motor", "DK", 0.10), ("Home", "DK", 0.08)]
    n = 0
    tot_case = tot_ibnr = 0
    for line, reg, scale in combos:
        for ay in range(2017, 2027):
            age = 2026 - ay
            base = scale * 118000 * (0.45 + 0.55 * max(0.05, 1 - age / 9.5))
            case = int(base * r.uniform(0.85, 1.15))
            ibnr = int(base * (0.42 if age < 2 else 0.22 if age < 5 else 0.08) * r.uniform(0.8, 1.2))
            if line == "SME Liability":
                ibnr = int(ibnr * 1.6)
            tot_case += case
            tot_ibnr += ibnr
            n += 1
            xb.sub(cells, "cell", line=line, region=reg, accidentYear=ay, caseReserves=case, ibnr=ibnr,
                   claimsOutstanding=case + ibnr, cellRef=f"TP2.C{n:03d}")
    tri = xb.sub(xb.root, "paidTriangles", basis="cumulative paid, GBP thousands", region="UK")
    for line, _reg, scale in [c for c in combos if c[1] == "UK"]:
        te = xb.sub(tri, "triangle", line=line)
        for ay in range(2017, 2027):
            ult = scale * 118000 * r.uniform(1.6, 2.1)
            cum = 0.0
            pattern = [0.38, 0.24, 0.13, 0.08, 0.05, 0.04, 0.03, 0.02, 0.015, 0.01]
            for dev in range(1, 2027 - ay + 1):
                cum += ult * pattern[dev - 1] * r.uniform(0.9, 1.1)
                xb.sub(te, "value", int(cum), accidentYear=ay, developmentYear=dev)
    mv = xb.sub(xb.root, "movementAnalysis", period="2026Q2")
    for line, reg, scale in combos:
        opening = int(scale * 118000 * r.uniform(5.5, 6.5))
        paid = int(opening * r.uniform(0.08, 0.12))
        change = int(opening * r.uniform(-0.03, 0.05))
        xb.sub(mv, "row", line=line, region=reg, opening=opening, paidInPeriod=paid, reserveChange=change,
               closing=opening - paid + change)
    totals = xb.sub(xb.root, "totals")
    xb.sub(totals, "caseReserves", tot_case)
    xb.sub(totals, "ibnr", tot_ibnr)
    xb.sub(totals, "claimsOutstanding", tot_case + tot_ibnr)
    hist = xb.sub(xb.root, "submissionHistory")
    for le in rep["late_events"]:
        xb.sub(hist, "lateSubmission", le["note"], period=le["period"], due=le["due"], submitted=le["submitted"],
               incident=le["incident"])
    val = xb.sub(xb.root, "validation")
    for k, name in enumerate(["cells sum to totals", "accident years complete for each line and region",
                              "Group Ledger reserve balance reconciled to case reserves", "no negative cells",
                              "currency conversion at the Group Ledger month-end rate (BR-RSV-012)",
                              "schema validation against TP2 v3.2"], 1):
        xb.sub(val, "check", "PASS", id=f"T{k:02d}", description=name)
    notes = xb.sub(xb.root, "notes")
    xb.sub(notes, "note", "Nordic reserves are converted to GBP at the Group Ledger month-end rate.")
    xb.sub(notes, "note", phrases.sentence(r, "governance"))
    content = xb.bytes("NISA-TP2 Quarterly Technical Provisions Return - 2026Q2 - Corvane Mutual - submitted copy")
    F.add("needle", "TP2 2026Q2 return metadata names source interface CLX-IF-051.",
          xloc("//header/sourceInterfaces"), "CLX-IF-051", world_ref="REPORT:NISA-TP2#source_interfaces",
          placement="PL-176")
    F.add("general", "The TP2 2026Q2 return is signed by the CFO, Priya Raman.",
          xloc("//header/signedBy"), "Priya Raman", world_ref="REPORT:NISA-TP2#signed_by_role")
    F.add("general", "TP2 data lineage: CLX-IF-042 to CLX-IF-043 to CLX-IF-051 (NISA Reporting Hub).",
          xloc("//dataLineage/step/@interface"), "CLX-IF-042 CLX-IF-043 CLX-IF-051", world_ref="INTERFACE:CLX-IF-051#depends_on")
    F.add("general", "TP2 2025Q1 was submitted late on 2025-05-07 (due 2025-05-05) because of INC-2025-0412; NISA granted a 2-day extension.",
          xloc("//submissionHistory/lateSubmission"), "2-day extension granted by Imogen Thackray",
          world_ref="REPORT:NISA-TP2#late_events")
    F.add("general", "NISA-TP2 is due 35 calendar days after quarter end; the 2026Q2 return was due 2026-08-04.",
          xloc("//header/dueRule"), "35 calendar days after quarter end", world_ref="REPORT:NISA-TP2#due")
    return Built(fid, content, F.items, f"{n} rows")


# ---------------------------------------------------------------------------------------------
# ST040 Claims process definition
# ---------------------------------------------------------------------------------------------

RACI_TAG = {"R": "responsible", "A": "accountable", "C": "consulted", "I": "informed"}


def decision_as_of(step_id: str, branch: dict, on: str) -> tuple[str, str | None, str | None]:
    cond, rule, note = branch["condition"], branch.get("rule"), branch.get("note")
    if step_id == "PS-FRD-01":
        v = W.rule_version("BR-FRD-031", on)
        p = v["parameters"]
        if "tier3_threshold" in p:
            cond = cond if cond == "otherwise" else f"sentinel_score >= {p['threshold']} or (tier == 'Tier-3' and sentinel_score >= {p['tier3_threshold']})"
        else:
            cond = cond if cond == "otherwise" else f"sentinel_score >= {p['threshold']}"
        rule = f"BR-FRD-031@v{v['version']}"
    if step_id == "PS-FRD-03" and branch.get("rule") == "BR-FRD-036":
        v = W.rule_version("BR-FRD-036", on)
        if v["version"] == 1:
            note = f"defer up to {v['parameters']['max_deferral_days']} days where SIU certifies a tipping-off risk"
        rule = f"BR-FRD-036@v{v['version']}"
    return cond, rule, note


def build_ST040(out_dir: pathlib.Path) -> Built:
    fid = "ST040"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:process")
    # SLA texts in the world are as of 2026-11-15: check the cited rule versions are the same on the anchor date
    for st in W.steps.values():
        for rid in st["rules"]:
            if rid in ("BR-FRD-031", "BR-FRD-036"):
                continue
            a, b = W.rule_version(rid, on), W.rule_version(rid, "2026-11-15")
            assert (a or {}).get("version") == (b or {}).get("version"), (st["id"], rid)
    xb = XB("urn:corvane:skerry:process:1", "processDefinition", id="CLAIMS-E2E", version="3.0", effectiveFrom="2026-07-01")
    doc_control(xb, xb.root, fid, approvers=["P005"], reviewers=["P017", "P054", "P008", "P009", "P013"])
    xb.sub(xb.root, "name", "Claims handling end to end (FNOL to Recovery)")
    xb.sub(xb.root, "purpose", "Defines the stages, steps, decisions, service levels and RACI of the Corvane claims "
                               "process, and maps each step to the CLARA programs and Claims Hub services that support "
                               "it. " + phrases.sentence(r, "governance"))
    stages = xb.sub(xb.root, "stages")
    rule_ids = set()
    for s in sorted(W.stages.values(), key=lambda x: x["order"]):
        owner = W.owner_of_process(s["id"], on)
        se = xb.sub(stages, "stage", id=s["id"], code=s["code"], order=s["order"])
        xb.sub(se, "name", s["name"])
        oe = xb.sub(se, "owner", pname(owner, on), personId=owner, title=ptitle(owner, on))
        sy = xb.sub(se, "systems")
        for sid in s["systems"]:
            xb.sub(sy, "system", sysname(sid, on), id=sid)
        steps = xb.sub(se, "steps")
        for sid in s["steps"]:
            st = W.steps[sid]
            ste = xb.sub(steps, "step", id=sid, order=st["order"])
            xb.sub(ste, "name", st["name"])
            xb.sub(ste, "description", st["description"])
            xb.sub(ste, "sla", st["sla"]["text"], value=st["sla"]["value"], unit=st["sla"]["unit"])
            ra = xb.sub(ste, "raci")
            for k in ("R", "A", "C", "I"):
                v = st["raci"][k]
                vals = v if isinstance(v, list) else [v]
                for x in vals:
                    if x in W.teams:
                        if team_exists(x, on):
                            xb.sub(ra, RACI_TAG[k], team_name(x, on), team=x)
                    else:
                        xb.sub(ra, RACI_TAG[k], pname(x, on), personId=x, title=ptitle(x, on))
            if st["decision"]:
                de = xb.sub(ste, "decision")
                xb.sub(de, "question", st["decision"]["question"])
                for b in st["decision"]["branches"]:
                    cond, rule, note = decision_as_of(sid, b, on)
                    xb.sub(de, "branch", note, condition=cond, next=b["next"] or "end", rule=rule)
            if st["next"]:
                nx = xb.sub(ste, "next")
                for x in st["next"]:
                    xb.sub(nx, "stepRef", ref=x)
            if st["programs"]:
                pr = xb.sub(ste, "claraPrograms")
                for x in st["programs"]:
                    xb.sub(pr, "program", W.programs[x]["description"], id=x)
            if st["services"]:
                sv = xb.sub(ste, "hubServices")
                for x in st["services"]:
                    xb.sub(sv, "service", svcname(x, on))
            if st["systems"]:
                sy2 = xb.sub(ste, "systems")
                for x in st["systems"]:
                    xb.sub(sy2, "system", sysname(x, on), id=x)
            if st["rules"]:
                ru = xb.sub(ste, "rules")
                for rid in st["rules"]:
                    v = W.rule_version(rid, on)
                    rule_ids.add(rid)
                    xb.sub(ru, "ruleRef", W.rules[rid]["title"], ref=rid, version=v["version"] if v else None)
    # rule catalogue with text where allowed
    rc = xb.sub(xb.root, "ruleCatalogue", asOf=on)
    for rid in sorted(rule_ids):
        v = W.rule_version(rid, on)
        if not v:
            continue
        re_ = xb.sub(rc, "rule", id=rid, version=v["version"], effectiveFrom=v["effective_from"], owner=pname(W.rules[rid]["owner"], on))
        xb.sub(re_, "title", W.rules[rid]["title"])
        if rule_text_ok(fid, rid, v["version"]):
            xb.sub(re_, "text", v["text"])
        else:
            xb.sub(re_, "text", "See the Claims Handling Manual for the wording of this rule.")
    content = xb.bytes("Corvane Mutual - Claims process definition v3.0 - approved")
    F.add("general", "Process definition (2026-07-13): the Recovery & Subrogation stage S7 is owned by Freya Lindahl, Head of Recoveries & Subrogation.",
          xloc("//stage[@id='S7']/owner"), "Freya Lindahl", world_ref="PROCESS:S7#owner_history")
    F.add("temporal", "As at 2026-07-13 the referral decision PS-FRD-01 refers at a Sentinel score of 65 or more for all claims (BR-FRD-031 v1).",
          xloc("//step[@id='PS-FRD-01']/decision/branch[1]/@condition"), "sentinel_score >= 65",
          world_ref="RULE:BR-FRD-031@v1#parameters.threshold")
    F.add("general", "Step PS-FRD-03: notify the customer within 10 business days of referral (BR-FRD-032 v2).",
          xloc("//step[@id='PS-FRD-03']/sla"), "within 10 business days of referral", world_ref="PROCESS:PS-FRD-03#sla")
    F.add("general", "Step PS-RSV-03: Tier-3 reserves reviewed every 14 days (BR-RSV-007 v3).",
          xloc("//step[@id='PS-RSV-03']/sla"), "Tier-3 every 14 days", world_ref="PROCESS:PS-RSV-03#sla")
    F.add("general", "Step PS-REC-02 decision: pursue subrogation where the recoverable amount is £1,000 or more (BR-REC-003 v3).",
          xloc("//step[@id='PS-REC-02']/decision/branch[1]/@condition"), "recoverable_gbp >= 1000",
          world_ref="RULE:BR-REC-003@v3#parameters.min_gbp")
    F.add("general", "Reserving stage S4 is owned by Lena Kristiansen, Head of Reserving.",
          xloc("//stage[@id='S4']/owner"), "Lena Kristiansen", world_ref="PROCESS:S4#owner_history")
    F.add("general", "Step PS-FNOL-05: acknowledge digital FNOLs within 1 business day and other channels within 2 (BR-FNOL-001 v3).",
          xloc("//step[@id='PS-FNOL-05']/sla"), "1 business day digital, 2 business days other channels",
          world_ref="RULE:BR-FNOL-001@v3")
    F.add("general", "Step PS-REC-06: write-offs above £10,000 need the Head of Recoveries & Subrogation (BR-REC-011 v2).",
          xloc("//step[@id='PS-REC-06']/decision/branch[1]"), "approval by the Head of Recoveries & Subrogation",
          world_ref="RULE:BR-REC-011@v2")
    return Built(fid, content, F.items, f"{len(W.steps)} rows")


# ---------------------------------------------------------------------------------------------
# ST041 Copybook schemas
# ---------------------------------------------------------------------------------------------

def pic_length(pic: str | None) -> int:
    if not pic:
        return 0
    p = pic.upper().replace(" ", "")
    usage = "DISPLAY"
    for u in ("COMP-3", "COMP"):
        if p.endswith(u):
            usage = u
            p = p[: -len(u)]
            break
    p = p.lstrip("S")
    digits = 0
    chars = 0
    for m in re.finditer(r"([X9AV])(?:\((\d+)\))?", p):
        sym, n = m.group(1), int(m.group(2) or 1)
        if sym == "V":
            continue
        if sym == "9":
            digits += n
        chars += n
    if usage == "COMP-3":
        return digits // 2 + 1
    if usage == "COMP":
        return 2 if digits <= 4 else 4 if digits <= 9 else 8
    return chars


def layout(fields: list[dict]) -> list[dict]:
    """Offsets (1-based) and lengths for a flat COBOL field list with level numbers."""
    out = []
    off = 1
    stack: list[dict] = []
    for f in fields:
        lvl = f["level"]
        while stack and stack[-1]["level"] >= lvl:
            stack.pop()
        rec = {"name": f["name"], "level": lvl, "pic": f["pic"], "offset": off, "length": pic_length(f["pic"]),
               "group": f["pic"] is None, "parents": [s["name"] for s in stack]}
        out.append(rec)
        if f["pic"]:
            off += rec["length"]
        else:
            stack.append(rec)
    for rec in out:
        if rec["group"]:
            kids = [x for x in out if rec["name"] in x["parents"] and not x["group"]]
            rec["length"] = sum(k["length"] for k in kids)
    return out


def cobol_source(cb: dict, lay: list[dict]) -> str:
    lines = ["      *" + "=" * 64 + "*", f"      * COPYBOOK : {cb['name']:<54}*"]
    desc = cb.get("description") or (f"Record layout for table {cb['table']}" if cb.get("table") else cb["kind"])
    lines.append(f"      * PURPOSE  : {desc[:54]:<54}*")
    lines.append("      *" + "=" * 64 + "*")
    for f in lay:
        indent = 7 + {1: 1, 5: 5, 10: 9, 15: 13}.get(f["level"], 5)
        head = " " * indent + f"{f['level']:02d}  {f['name']}"
        if f["pic"]:
            lines.append(f"{head:<44}PIC {f['pic']}.")
        else:
            lines.append(head + ".")
    return "\n".join(lines)


def build_ST041(out_dir: pathlib.Path) -> Built:
    fid = "ST041"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:copybooks")
    xb = XB("urn:corvane:skerry:copybooks:1", "copybookSchemas", system="CLARA", asOf=on)
    doc_control(xb, xb.root, fid, approvers=["P016"], reviewers=["P023", "P025"], history_authors=["P052"])
    xb.sub(xb.root, "method", "Copybooks parsed from the CLARA source baseline. Offsets are 1-based; lengths are "
                              "storage bytes (COMP-3 packed, COMP binary). " + phrases.sentence(r, "governance"))
    used_by: dict[str, list[str]] = {}
    for p in W.programs.values():
        for c in p["copybooks"]:
            used_by.setdefault(c, []).append(p["id"])
    cl = xb.sub(xb.root, "copybooks", count=len(W.copybooks))
    for name, cb in W.copybooks.items():
        lay = layout(cb["fields"])
        reclen = sum(x["length"] for x in lay if not x["group"])
        ce = xb.sub(cl, "copybook", name=name, kind=cb["kind"], recordLength=reclen)
        if cb.get("table"):
            ce.set("table", cb["table"])
        if cb.get("description"):
            xb.sub(ce, "description", cb["description"])
        fe = xb.sub(ce, "fields")
        cols = {c["name"]: c for c in W.tables[cb["table"]]["columns"]} if cb.get("table") else {}
        for f in lay:
            el = xb.sub(fe, "field", level=f"{f['level']:02d}", offset=f["offset"], length=f["length"],
                        group=f["group"])
            xb.sub(el, "name", f["name"])
            if f["pic"]:
                xb.sub(el, "pic", f["pic"])
            col = f["name"].split("-", 1)[1].replace("-", "_") if "-" in f["name"] else None
            if col and col in cols:
                c = cols[col]
                xb.sub(el, "column", c["description"], name=col, type=c["type"], nullable=c["nullable"])
        ub = sorted(set(used_by.get(name, []) + list(cb.get("used_by") or [])))
        if ub:
            u = xb.sub(ce, "usedBy")
            for p in ub:
                xb.sub(u, "program", ref=p)
        if cb.get("field_history"):
            ch = xb.sub(ce, "changeLog")
            for h in cb["field_history"]:
                if h["date"] <= on:
                    xb.sub(ch, "change", h["note"], field=h["field"], fromPic=h["from_pic"], toPic=h["to_pic"],
                           date=h["date"], ticket=h["ticket"])
        src = xb.sub(ce, "source")
        src.text = etree.CDATA("\n" + cobol_source(cb, lay) + "\n")
    content = xb.bytes("Corvane Mutual - CLARA copybook schemas - generated from the source baseline")
    F.add("needle", "Copybook schema RSVMOVE: RM-AMOUNT PIC S9(9)V99 COMP-3; RM-REC-VERSION PIC 9(2).",
          xloc("//copybook[@name='RSVMOVE']/fields/field[name='RM-AMOUNT']"), "RM-AMOUNT S9(9)V99 COMP-3",
          world_ref="COPYBOOK:RSVMOVE#fields", placement="PL-177")
    F.add("general", "RSVMOVE field RM-REC-VERSION is PIC 9(2) (record version byte added 2025-04-30, CHUB-142).",
          xloc("//copybook[@name='RSVMOVE']/fields/field[name='RM-REC-VERSION']"), "RM-REC-VERSION 9(2)",
          world_ref="COPYBOOK:RSVMOVE#fields")
    F.add("temporal", "RSVMOVE RM-AMOUNT was widened to S9(11)V99 COMP-3 on 2025-04-25 (CHUB-138) and reverted on 2025-04-30 (CHUB-142).",
          xloc("//copybook[@name='RSVMOVE']/changeLog"), "Widened for Nordic large losses; broke CLX-IF-043 (INC-2025-0412)",
          world_ref="COPYBOOK:RSVMOVE#field_history")
    F.add("general", "Copybook RSVMOVE is the CLX-IF-042 fixed-width record (queue CLR.RSVMOVE.OUT), used by CLRRS170.",
          xloc("//copybook[@name='RSVMOVE']/usedBy"), "CLRRS170", world_ref="COPYBOOK:RSVMOVE#used_by")
    F.add("scale", f"The copybook schema file describes {len(W.copybooks)} CLARA copybooks.",
          xloc("//copybooks/@count"), str(len(W.copybooks)), world_ref="SYSTEM:SYS01")
    return Built(fid, content, F.items, f"{len(W.copybooks)} rows")


# ---------------------------------------------------------------------------------------------
# ST042 JCL schedule
# ---------------------------------------------------------------------------------------------

def copybook_fields_as_of(name: str, on: str) -> list[dict]:
    """Copybook fields as they stood on `on` (field_history changes after `on` are undone)."""
    fields = [dict(f) for f in W.copybooks[name]["fields"]]
    for h in sorted(W.copybooks[name].get("field_history") or [], key=lambda x: str(x["date"]), reverse=True):
        if str(h["date"]) <= on:
            continue
        for f in fields:
            if f["name"] == h["field"]:
                f["pic"] = h["from_pic"]
        fields = [f for f in fields if not (f["name"] == h["field"] and f["pic"] is None)]
    return fields


def dataset_lrecl(ds: dict, steps: list[dict], on: str) -> int:
    """Record length of a job dataset: the layout of the step copybook named in the DSN (RSVOUT -> RSVMOVE)."""
    quals = re.split(r"[.(]", ds["dsn"])
    for st in steps:
        for c in W.programs[st["program"]]["copybooks"]:
            if c in quals:
                return sum(x["length"] for x in layout(copybook_fields_as_of(c, on)) if not x["group"])
    raise ValueError(f"no record layout for dataset {ds['dsn']}")


def jcl_text(job: dict, steps: list[dict], desc: str, on: str) -> str:
    out = [f"//{job['name']:<8} JOB (CLR,BATCH),'{desc[:20].upper()}',CLASS=B,MSGCLASS=X,", "//         NOTIFY=&SYSUID"]
    for st in steps:
        out.append(f"//{st['step']:<8} EXEC PGM={st['program']}")
        out.append("//STEPLIB  DD DSN=CLR.PROD.LOADLIB,DISP=SHR")
        for ds in job["datasets"]:
            out.append(f"//{ds['dd']:<8} DD DSN={ds['dsn']},DISP=(NEW,CATLG,DELETE),")
            out.append(f"//            SPACE=(CYL,(20,10),RLSE),DCB=(RECFM=FB,LRECL={dataset_lrecl(ds, steps, on)},BLKSIZE=0)")
        out.append("//SYSOUT   DD SYSOUT=*")
    return "\n".join(out)


def build_ST042(out_dir: pathlib.Path) -> Built:
    fid = "ST042"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:jcl")
    xb = XB("urn:corvane:skerry:batch-schedule:1", "batchSchedule", system="CLARA", scheduler="Batch Scheduler", asOf=on)
    doc_control(xb, xb.root, fid, approvers=["P016"], reviewers=["P023", "P025"])
    hdr = xb.sub(xb.root, "scheduleHeader")
    xb.sub(hdr, "scheduler", sysname("SYS18", on), systemId="SYS18")
    xb.sub(hdr, "batchWindow", W.systems["SYS01"]["batch_window"])
    xb.sub(hdr, "ownerTeam", team_name("T25", on), teamId="T25")
    xb.sub(hdr, "contact", pname("P026", on), title=ptitle("P026", on))
    xb.sub(hdr, "calendar", "UK business-day calendar with Nordic holidays applied to Nordic jobs")
    job_list = jcl_jobs_as_of(on)   # only jobs/programs that exist on the schedule date
    jobs = xb.sub(xb.root, "jobs", count=len(job_list))
    for name, j, steps in job_list:
        ref = f"JCL:{name}"
        desc = j["description"]
        status = j["status"]
        sched = j["schedule"]
        if name == "CLRDRSV9" and on < "2026-08-28":
            status = "active"
            desc = "Reserve parallel-run reconciliation"
        je = xb.sub(jobs, "job", name=name, status=status, ownerTeam=j["owner_team"], scheduler=j["scheduler"])
        xb.sub(je, "description", desc)
        if may(fid, ref, "schedule"):
            xb.sub(je, "schedule", sched)
        else:
            xb.sub(je, "schedule", "held in the Batch Scheduler calendar (not reproduced here)", published="false")
        se = xb.sub(je, "steps")
        for st in steps:
            p = W.programs[st["program"]]
            ste = xb.sub(se, "step", name=st["step"], program=st["program"], area=p["area"])
            xb.sub(ste, "description", st["description"])
            if p["reads_tables"]:
                xb.sub(ste, "reads", " ".join(p["reads_tables"]))
            if p["writes_tables"]:
                xb.sub(ste, "writes", " ".join(p["writes_tables"]))
            xb.sub(ste, "copybooks", " ".join(p["copybooks"]))
            xb.sub(ste, "developer", pname(p["owner_person"], on), email=pemail(p["owner_person"], on))
        if j["datasets"]:
            de = xb.sub(je, "datasets")
            for ds in j["datasets"]:
                xb.sub(de, "dataset", ds["dsn"], dd=ds["dd"])
        ifs = sorted({i["id"] for i in W.interfaces.values() for st in steps
                      if st["program"] in i["programs"] and interface_exists(i["id"], on)})
        if ifs:
            ie = xb.sub(je, "interfaces")
            for x in ifs:
                xb.sub(ie, "interface", W.interfaces[x]["name"], ref=x)
        if j["restart"] and may(fid, ref, "restart"):
            xb.sub(je, "restart", j["restart"])
        elif j["restart"]:
            xb.sub(je, "restart", "See the CLARA batch restart table.")
        else:
            xb.sub(je, "restart", "Standard restart: rerun from the failed step after the cause is fixed.")
        jt = xb.sub(je, "jcl")
        jt.text = etree.CDATA("\n" + jcl_text(j, steps, desc, on) + "\n")
        aa = xb.sub(je, "abendActions")
        for k, s_ in enumerate(r.sample(phrases.BANKS["runbook"], 3), 1):
            xb.sub(aa, "action", s_, order=k)
    content = xb.bytes("Corvane Mutual - CLARA JCL schedule - approved")
    F.add("general", "Job CLRNRSV3 runs CLRRS170 (STEP010) and writes dataset CLR.PROD.RSVMOVE.DAILY(+1) via DD RSVOUT.",
          xloc("//job[@name='CLRNRSV3']/datasets"), "CLR.PROD.RSVMOVE.DAILY(+1)", world_ref="JCL:CLRNRSV3#datasets",
          notes="The CLRNRSV3 schedule is deliberately not stated (guarded by the CLX-IF-042 schedule, VS033).")
    F.add("general", "CLRNRSV3 restart: rerun the whole job; CLRRS170 only extracts rows with EXTRACTED_FLAG = 'N'.",
          xloc("//job[@name='CLRNRSV3']/restart"), "only extracts rows with EXTRACTED_FLAG", world_ref="JCL:CLRNRSV3#restart")
    F.add("general", "Job CLRNRSV1 (Tier-3 reserve review and revaluation) runs daily at 01:30.",
          xloc("//job[@name='CLRNRSV1']/schedule"), "daily 01:30", world_ref="JCL:CLRNRSV1#schedule")
    F.add("general", "Job CLRNFR99 (auto-decline sweep, CLRFR140) was removed from the schedule on 2026-04-01; it previously ran daily at 00:45.",
          xloc("//job[@name='CLRNFR99']/schedule"), "removed from schedule 2026-04-01 (was daily 00:45)",
          world_ref="JCL:CLRNFR99#schedule")
    F.add("temporal", "As at 2026-05-18 job CLRDRSV9 (reserve parallel-run reconciliation) was active, daily 05:00 for 2026-03-02 to 2026-08-28.",
          xloc("//job[@name='CLRDRSV9']/@status"), "active", world_ref="JCL:CLRDRSV9#status")
    F.add("general", "Job CLRNFR01 (nightly fraud scoring and referral sweep) runs CLRFR110, CLRFR080 and CLRFR040 at 00:15.",
          xloc("//job[@name='CLRNFR01']/steps"), "CLRFR040", world_ref="JCL:CLRNFR01#steps")
    F.add("general", "The CLARA batch window is 23:30–05:30 UK time.", xloc("//scheduleHeader/batchWindow"),
          "23:30–05:30 UK time", world_ref="SYSTEM:SYS01#batch_window")
    return Built(fid, content, F.items, f"{len(job_list)} rows")


BUILDERS = {
    "ST035": build_ST035, "ST036": build_ST036, "ST037": build_ST037, "ST038": build_ST038,
    "ST039": build_ST039, "ST040": build_ST040, "ST041": build_ST041, "ST042": build_ST042,
}
