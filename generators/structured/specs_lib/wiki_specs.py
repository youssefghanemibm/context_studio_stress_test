"""Wiki export pages ST053-ST060 (Confluence-like HTML with nested tables, macros and cross links)."""
from __future__ import annotations

import html
import pathlib

from generators.common import util

from .core import (W, Built, Facts, add_business_days, fauthor, fdate, fname, ftitle, human_date, may, minus_days,
                   need, pemail, pname, ptitle, pcity, rule_params_ok, rule_text_ok, rule_ver, svcname, sysname,
                   team_exists, team_name)
from . import phrases
from .xml_specs import layout as cobol_layout, system_owner
from .yaml_specs import MOVEMENT_FIELDS, RSV_ERROR_CODES

PAGES = ["ST053", "ST058", "ST054", "ST059", "ST055", "ST057", "ST056", "ST060"]
PAGE_TITLE = {
    "ST053": "Claims Hub Home",
    "ST054": "CLX-IF-042 Reserve Movement Daily Extract",
    "ST055": "Glossary",
    "ST056": "CLARA Batch Runbook",
    "ST057": "Team Directory",
    "ST058": "reserve-engine Design",
    "ST059": "Fraud Rules 2026",
    "ST060": "Release Notes",
}
TREE = [("ST053", 0), ("Architecture", 1), ("ST058", 2), ("Interfaces", 1), ("ST054", 2), ("ST059", 1),
        ("ST055", 1), ("ST057", 1), ("ST056", 1), ("ST060", 1)]
PARENT = {"ST058": "Architecture", "ST054": "Interfaces"}

CSS = """body{font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#172b4d;margin:0}
#page{display:flex}#sidebar{width:240px;background:#f4f5f7;padding:12px;font-size:13px}
#main{flex:1;padding:16px 24px}table.confluenceTable{border-collapse:collapse;margin:8px 0}
th.confluenceTh,td.confluenceTd{border:1px solid #c1c7d0;padding:4px 8px;vertical-align:top}
th.confluenceTh{background:#f4f5f7}table.nested{margin:0}
.confluence-information-macro{border:1px solid #c1c7d0;padding:8px 12px;margin:10px 0;border-radius:3px}
.confluence-information-macro-information{background:#deebff}.confluence-information-macro-warning{background:#ffebe6}
.confluence-information-macro-note{background:#fffae6}.confluence-information-macro-tip{background:#e3fcef}
pre.syntaxhighlighter-pre{background:#f4f5f7;padding:8px;overflow:auto;font-family:monospace}
.status-macro{font-size:11px;font-weight:bold;padding:1px 4px;border-radius:3px;background:#dfe1e6}
.aui-lozenge-success{background:#e3fcef}.aui-lozenge-current{background:#deebff}.aui-lozenge-error{background:#ffebe6}
#breadcrumbs li{display:inline;list-style:none}#breadcrumbs li:after{content:' / '}"""


def e(s) -> str:
    return html.escape(str(s), quote=True)


def a(fid: str, text: str | None = None) -> str:
    return f'<a href="{fname(fid)}">{e(text or PAGE_TITLE[fid])}</a>'


def table(headers: list[str] | None, rows: list[list[str]], tid: str | None = None, cls: str = "confluenceTable",
          row_ids: list[str | None] | None = None, raw: bool = True) -> str:
    out = [f'<table class="{cls}"' + (f' id="{tid}"' if tid else "") + "><tbody>"]
    if headers:
        out.append("<tr>" + "".join(f'<th class="confluenceTh">{e(h)}</th>' for h in headers) + "</tr>")
    for k, r in enumerate(rows):
        rid = row_ids[k] if row_ids else None
        out.append("<tr" + (f' id="{rid}"' if rid else "") + ">" +
                   "".join(f'<td class="confluenceTd">{c if raw else e(c)}</td>' for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def kv_table(pairs: list[tuple[str, str]], tid: str | None = None, cls: str = "confluenceTable") -> str:
    out = [f'<table class="{cls}"' + (f' id="{tid}"' if tid else "") + "><tbody>"]
    for k, v in pairs:
        out.append(f'<tr><th class="confluenceTh">{e(k)}</th><td class="confluenceTd">{v}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


def macro(kind: str, body: str, title: str | None = None, mid: str | None = None) -> str:
    t = f'<p class="title"><strong>{e(title)}</strong></p>' if title else ""
    icon = {"information": "info", "warning": "warning", "note": "warning", "tip": "check"}[kind]
    return (f'<div class="confluence-information-macro confluence-information-macro-{kind}"' +
            (f' id="{mid}"' if mid else "") + f'>{t}<span class="aui-icon aui-icon-small aui-iconfont-{icon} '
            f'confluence-information-macro-icon"></span><div class="confluence-information-macro-body">{body}</div></div>')


def code(lang: str, text: str, cid: str | None = None) -> str:
    return (f'<div class="code panel pdl"' + (f' id="{cid}"' if cid else "") + '><div class="codeContent panelContent pdl">'
            f'<pre class="syntaxhighlighter-pre" data-syntaxhighlighter-params="brush: {lang}; gutter: false; '
            f'theme: Confluence" data-theme="Confluence">{e(text)}</pre></div></div>')


def status(text: str, kind: str = "current") -> str:
    return f'<span class="status-macro aui-lozenge aui-lozenge-{kind}">{e(text.upper())}</span>'


def p(text: str, raw: bool = False, pid: str | None = None) -> str:
    return "<p" + (f' id="{pid}"' if pid else "") + ">" + (text if raw else e(text)) + "</p>"


def h(level: int, text: str, hid: str | None = None) -> str:
    return f"<h{level}" + (f' id="{hid}"' if hid else "") + f">{e(text)}</h{level}>"


def ul(items: list[str], raw: bool = False, uid: str | None = None) -> str:
    return "<ul" + (f' id="{uid}"' if uid else "") + ">" + "".join(f"<li>{i if raw else e(i)}</li>" for i in items) + "</ul>"


def page_tree(current: str) -> str:
    out = ['<div id="sidebar"><div class="pagetree-header"><strong>Claims Hub (CHUB)</strong></div><ul class="page-tree">']
    for node, lvl in TREE:
        pad = "&nbsp;&nbsp;" * lvl
        if node in PAGE_TITLE:
            label = PAGE_TITLE[node]
            if node == current:
                out.append(f'<li class="current">{pad}<strong>{e(label)}</strong></li>')
            else:
                out.append(f"<li>{pad}{a(node)}</li>")
        else:
            out.append(f'<li class="folder">{pad}{e(node)}</li>')
    out.append("</ul></div>")
    return "".join(out)


def render_page(fid: str, body: str, labels: list[str], comments: list[tuple[str, str, str]] | None = None,
                attachments: list[str] | None = None) -> bytes:
    on = fdate(fid)
    author = fauthor(fid)
    r = util.rng(f"{fid}:meta")
    created = minus_days(on, r.randint(40, 300))
    creator = author
    title = PAGE_TITLE[fid]
    crumbs = ['<li class="first"><span>Claims Hub</span></li>']
    if fid != "ST053":
        crumbs.append(f"<li><span>{a('ST053')}</span></li>")
    if fid in PARENT:
        crumbs.append(f"<li><span>{e(PARENT[fid])}</span></li>")
    meta = (f'<div class="page-metadata">Created by <span class="author">{e(pname(creator, created))}</span>, '
            f'last modified by <span class="editor">{e(pname(author, on))}</span> on '
            f'<span class="last-modified" data-date="{on}">{human_date(on)}</span></div>')
    lab = ('<div class="labels-section"><span class="labels-title">Labels:</span> ' +
           " ".join(f'<a class="label" href="#label-{e(l)}">{e(l)}</a>' for l in labels) + "</div>")
    att = ""
    if attachments:
        att = '<div class="pageSection group" id="attachments"><h2>Attachments</h2>' + ul(attachments) + "</div>"
    com = ""
    if comments:
        items = []
        for who, when, text in comments:
            items.append(f'<div class="comment"><div class="comment-header"><strong>{e(pname(who, when))}</strong> '
                         f'<span class="date">{human_date(when)}</span></div><div class="comment-content">{p(text)}</div></div>')
        com = '<div class="pageSection group" id="comments-section"><h2>Comments</h2>' + "".join(items) + "</div>"
    doc = f"""<!DOCTYPE html>
<html>
<head>
<title>Claims Hub : {e(title)}</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="confluence-space-key" content="CHUB">
<meta name="page-last-modified" content="{on}">
<style>{CSS}</style>
</head>
<body class="theme-default aui-theme-default">
<div id="page">
{page_tree(fid)}
<div id="main" class="aui-page-panel">
<div id="main-header">
<div id="breadcrumb-section"><ol id="breadcrumbs">{"".join(crumbs)}</ol></div>
<h1 id="title-heading" class="pagetitle"><span id="title-text">Claims Hub : {e(title)}</span></h1>
</div>
<div id="content" class="view">
{meta}
<div id="main-content" class="wiki-content group">
{body}
</div>
{lab}
{att}
{com}
</div>
<div id="footer"><section class="footer-body"><p>Document generated by the wiki export on {on}. Corvane Mutual – Internal.</p></section></div>
</div>
</div>
</body>
</html>
"""
    return doc.encode("utf-8")


def hloc(xpath: str) -> dict:
    return {"kind": "html_xpath", "xpath": xpath}


def comments_for(fid: str, people: list[str], n: int = 3) -> list[tuple[str, str, str]]:
    r = util.rng(f"{fid}:comments")
    on = fdate(fid)
    bank = ["Thanks – this matches what we agreed at the last review.",
            "Could we add a link to the related Jira epic?", "Updated the table after the squad sync.",
            "Is this still accurate after the last release? Please confirm.", "Looks good to me.",
            "I have raised a question with the owner; will update once answered.",
            "Added the missing contact details.", "Please keep the terminology aligned with the glossary page.",
            "The diagram export is attached to this page.", "Reviewed – no changes needed."]
    out = []
    for k in range(n):
        who = people[k % len(people)]
        when = minus_days(on, r.randint(0, 30))
        if W.employed(who, when):
            out.append((who, when, r.choice(bank)))
    return sorted(out, key=lambda x: x[1])


def related_links(fid: str) -> str:
    return ul([a(x) for x in PAGES if x != fid], raw=True, uid="related-pages")


# ---------------------------------------------------------------------------------------------
# ST053 Claims Hub Home
# ---------------------------------------------------------------------------------------------

def build_ST053(out_dir: pathlib.Path) -> Built:
    fid = "ST053"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:home")
    prog = W.timeline["programme"]
    body = []
    body.append(macro("information", p(f"Welcome to the Claims Hub space. Claims Hub ({sysname('SYS02', on)}) replaces "
                                       f"the CLARA mainframe claims system under Programme Skerry. " +
                                       phrases.sentence(r, "wiki"))))
    body.append(h(2, "Programme at a glance", "programme"))
    body.append(kv_table([
        ("Programme", "Programme Skerry – CLARA to Claims Hub"),
        ("Business case", "Signed 2024-11-18 by the then CFO, Gareth Whitcombe; budget £48.6m"),
        ("IBM engagement start", prog["ibm_engagement_start"]),
        ("MVP live", f"{prog['mvp']} (FNOL and triage, digital channels)"),
        ("Wave 0", f"{prog['wave0']} – Denmark ({status('done', 'success')})"),
        ("Wave 1", f"{prog['wave1']} – UK motor ({status('done', 'success')})"),
        ("Wave 2", f"{prog['wave2']} – UK home, commercial, liability; Norway; Sweden ({status('planned')})"),
        ("CLARA decommission target", prog["clara_decommission_target"]),
        ("Product owner", f"{e(pname('P017', on))}, {e(ptitle('P017', on))}"),
    ], tid="programme-facts"))
    body.append(macro("warning", p(f"Wave 2 change freeze: {W.waves['MW-2']['freeze']}. Production changes in that window need "
                                   "Steering Committee approval."), title="Wave 2 freeze"))
    # squads with nested tables
    body.append(h(2, "Squads and platform teams", "squads-heading"))
    body.append(p("Each squad owns its services end to end. The nested tables show when the squad was formed, who leads "
                  "it and which repositories it looks after."))
    rows, rids = [], []
    for tid in ["T27", "T28", "T29", "T30", "T22", "T21", "T20", "T31"]:
        t = W.teams[tid]
        if not team_exists(tid, on):
            continue
        lead = W.team_lead(tid, on)
        pairs = [("Formed", e(t.get("formed"))), ("Engineering lead" if tid in ("T27", "T28", "T29", "T30") else "Lead",
                                                   e(pname(lead, on)))]
        if t.get("github_team") and may(fid, f"TEAM:{tid}", "github_team"):
            pairs.append(("GitHub team", f"<code>{e(t['github_team'])}</code>"))
        pairs.append(("Purpose", e(t["purpose"])))
        pairs.append(("Department", e(W.departments[W.team_department(tid, on)]["name"])))
        nested = kv_table(pairs, tid=f"squad-{tid}", cls="confluenceTable nested")
        rows.append([f"<strong>{e(team_name(tid, on))}</strong>", nested])
        rids.append(f"squad-row-{tid}")
    body.append(table(["Squad / team", "Details"], rows, tid="squads", row_ids=rids))
    # services
    body.append(h(2, "Services", "services"))
    srows = []
    for sid, s in W.services_by_id.items():
        nm = svcname(sid, on)
        former = ", ".join(f"{rn['from_name']} (until {rn['date']})" for rn in s["renames"] if rn["date"] <= on)
        srows.append([f"<code>{e(nm)}</code>", e(s["description"]), e(s["k8s_namespace"]), e(s["status"]),
                      e(s["go_live"]), e(former or "–")])
    body.append(table(["Service", "Description", "Namespace", "Status", "Go-live", "Former name"], srows, tid="services-table"))
    body.append(p("Service-level design pages: " + a("ST058") + ". Interface pages: " + a("ST054") + ".", raw=True))
    # environments
    body.append(h(2, "Environments", "environments"))
    body.append(table(["Environment", "Cluster", "Purpose"], [
        ["dev", "ocp-dev-lon1", "Squad development and integration"],
        ["test", "ocp-test-lon1", "System and contract testing"],
        ["preprod", "ocp-pre-lon1", "Release rehearsal and performance testing"],
        ["prod", "ocp-prd-lon1", "Production (London)"],
        ["dr", "ocp-dr-lds1", "Disaster recovery (Leeds)"],
    ], tid="environments-table", raw=False))
    # decisions
    body.append(h(2, "Key decisions", "decisions"))
    drows = []
    for did, dd in sorted(W.decisions.items(), key=lambda x: x[1]["date"]):
        if dd["date"] > on or not may(fid, f"DECISION:{did}"):
            continue
        drows.append([e(did), e(dd["date"]), e(dd["statement"]), e(", ".join(pname(x, dd["date"]) for x in dd["decided_by"]))])
    body.append(table(["ID", "Date", "Decision", "Decided by"], drows, tid="decisions-table"))
    # incidents
    body.append(h(2, "Recent incidents", "incidents"))
    irows = []
    for iid, inc in sorted(W.incidents.items(), key=lambda x: x[1]["date"]):
        if inc["date"] > on or inc["date"] < "2025-01-01":
            continue
        st = inc.get("status") or "resolved"
        if iid == "INC-2026-0518":
            st = "mitigated"
        title = inc["title"] if may(fid, "SYSTEM:SYS01", "cics_regions") else inc["title"].replace("CICSPRD1", "online")
        irows.append([e(iid), e(inc["date"]), e(inc.get("severity", "")), e(title),
                      e(", ".join(sysname(s, on) for s in inc["systems"])), e(st)])
    body.append(table(["Incident", "Date", "Severity", "Title", "Systems", "Status"], irows, tid="incidents-table"))
    # ADRs
    body.append(h(2, "Architecture decision records", "adrs"))
    arows = []
    for aid, ad in W.adrs.items():
        if str(ad["date"]) > on:
            continue
        kind = {"accepted": "success", "superseded": "error", "deprecated": "error", "proposed": "current"}.get(ad["status"], "current")
        arows.append([e(aid), e(ad["date"]), status(ad["status"], kind), e(ad["title"])])
    body.append(table(["ADR", "Date", "Status", "Title"], arows, tid="adr-table"))
    # milestones
    body.append(h(2, "Programme timeline", "timeline"))
    mrows = []
    for ev in sorted(W.events.values(), key=lambda x: x["date"]):
        if ev["date"] > on or ev["date"] < "2024-01-01" or ev["kind"] == "document" or not may(fid, f"EVENT:{ev['id']}"):
            continue
        mrows.append([e(ev["date"]), e(ev["kind"]), e(ev["summary"])])
    body.append(table(["Date", "Type", "Milestone"], mrows, tid="timeline-table"))
    body.append(h(2, "Governance forums", "forums"))
    crows = []
    for cid, c in W.committees.items():
        chair = [x["person"] for x in c["chair_history"] if x["from"] <= on and (x["to"] is None or on <= x["to"])][0]
        cad = e(c["cadence"]) if may(fid, f"COMMITTEE:{cid}", "cadence") else "see the forum calendar"
        crows.append([e(c["name"]), e(pname(chair, on)), cad, e(c["remit"])])
    body.append(table(["Forum", "Chair", "Cadence", "Remit"], crows, tid="forums-table"))
    body.append(h(2, "System landscape", "landscape"))
    lrows = []
    for sid, sy in W.systems.items():
        own = system_owner(sid, on)
        lrows.append([e(sysname(sid, on)), e(sid), e(sy["type"]), e(sy["lifecycle"]), e(pname(own, on)),
                      e(sy.get("decommission_target") or "–")])
    body.append(table(["System", "ID", "Type", "Lifecycle", "Owner", "Decommission target"], lrows, tid="landscape-table"))
    # topics
    body.append(h(2, "Event topics", "topics"))
    trows = []
    for t in sorted(W.topics.values(), key=lambda x: x["name"]):
        if str(t.get("introduced") or "0000") > on or not may(fid, f"TOPIC:{t['name']}"):
            continue
        prod = svcname(t["producer"], on) if t["producer"] in W.services else t["producer"]
        cons = ", ".join(svcname(c, on) if c in W.services else c for c in t["consumers"])
        trows.append([f"<code>{e(t['name'])}</code>", e(prod), e(cons)])
    body.append(table(["Topic", "Producer", "Consumers"], trows, tid="topics-table"))
    body.append(h(2, "Migration waves", "waves"))
    wrows = []
    for wid, wv in W.waves.items():
        prods = ", ".join(W.products[x.strip()]["name"] for x in wv["scope"].split("(")[-1].rstrip(")").split(",")
                          if x.strip() in W.products) or wv["scope"]
        st_ = "complete" if wv["date"] <= on else "planned"
        wrows.append([e(wv["name"]), e(wv["date"]), e(prods), e(wv.get("freeze") or "–"),
                      status(st_, "success" if st_ == "complete" else "current")])
    body.append(table(["Wave", "Cut-over", "Products", "Change freeze", "Status"], wrows, tid="waves-table"))
    body.append(h(2, "Interfaces involving Claims Hub", "chub-interfaces"))
    body.append(p("Interfaces where Claims Hub is the source or target, or where a Claims Hub service does the work. "
                  "The nested tables show the upstream and downstream interfaces; the interface catalogue is the "
                  "reference for full detail."))
    irows2 = []
    for iid, it in W.interfaces.items():
        if str(it["since"]) > on or not ("SYS02" in (it["source_system"], it["target_system"]) or it["services"]):
            continue
        deps = [[e(d), e(W.interfaces[d]["name"]), "upstream"] for d in it["depends_on"]]
        deps += [[e(d), e(W.interfaces[d]["name"]), "downstream"] for d in it["dependents"]]
        nested = (table(["Interface", "Name", "Direction"], deps, tid=f"deps-{iid}", cls="confluenceTable nested")
                  if deps else "–")
        svc_ = ", ".join(svcname(x, on) for x in it["services"]) or "–"
        irows2.append([f"<strong>{e(iid)}</strong>", e(it["name"]),
                       e(f"{sysname(it['source_system'], on)} → {sysname(it['target_system'], on)}"), e(it["protocol"]),
                       f"<code>{e(svc_)}</code>", e(pname(it["owner"], on)), nested])
    body.append(table(["Interface", "Name", "Flow", "Protocol", "Service", "Owner", "Dependencies"], irows2,
                      tid="chub-interfaces-table"))
    body.append(h(2, "Recently completed work", "recent-work"))
    body.append(p("Tickets resolved in the last ten weeks. Release-level detail is on the " + a("ST060") + " page.", raw=True))
    trows2 = []
    for t in sorted(W.tickets.values(), key=lambda x: (str(x.get("resolved") or ""), x["id"]), reverse=True):
        res = str(t.get("resolved") or "")
        if not res or res > on or res < minus_days(on, 70) or t["status"] != "Done" or not may(fid, f"TICKET:{t['id']}"):
            continue
        trows2.append([e(t["id"]), e(t["type"]), e(t["summary"]), e(t.get("component") or "–"), e(res)])
    body.append(table(["Key", "Type", "Summary", "Component", "Resolved"], trows2, tid="recent-work-table"))
    body.append(h(2, "Getting started", "getting-started"))
    body.append(code("bash", "git clone git@github.com:corvane/claims-hub.git\ncd claims-hub/services/fnol-intake-svc\n"
                             "mvn -B verify\nmvn spring-boot:run -Dspring-boot.run.profiles=local"))
    body.append(p(phrases.paragraph(r, "wiki", 3)))
    body.append(h(2, "Space pages", "space-pages"))
    body.append(related_links(fid))
    content = render_page(fid, "\n".join(body), ["claims-hub", "home", "programme-skerry"],
                          comments_for(fid, ["P032", "P048", "P041"]),
                          attachments=["claims-hub-context-diagram.png", "wave-plan-2026.pdf"])
    F.add("needle", "Wiki home nested table: Squad Recoveries & Documents formed 2026-11-01, lead Tariq Hussain.",
          hloc("//table[@id='squad-T30']"), "Formed 2026-11-01 Engineering lead Tariq Hussain",
          world_ref="TEAM:T30", placement="PL-183")
    F.add("general", "Wiki home: Hub Squad – Reserve & Finance is led by Daniel Achebe.",
          hloc("//table[@id='squad-T28']"), "Engineering lead Daniel Achebe", world_ref="TEAM:T28")
    F.add("general", "Wiki home: Wave 2 (UK home, commercial, liability; Norway; Sweden) is planned for 2027-02-15.",
          hloc("//table[@id='programme-facts']"), "2027-02-15 – UK home, commercial, liability; Norway; Sweden",
          world_ref="WAVE:MW-2#date")
    F.add("general", "Wiki home: the business case was signed on 2024-11-18 by the then CFO Gareth Whitcombe, budget £48.6m.",
          hloc("//table[@id='programme-facts']"), "Signed 2024-11-18 by the then CFO, Gareth Whitcombe",
          world_ref="EVENT:EV-010")
    F.add("alias_use", "Wiki home services table: reserve-engine was called reserve-svc until 2026-02-10.",
          hloc("//table[@id='services-table']"), "reserve-svc (until 2026-02-10)", world_ref="SERVICE:reserve-engine#renames")
    F.add("general", "Decision DEC-011: Wave 2 cut-over confirmed as 2027-02-15 (earlier draft 2027-01-18 void).",
          hloc("//table[@id='decisions-table']"), "Wave 2 cut-over date confirmed as 2027-02-15", world_ref="DECISION:DEC-011")
    F.add("general", "Wiki home waves table: Wave 0 Denmark cut over on 2026-06-01 (complete).",
          hloc("//table[@id='waves-table']//tr[2]"), "Wave 0 – Denmark 2026-06-01", world_ref="WAVE:MW-0#date")
    return Built(fid, content, F.items, f"{len(rows) + len(srows) + len(drows) + len(irows) + len(arows) + len(trows)} rows")


# ---------------------------------------------------------------------------------------------
# ST054 CLX-IF-042 page
# ---------------------------------------------------------------------------------------------

def build_ST054(out_dir: pathlib.Path) -> Built:
    fid = "ST054"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:if042")
    i = W.interfaces["CLX-IF-042"]
    ref = "INTERFACE:CLX-IF-042"
    assert not may(fid, ref, "schedule") and not may(fid, ref, "mq_max_depth")
    body = []
    body.append(p(f"{status('live', 'success')} {status('critical', 'error')} This page describes interface CLX-IF-042, "
                  "the daily extract of CLARA reserve movements to the MQ Backbone.", raw=True))
    body.append(h(2, "Summary", "summary"))
    body.append(kv_table([
        ("Interface ID", "CLX-IF-042"), ("Name", e(i["name"])),
        ("Source", f"{e(sysname(i['source_system'], on))} ({i['source_system']})"),
        ("Target", f"{e(sysname(i['target_system'], on))} ({i['target_system']})"),
        ("Protocol", e(i["protocol"])), ("Format", e(i["format"])),
        ("Program", "<code>CLRRS170</code> – " + e(W.programs["CLRRS170"]["description"])),
        ("Batch job", "<code>CLRNRSV3</code> (Batch Scheduler); timing is held in the scheduler calendar"),
        ("Output dataset", f"<code>{e(i['dataset'])}</code>"),
        ("Queue", f"<code>{e(i['mq_queue'])}</code> on queue manager CLRQM01"),
        ("Record layout", "Copybook <code>RSVMOVE</code>"),
        ("Source table", "<code>CLR.T_RESERVE_MOVEMENT</code>"),
        ("Owner", f"{e(pname(i['owner'], on))}, {e(ptitle(i['owner'], on))}"),
        ("Criticality", e(i["criticality"])), ("In service since", e(i["since"])),
        ("Typical volume", e(i["avg_daily_volume"])),
        ("Upstream", "CLX-IF-027 " + e(W.interfaces["CLX-IF-027"]["name"])),
    ], tid="if-properties"))
    body.append(macro("information", p("RSVMOVE carries a record version byte (RM-REC-VERSION, value 02) since 2025-04-30 "
                                       "(CHUB-142). Consumers validate it before processing."), title="Record version"))
    body.append(macro("warning", p("Any change to the RSVMOVE layout or to the extract needs signed impact assessments "
                                   "from every downstream consumer (CHUB-144). The unannounced widening of RM-AMOUNT under "
                                   "CHUB-138 broke the GL reserve journals in INC-2025-0412."), title="Change control"))
    # related systems box
    rel = [f"{e(sysname('SYS03', on))} (fraud scoring, CLX-IF-008)",
           f"{e(sysname('SYS14', on))} (queue manager CLRQM01)",
           f"{e(sysname('SYS15', on))} (Kafka bridge target, CLX-IF-049)",
           f"{e(sysname('SYS06', on))} (GL reserve journals, CLX-IF-043)",
           f"{e(sysname('SYS11', on))} (reserve fact load, CLX-IF-044)",
           f"{e(sysname('SYS07', on))} (cession feed, CLX-IF-047)",
           f"{e(sysname('SYS10', on))} (NISA-TP2 via CLX-IF-051)",
           f"{e(sysname('SYS21', on))} (triangles, CLX-IF-058)",
           f"{e(sysname('SYS26', on))} (bordereaux, CLX-IF-055)"]
    body.append('<div class="panel related-systems" id="related-systems"><div class="panelHeader"><b>Related systems '
                '(CLARA reserve estate)</b></div><div class="panelContent">' + ul(rel, raw=True) + "</div></div>")
    # consumers with nested downstream table
    body.append(h(2, "Consumers", "consumers"))
    drows = []
    for d in i["dependents"]:
        x = W.interfaces[d]
        drows.append([f"<strong>{e(d)}</strong>", e(x["name"]), e(sysname(x["target_system"], on)),
                      e(W.interface_schedule(d, on)), e(pname(x["owner"], on)),
                      e(", ".join(team_name(t, on) for t in x["consumer_teams"]))])
    downstream = table(["Interface", "Name", "Target", "Schedule", "Owner", "Consumer team"], drows,
                       tid="downstream", cls="confluenceTable nested")
    imp = W.impact("CLX-IF-042")
    h2rows = []
    for d in imp["hops"].get(2, []):
        x = W.interfaces[d]
        h2rows.append([f"<strong>{e(d)}</strong>", e(x["name"]), e(f"depends on {', '.join(x['depends_on'])}"),
                       e(sysname(x["target_system"], on)), e(", ".join(x["feeds_reports"]) or "–")])
    hop2 = table(["Interface", "Name", "Dependency", "Target", "Reports"], h2rows, tid="second-hop",
                 cls="confluenceTable nested")
    body.append(table(["Level", "Interfaces"], [["Downstream (hop 1)", downstream], ["Second hop", hop2],
                                                ["Reports affected", e(", ".join(imp["reports"]))],
                                                ["Consumer teams", e(", ".join(team_name(t, on) for t in imp["teams"]))]],
                      tid="consumers-table"))
    body.append(p("The second hop feeds the NISA-TP2 return and the Reserving team's monthly IBNR run (through CLX-IF-058)."))
    # layout
    body.append(h(2, "Record layout (RSVMOVE)", "layout"))
    lay = cobol_layout(W.copybooks["RSVMOVE"]["fields"])
    lrows = [[e(f"{x['level']:02d}"), f"<code>{e(x['name'])}</code>", e(x["pic"] or "group"), e(x["offset"]), e(x["length"])]
             for x in lay]
    body.append(table(["Level", "Field", "PIC", "Offset", "Length"], lrows, tid="rsvmove-layout"))
    body.append(h(2, "Extract logic", "extract-logic"))
    body.append(code("sql", "SELECT MOVE_ID, RSV_ID, CLAIM_ID, MOVE_TS, MOVE_TYPE_CD, MOVE_AMT, MOVE_GBP_AMT\n"
                            "  FROM CLR.T_RESERVE_MOVEMENT\n WHERE EXTRACTED_FLAG = 'N'\n ORDER BY CLAIM_ID, MOVE_ID;\n"
                            "-- after a successful MQPUT of each record:\nUPDATE CLR.T_RESERVE_MOVEMENT\n"
                            "   SET EXTRACTED_FLAG = 'Y', EXTRACT_RUN_ID = :WS-RUN-ID\n WHERE MOVE_ID = :WS-MOVE-ID;",
                     cid="extract-sql"))
    body.append(p("Restart: rerun the whole job; CLRRS170 only extracts rows with EXTRACTED_FLAG = 'N', so a rerun does not "
                  "resend records that were already put to the queue."))
    body.append(h(2, "Sample record", "sample"))
    body.append(code("text", "RM-REC-TYPE=RM RM-REC-VERSION=02 RM-EXTRACT-DATE=2026-08-31 RM-CLAIM-ID=(claim key)\n"
                             "RM-MOVE-TYPE=AD RM-CURRENCY=GBP RM-AMOUNT=+000012500.00 RM-GBP-AMOUNT=+000012500.00\n"
                             "RM-PRODUCT=MOTUK RM-PERIL=COL RM-TIER=2 (synthetic values; packed fields shown unpacked)",
                     cid="sample-record"))
    body.append(h(2, "Downstream detail", "downstream-detail"))
    for d in i["dependents"] + ["CLX-IF-027"]:
        x = W.interfaces[d]
        body.append(h(3, f"{d} {x['name']}" + (" (upstream)" if d == "CLX-IF-027" else ""), f"detail-{d}"))
        body.append(kv_table([("Source", e(sysname(x["source_system"], on))), ("Target", e(sysname(x["target_system"], on))),
                              ("Protocol", e(x["protocol"])), ("Format", e(x["format"])),
                              ("Schedule", e(W.interface_schedule(d, on))), ("Owner", e(pname(x["owner"], on))),
                              ("Criticality", e(x["criticality"])),
                              ("Feeds", e(", ".join(x["dependents"]) or "–"))], tid=f"detail-table-{d}"))
    body.append(h(2, "Source table columns (CLR.T_RESERVE_MOVEMENT)", "source-columns"))
    body.append(table(["Column", "Type", "Nullable", "Description"],
                      [[f"<code>{e(c['name'])}</code>", e(c["type"]), e("yes" if c["nullable"] else "no"), e(c["description"])]
                       for c in W.tables["CLR.T_RESERVE_MOVEMENT"]["columns"]], tid="source-columns-table"))
    body.append(h(2, "Mapping to the Kafka bridge (CLX-IF-049)", "bridge-mapping"))
    body.append(table(["RSVMOVE field", "Avro field (claims.reserve.movement.v1)", "Rule"], [
        ["RM-CLAIM-ID", "claim_id", "message key"], ["RM-MOVE-ID", "movement_id", "idempotency key"],
        ["RM-MOVE-TYPE", "movement_type", "IN, AD, IX, RV, ST, RC"], ["RM-CURRENCY", "currency", "ISO 4217"],
        ["RM-AMOUNT", "amount_minor", "x 100, sign kept (minor units)"], ["RM-GBP-AMOUNT", "gbp_amount_minor", "x 100"],
        ["RM-REC-VERSION", "record_version", "must be 02"]], tid="bridge-mapping-table", raw=False))
    body.append(h(2, "Monitoring", "monitoring"))
    body.append(ul(["Queue depth on CLR.RSVMOVE.OUT is alerted as a share of the queue's maximum depth.",
                    "Consumer lag on claims.reserve.movement.v1 is alerted for reserve-engine (see INC-2026-0311).",
                    "A missing extract dataset is reported by the Batch Scheduler as a late job.",
                    phrases.sentence(r, "interface_ops", "CLX-IF-042")]))
    body.append(h(2, "FAQ", "faq"))
    body.append("<dl id=\"faq\">" + "".join(f"<dt>{e(q)}</dt><dd>{e(a_)}</dd>" for q, a_ in [
        ("Can I rerun the extract?", "Yes. The extract only picks up rows with EXTRACTED_FLAG = 'N', so a rerun does not resend records."),
        ("Who must approve a layout change?", "Every downstream consumer: GL (CLX-IF-043), CDW (CLX-IF-044), ReCede (CLX-IF-047) and the Kafka bridge (CLX-IF-049)."),
        ("Which return depends on this interface?", "NISA-TP2, through CLX-IF-043 and CLX-IF-051."),
        ("Where is the record layout kept?", "Copybook RSVMOVE in the CLARA source baseline."),
    ]) + "</dl>")
    body.append(h(2, "Change history", "change-history"))
    crow = []
    for tk in ["CHUB-138", "CHUB-142", "CHUB-143", "CHUB-144", "CHUB-188"]:
        t = W.tickets[tk]
        crow.append([e(tk), e(t.get("resolved") or t["created"]), e(t["summary"]), e(pname(t["assignee"], on))])
    body.append(table(["Ticket", "Date", "Change", "By"], crow, tid="change-table"))
    body.append(h(2, "Operations", "operations"))
    body.append(p(phrases.paragraph(r, "interface_ops", 4, "CLX-IF-042")))
    body.append(p(phrases.paragraph(r, "error_handling", 3)))
    body.append(h(2, "Other CLARA outbound interfaces", "clara-outbound"))
    body.append(p("For context, the other interfaces that leave CLARA. Each has its own page in the Interfaces section "
                  "and its own entry in the interface catalogue."))
    orows = []
    for oid, ox in W.interfaces.items():
        if ox["source_system"] != "SYS01" or oid == "CLX-IF-042" or str(ox["since"]) > on:
            continue
        orows.append([e(oid), e(ox["name"]), e(f"{sysname(ox['target_system'], on)} ({ox['target_system']})"),
                      e(ox["protocol"]), e(ox["criticality"]), e(pname(ox["owner"], on))])
    body.append(table(["Interface", "Name", "Target", "Protocol", "Criticality", "Owner"], orows, tid="clara-outbound-table"))
    body.append(h(2, "Impact assessment checklist", "impact-checklist"))
    body.append("<ol id=\"impact-checklist-list\">" + "".join(f"<li>{e(x)}</li>" for x in r.sample(phrases.BANKS["impact_checklist"], 7)) + "</ol>")
    body.append(h(2, "When the extract fails", "failure-runbook"))
    body.append("<ol id=\"failure-steps\">" + "".join(f"<li>{e(x)}</li>" for x in r.sample(phrases.BANKS["runbook_if"], 6)) + "</ol>")
    body.append(macro("note", p("Batch timings for CLARA jobs are maintained in the Batch Scheduler calendar and are not "
                                "copied to wiki pages, so that there is a single source."), title="Timings"))
    body.append(h(2, "Contacts", "contacts"))
    body.append(table(["Role", "Name", "Email"], [
        ["Interface owner", e(pname("P031", on)), e(pemail("P031", on))],
        ["CLARA platform", e(pname("P016", on)), e(pemail("P016", on))],
        ["Batch operations", e(pname("P026", on)), e(pemail("P026", on))],
        ["GL adapter (CLX-IF-043)", e(pname("P021", on)), e(pemail("P021", on))],
        ["CDW load (CLX-IF-044)", e(pname("P036", on)), e(pemail("P036", on))],
        ["Cession feed (CLX-IF-047)", e(pname("P038", on)), e(pemail("P038", on))],
    ], tid="contacts-table"))
    body.append(h(2, "Related pages", "related"))
    body.append(related_links(fid))
    content = render_page(fid, "\n".join(body), ["interface", "clx-if-042", "reserve", "clara"],
                          comments_for(fid, ["P021", "P050", "P036"]), attachments=["RSVMOVE-layout-v02.pdf"])
    F.add("needle", "Wiki CLX-IF-042 page: nested 'Downstream' table lists CLX-IF-043, CLX-IF-044, CLX-IF-047, CLX-IF-049.",
          hloc("//table[@id='downstream']//td[1]"), "CLX-IF-043 CLX-IF-044 CLX-IF-047 CLX-IF-049",
          world_ref="INTERFACE:CLX-IF-042#dependents", placement="PL-184")
    F.add("contradiction_new", "The wiki calls the fraud engine 'Sentinel' throughout.",
          hloc("//div[@id='related-systems']"), "Sentinel (fraud scoring, CLX-IF-008)", world_ref="SYSTEM:SYS03#name",
          placement="PL-185", notes="C06: LD025 (2024-11-04) calls the same system FRAUDNET.")
    F.add("general", "CLX-IF-042 second hop: CLX-IF-051, CLX-IF-055 and CLX-IF-058.",
          hloc("//table[@id='second-hop']//td[1]"), "CLX-IF-051 CLX-IF-055 CLX-IF-058", world_ref="INTERFACE:CLX-IF-042#dependents")
    F.add("general", "CLX-IF-042 downstream schedules: CLX-IF-043 daily 03:45, CLX-IF-044 daily 04:00, CLX-IF-047 daily 04:15, CLX-IF-049 daily 02:45.",
          hloc("//table[@id='downstream']//tr[td[1]/strong='CLX-IF-043']"), "daily 03:45",
          world_ref="INTERFACE:CLX-IF-043#schedule")
    F.add("general", "CLX-IF-042 is written by program CLRRS170 in batch job CLRNRSV3, from CLR.T_RESERVE_MOVEMENT.",
          hloc("//table[@id='if-properties']"), "CLRNRSV3", world_ref="INTERFACE:CLX-IF-042#jcl_job")
    F.add("general", "CLX-IF-042 restart: rerun the whole job; only EXTRACTED_FLAG = 'N' rows are extracted.",
          hloc("//div[@id='main-content']/p[contains(., 'Restart')]"), "only extracts rows with EXTRACTED_FLAG = 'N'",
          world_ref="JCL:CLRNRSV3#restart")
    F.add("general", "RSVMOVE RM-AMOUNT is PIC S9(9)V99 COMP-3 (6 bytes).",
          hloc("//table[@id='rsvmove-layout']//tr[td[2]/code='RM-AMOUNT']"), "RM-AMOUNT S9(9)V99 COMP-3",
          world_ref="COPYBOOK:RSVMOVE#fields")
    F.add("general", "Wiki CLX-IF-042 page: CLARA outbound interface CLX-IF-008 targets Sentinel (SYS03).",
          hloc("//table[@id='clara-outbound-table']//tr[td[1]='CLX-IF-008']"), "Sentinel (SYS03)",
          world_ref="SYSTEM:SYS03#name", notes="Second use of the current name on the page (C06 side B).")
    return Built(fid, content, F.items, f"{len(lrows) + len(drows) + len(h2rows)} rows")


# ---------------------------------------------------------------------------------------------
# ST055 Glossary
# ---------------------------------------------------------------------------------------------

FAMILY_LABEL = {"LD": "manuals and long documents", "VS": "slides and diagrams", "ST": "data and specifications",
                "TX": "emails, transcripts and tickets", "CODE": "code and schemas"}
ABBREV = [("ADR", "Architecture decision record"), ("ARW", "Actuarial Reserving Workbench"),
          ("BI", "Bodily injury"), ("CDW", "Claims Data Warehouse"), ("CHUB", "Claims Hub (Jira project key)"),
          ("CIS", "Corvane Identity Service"), ("CLR", "CLARA schema and program prefix"),
          ("CPG", "Corvane Payments Gateway"), ("EIG", "Evidence Intake Gateway"), ("ESP", "Event Streaming Platform"),
          ("EOW", "Escape of Water"), ("FNOL", "First Notice of Loss"), ("FR1", "NISA quarterly fraud referral return"),
          ("IBNR", "Incurred but not reported"), ("LLNT", "Large Loss Notification Threshold"),
          ("NISA", "National Insurance Supervisory Authority"), ("NRH", "NISA Reporting Hub"),
          ("RI", "Reinsurance"), ("SCM", "SIU Case Manager"), ("SIU", "Special Investigations Unit (Counter-Fraud & SIU)"),
          ("TP2", "NISA quarterly technical provisions return"), ("CT1", "NISA annual claims timeliness return")]


def build_ST055(out_dir: pathlib.Path) -> Built:
    fid = "ST055"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:glossary")
    body = [macro("information", p("Use the canonical term in specifications and data models. The 'Also called' column "
                                   "lists the variants you will meet in manuals, slides, emails and code. "
                                   + phrases.sentence(r, "wiki"))),
            h(2, "Business terms", "business-terms")]
    rows, rids = [], []
    for gid, g in W.glossary.items():
        variants = " / ".join(v["term"] for v in g["variants"])
        nested_rows = [[e(v["term"]), e(", ".join(FAMILY_LABEL.get(f, f) for f in v["families"])), e(v.get("note") or "–")]
                       for v in g["variants"]]
        nested = table(["Variant", "Where you will see it", "Note"], nested_rows, tid=f"usage-{gid}", cls="confluenceTable nested")
        refs = ", ".join(g.get("refs") or [])
        rows.append([f"<strong>{e(g['canonical'])}</strong>", e(g["definition"]), e(variants), nested, e(refs or "–")])
        rids.append(f"gl-{gid}")
    body.append(table(["Term", "Definition", "Also called", "Usage by document type", "Related"], rows, tid="glossary",
                      row_ids=rids))
    body.append(h(2, "System names", "system-names"))
    srows = []
    for sid, s in W.systems.items():
        former = ", ".join(f"{rn['from_name']} (renamed {rn['date']})" for rn in s.get("renames", []) if rn["date"] <= on)
        srows.append([e(sysname(sid, on)), e(sid), e(", ".join(s.get("aliases", [])[:4])), e(former or "–"), e(s["type"])])
    body.append(table(["Current name", "ID", "Aliases", "Former name", "Type"], srows, tid="system-names-table"))
    body.append(h(2, "Service names", "service-names"))
    vrows = []
    for sid, s in W.services_by_id.items():
        former = ", ".join(f"{rn['from_name']} (renamed {rn['date']}, {rn['adr']})" for rn in s["renames"] if rn["date"] <= on)
        vrows.append([f"<code>{e(svcname(sid, on))}</code>", e(", ".join(s["aliases"])), e(former or "–")])
    body.append(table(["Service", "Aliases", "Former name"], vrows, tid="service-names-table"))
    body.append(h(2, "Abbreviations", "abbreviations"))
    body.append(table(["Abbreviation", "Meaning"], [[e(x), e(y)] for x, y in ABBREV], tid="abbreviations"))
    body.append(h(2, "Nordic terms", "nordic"))
    body.append(table(["Term", "Language", "Meaning"], [
        ["egenandel", "Norwegian", "Excess"], ["självrisk", "Swedish", "Excess"], ["selvrisiko", "Danish", "Excess"],
        ["skadetakstmann", "Norwegian", "Claims Assessor"], ["skademelding", "Norwegian", "First Notice of Loss"],
        ["regress / regressfordring", "Nordic", "Subrogation (recovery from a third party)"],
        ["takst", "Norwegian / Danish", "Assessment"]], tid="nordic-terms", raw=False))
    body.append(p(phrases.paragraph(r, "governance", 2)))
    body.append(h(2, "Related pages", "related"))
    body.append(related_links(fid))
    content = render_page(fid, "\n".join(body), ["glossary", "terminology"], comments_for(fid, ["P054", "P017", "P011"]))
    F.add("terminology", "Wiki glossary: 'loss adjuster / adjuster / assessor' → Claims Assessor.",
          hloc("//tr[@id='gl-G-001']"), "loss adjuster / adjuster / assessor", world_ref="GLOSSARY:G-001",
          placement="PL-186")
    F.add("terminology", "Wiki glossary: canonical term Claims Assessor (internal employee or panel vendor who inspects or desk-assesses a loss).",
          hloc("//tr[@id='gl-G-001']/td[1]"), "Claims Assessor", world_ref="GLOSSARY:G-001")
    F.add("terminology", "Wiki glossary: 'case handler' (older manual v6.1) means Claims Handler.",
          hloc("//table[@id='usage-G-007']"), "case handler", world_ref="GLOSSARY:G-007")
    F.add("alias_use", "Wiki glossary: Sentinel was formerly FRAUDNET (renamed 2025-03-01).",
          hloc("//table[@id='system-names-table']"), "FRAUDNET (renamed 2025-03-01)", world_ref="SYSTEM:SYS03#renames")
    F.add("terminology", "Wiki glossary: LLNT is the Large Loss Notification Threshold (£250,000, BR-RSV-011 v2).",
          hloc("//tr[@id='gl-G-015']"), "LLNT", world_ref="GLOSSARY:G-015")
    return Built(fid, content, F.items, f"{len(rows) + len(srows) + len(vrows)} rows")


# ---------------------------------------------------------------------------------------------
# ST056 CLARA batch runbook
# ---------------------------------------------------------------------------------------------

ABENDS = [("S0C7", "Data exception – non-numeric data in a packed or zoned field.",
           "Identify the failing key from the dump, hand the record to development; do not patch data in place."),
          ("S0C4", "Protection exception – invalid storage reference.", "Collect the dump and escalate to the on-call developer."),
          ("S322", "CPU time limit exceeded.", "Check for unusual volumes before rerunning; escalate if it repeats."),
          ("S806", "Load module not found.", "Check the load library concatenation and the last promotion."),
          ("SB37 / SD37", "Dataset out of space.", "Allocate more space through the storage team, then restart the step."),
          ("SQLCODE -911", "DB2 deadlock or timeout.", "Rerun the step once; if it fails again, check for long-running units of work."),
          ("SQLCODE -805", "DBRM or package not found.", "Check the last bind for the program and escalate to the DBA.")]


def build_ST056(out_dir: pathlib.Path) -> Built:
    fid = "ST056"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:runbook")
    body = [macro("warning", p("Never rerun a CLARA batch job without checking the restart instruction below. When in "
                               "doubt, phone the CLARA on-call developer first."), title="Before you restart anything"),
            h(2, "Batch overview", "overview"),
            kv_table([("Batch window", e(W.systems["SYS01"]["batch_window"])),
                      ("Scheduler", f"{e(sysname('SYS18', on))} (SYS18)"),
                      ("Operations team", e(team_name("T25", on))),
                      ("Batch Operations Lead", e(pname("P026", on))),
                      ("Platform owner", f"{e(pname('P016', on))}, {e(ptitle('P016', on))}"),
                      ("Queue manager", "CLRQM01")], tid="batch-overview")]
    body.append(h(2, "Escalation", "escalation"))
    body.append(table(["Order", "Who", "Role", "Email", "Phone"], [
        [str(k), e(pname(x, on)), e(ptitle(x, on)), e(pemail(x, on)), e(W.people[x]["phone"])]
        for k, x in enumerate(["P026", "P023", "P025", "P016", "P031"], 1)], tid="escalation-table"))
    body.append(h(2, "Job catalogue", "jobs"))
    jrows, jids = [], []
    for name, j in W.jcl_jobs.items():
        ref = f"JCL:{name}"
        desc = j["description"]
        stt = j["status"]
        if name == "CLRDRSV9" and on < "2026-08-28":
            desc, stt = "Reserve parallel-run reconciliation", "active"
        sched = e(j["schedule"]) if may(fid, ref, "schedule") else "set in the scheduler calendar"
        steps = table(["Step", "Program", "What it does"],
                      [[e(s["step"]), f"<code>{e(s['program'])}</code>", e(s["description"])] for s in j["steps"]],
                      tid=f"steps-{name}", cls="confluenceTable nested")
        if j["restart"] and may(fid, ref, "restart"):
            rst = e(j["restart"])
        elif j["restart"]:
            rst = "Call the CLARA on-call developer before any rerun."
        else:
            rst = "Standard: fix the cause, then rerun from the failed step."
        jrows.append([f"<strong>{e(name)}</strong>", e(desc), sched, steps, rst, status(stt, "success" if stt == "active" else "error")])
        jids.append(f"job-{name}")
    body.append(table(["Job", "Description", "Schedule", "Steps", "Restart", "Status"], jrows, tid="job-catalogue", row_ids=jids))
    body.append(macro("note", p("Job CLRNFR99 (auto-decline sweep, program CLRFR140) was taken out of the schedule on "
                                "2026-04-01 under CHUB-207. Do not reinstate it."), title="Removed job"))
    body.append(macro("information", p("Job CLRDRSV9 runs the reserve parallel-run reconciliation against reserve-engine "
                                       "from 2026-03-02 to 2026-08-28 (CHUB-241)."), title="Parallel run"))
    body.append(h(2, "Interfaces produced by batch", "batch-interfaces"))
    birows = []
    for name, j in W.jcl_jobs.items():
        for st in j["steps"]:
            for i in W.interfaces.values():
                if st["program"] in i["programs"]:
                    birows.append([e(name), e(st["program"]), e(i["id"]), e(i["name"]), e(sysname(i["target_system"], on))])
    body.append(table(["Job", "Program", "Interface", "Name", "Target"], birows, tid="batch-interfaces-table"))
    body.append(h(2, "Common abends", "abends"))
    body.append(table(["Code", "Meaning", "Action"], [[e(x), e(y), e(z)] for x, y, z in ABENDS], tid="abend-table"))
    body.append(h(2, "Lessons from incidents", "lessons"))
    lrows = []
    for iid in ["INC-2024-0243", "INC-2025-0677", "INC-2026-0104", "INC-2026-0518"]:
        inc = W.incidents[iid]
        if inc["date"] > on:
            continue
        st = "mitigated" if iid == "INC-2026-0518" else "resolved"
        lrows.append([e(iid), e(inc["date"]), e(inc["title"]), e(inc["root_cause"]), e(st)])
    body.append(table(["Incident", "Date", "What happened", "Root cause", "Status"], lrows, tid="lessons-table"))
    body.append(h(2, "Useful commands", "commands"))
    body.append(code("text", "/* display the status of a job in the scheduler */\nBSCH DISPLAY JOB(CLRNRSV2)\n"
                             "/* hold and release a job */\nBSCH HOLD JOB(CLRNRC01)\nBSCH RELEASE JOB(CLRNRC01)\n"
                             "/* display queue depth */\nDISPLAY QLOCAL('CLR.RSVMOVE.OUT') CURDEPTH",
                     cid="commands-block"))
    body.append(h(2, "Shift checklist", "checklist"))
    body.append(ul(r.sample(phrases.BANKS["runbook"], 8)))
    body.append(h(2, "Related pages", "related"))
    body.append(related_links(fid))
    content = render_page(fid, "\n".join(body), ["clara", "batch", "runbook", "operations"],
                          comments_for(fid, ["P026", "P023", "P016"]))
    F.add("general", "CLARA batch runbook: job CLRNRSV3 extracts reserve movements for CLX-IF-042 with CLRRS170; restart by rerunning the whole job.",
          hloc("//tr[@id='job-CLRNRSV3']"), "Rerun the whole job", world_ref="JCL:CLRNRSV3#restart",
          notes="Schedule withheld (guarded by CLX-IF-042 schedule).")
    F.add("general", "CLARA batch runbook: job CLRNTR01 (nightly triage) runs daily at 23:45.",
          hloc("//tr[@id='job-CLRNTR01']"), "daily 23:45", world_ref="JCL:CLRNTR01#schedule")
    F.add("general", "CLARA batch runbook: CLRYGL90 rerun allowed because revaluation is idempotent for the same rate date.",
          hloc("//tr[@id='job-CLRYGL90']"), "revaluation is idempotent for the same rate date", world_ref="JCL:CLRYGL90#restart")
    F.add("general", "CLARA batch runbook: INC-2026-0104 – CLRYGL90 abended with S0C7 on a malformed SEK year-end rate.",
          hloc("//table[@id='lessons-table']"), "Malformed SEK year-end rate", world_ref="INCIDENT:INC-2026-0104")
    F.add("general", "CLARA batch runbook: escalation starts with Sunita Vaghela, Batch Operations Lead.",
          hloc("//table[@id='escalation-table']"), "Sunita Vaghela", world_ref="PERSON:P026")
    return Built(fid, content, F.items, f"{len(jrows) + len(lrows)} rows")


# ---------------------------------------------------------------------------------------------
# ST057 Team directory
# ---------------------------------------------------------------------------------------------

def build_ST057(out_dir: pathlib.Path) -> Built:
    fid = "ST057"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:directory")
    body = [macro("information", p("Two colleagues share the name Callum Fairbairn: one in Corvane Motor Claims (Leeds) and "
                                   "one in the IBM Programme Skerry team (London). Check the organisation and location "
                                   "columns before you email."), title="Namesakes")]
    body.append(h(2, "People", "people"))
    rows, rids = [], []
    internal = [pid for pid, x in W.people.items() if x["employer"] in ("ORG-CORVANE", "ORG-IBM") and W.employed(pid, on)]
    internal.sort(key=lambda x: (W.people[x]["name"].split()[-1], x))
    for pid in internal:
        x = W.people[pid]
        org = "Corvane Mutual" if x["employer"] == "ORG-CORVANE" else "IBM Consulting"
        tm = W.team_of(pid, on)
        mgr = W.manager_of(pid, on)
        rows.append([f"<strong>{e(pname(pid, on))}</strong>", e(ptitle(pid, on)), e(org), e(team_name(tm, on) if tm else "–"),
                     e(pcity(pid, on)), e(pname(mgr, on) if mgr else "–"), e(pemail(pid, on)), e(x["phone"])])
        rids.append(f"dir-{pid}")
    body.append(table(["Name", "Title", "Organisation", "Team", "Location", "Manager", "Email", "Phone"], rows,
                      tid="staff-directory", row_ids=rids))
    body.append(h(2, "Teams", "teams"))
    trows, tids = [], []
    for tid, t in W.teams.items():
        if not team_exists(tid, on):
            continue
        members = [pid for pid in internal if W.team_of(pid, on) == tid]
        lead = W.team_lead(tid, on)
        mem = table(["Member", "Title"], [[e(pname(m, on)), e(ptitle(m, on))] for m in members] or [["–", "–"]],
                    tid=f"members-{tid}", cls="confluenceTable nested")
        trows.append([f"<strong>{e(team_name(tid, on))}</strong>", e(W.departments[W.team_department(tid, on)]["name"]),
                      e(pname(lead, on) if lead else "–"), e(t["purpose"]), mem])
        tids.append(f"team-{tid}")
    body.append(table(["Team", "Department", "Lead", "Purpose", "Members"], trows, tid="teams-table", row_ids=tids))
    body.append(h(2, "External contacts", "external"))
    erows = []
    for pid, x in W.people.items():
        if x["employer"] in ("ORG-CORVANE", "ORG-IBM"):
            continue
        org = W.regulators[x["employer"]]["name"] if x["employer"] in W.regulators else W.vendors[x["employer"]]["name"]
        erows.append([e(pname(pid, on)), e(ptitle(pid, on)), e(org), e(pemail(pid, on)), e(x["phone"])])
    body.append(table(["Name", "Title", "Organisation", "Email", "Phone"], erows, tid="external-contacts"))
    body.append(p(phrases.sentence(r, "wiki") + " Changes to this page follow the joiners/movers/leavers process."))
    body.append(h(2, "Related pages", "related"))
    body.append(related_links(fid))
    content = render_page(fid, "\n".join(body), ["directory", "people", "contacts"], comments_for(fid, ["P032", "P048"]))
    F.add("alias_use", "Team directory has two Callum Fairbairn entries: Corvane (Leeds, Motor Claims Team Leader) and IBM (London, Data Migration Lead).",
          hloc("//tr[@id='dir-P022']"), "Callum Fairbairn Motor Claims Team Leader Corvane Mutual",
          world_ref="PERSON:P022", placement="PL-187", also_in=[])
    F.add("alias_use", "Team directory: the IBM Callum Fairbairn is Data Migration Lead in London.",
          hloc("//tr[@id='dir-P051']"), "Callum Fairbairn Data Migration Lead IBM Consulting", world_ref="PERSON:P051")
    F.add("general", "Team directory: Ingrid Ashby is the Claims Director.", hloc("//tr[@id='dir-P005']"),
          "Ingrid Ashby Claims Director", world_ref="PERSON:P005#name_history")
    F.add("general", "Team directory: Tariq Hussain is Engineering Lead – Recoveries & Documents Squad.",
          hloc("//tr[@id='dir-P043']"), "Engineering Lead – Recoveries & Documents Squad", world_ref="PERSON:P043")
    F.add("general", "Team directory: Freya Lindahl (Head of Recoveries & Subrogation) is based in Stockholm.",
          hloc("//tr[@id='dir-P013']"), "Head of Recoveries & Subrogation", world_ref="PERSON:P013")
    F.add("general", "Team directory: Niall Brannigan reports to Karin Holmberg (CRO).", hloc("//tr[@id='dir-P008']"),
          "Karin Holmberg", world_ref="PERSON:P008#reports_to")
    return Built(fid, content, F.items, f"{len(rows) + len(trows) + len(erows)} rows")


# ---------------------------------------------------------------------------------------------
# ST058 reserve-engine design
# ---------------------------------------------------------------------------------------------

def build_ST058(out_dir: pathlib.Path) -> Built:
    fid = "ST058"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:design")
    s = W.services["reserve-engine"]
    name = svcname("reserve-engine", on)
    assert name == "reserve-engine"
    t3 = [h_["value"] for h_ in s["config"]["config_history"] if h_["key"] == "tier3-review-days" and h_["to"] > on][0]
    rv7 = W.rule_version("BR-RSV-007", on)
    assert rv7["parameters"]["review_days"] == t3
    body = [p(f"{status('approved', 'success')} Design of <code>{name}</code>, the Claims Hub service for case reserves "
              "and reserve movements.", raw=True),
            macro("information", p("reserve-svc was renamed reserve-engine on 2026-02-10 (CHUB-233, ADR-019). The "
                                   "repository path, namespace labels and Terraform module moved with the rename; "
                                   "the namespace stays chub-reserve. Event topic reserve.changed.v1 was retired and "
                                   "replaced by reserve.changed.v2."), title="Rename")]
    body.append(h(2, "Responsibilities", "responsibilities"))
    body.append(ul([s["description"], "Authority checks on reserve movements (BR-RSV-003 v3)",
                    "Large loss flagging for Reinsurance (BR-RSV-011 v2, LLNT £250,000)",
                    "Synchronisation with CLARA reserve movements through CLX-IF-049 until Wave 2"]))
    body.append(h(2, "Interfaces", "interfaces"))
    apis = []
    for x in s["apis"]:
        note = "planned for Wave 2 (ADR-028)" if x["path"] == "/revaluation-runs" else "live in pre-production"
        apis.append([e(x["method"]), f"<code>{e(x['path'])}</code>", e(x["summary"]), e(note)])
    body.append(table(["Method", "Path", "Summary", "Status"], apis, tid="api-table"))
    body.append(table(["Direction", "Topic", "Interface", "Notes"], [
        ["consumes", "<code>claims.reserve.movement.v1</code>", "CLX-IF-049", e("Bridged CLARA movements (ADR-012); key claim_id, schema v3")],
        ["consumes", "<code>triage.completed.v1</code>", "–", e("Tier changes trigger review rescheduling")],
        ["produces", "<code>reserve.changed.v2</code>", "CLX-IF-045", e("Consumed by gl-posting-svc and reporting-feed-svc")],
    ], tid="events-table"))
    body.append(h(2, "API detail", "api-detail"))
    for x in s["apis"]:
        if x["path"] == "/revaluation-runs":
            continue
        body.append(h(3, f"{x['method']} {x['path']}", None))
        body.append(p(x["summary"] + ". " + phrases.sentence(r, "api")))
        if x["method"] == "POST":
            body.append(table(["Field", "Type", "Notes"], [["reserveType", "string", "Reserve type code"],
                                                          ["movementType", "enum", "IN, AD, IX, RV, ST, RC"],
                                                          ["amount.amountMinor", "integer", "Minor units"],
                                                          ["amount.currency", "string", "GBP, NOK, SEK or DKK"],
                                                          ["reasonCode", "string", "Code list RSNC (BR-RSV-015)"]], raw=False))
        else:
            body.append(table(["Field", "Type", "Notes"], [["claimId", "string", "Claim reference"],
                                                          ["lines[]", "array", "One line per reserve type"],
                                                          ["lines[].outstanding", "Money", "Outstanding reserve"],
                                                          ["lines[].gbpEquivalent", "Money", "GBP equivalent at the GL rate"],
                                                          ["nextReviewDate", "date", "Tier-3 review date"]], raw=False))
    body.append(h(2, "Data model", "data-model"))
    drows = []
    for tname in s["postgres_tables"]:
        tb = W.tables[tname]
        cols = table(["Column", "Type", "Description"],
                     [[f"<code>{e(c['name'])}</code>", e(c["type"]), e(c["description"])] for c in tb["columns"]],
                     tid=f"cols-{tname.replace('.', '-')}", cls="confluenceTable nested")
        drows.append([f"<code>{e(tname)}</code>", e(tb["database"]), cols])
    body.append(table(["Table", "Database", "Columns"], drows, tid="data-model-table"))
    body.append(h(2, "Configuration", "configuration"))
    cfg_rows = [["tier3-review-days", e(t3), e(f"BR-RSV-007 v{rv7['version']}; changes to 14 when v3 is approved")],
                ["large-loss-threshold-gbp", e(s["config"]["large-loss-threshold-gbp"]), "BR-RSV-011 v2"]]
    body.append(table(["Key", "Value", "Source"], cfg_rows, tid="config-table"))
    body.append(macro("note", p("Indexation parameters for bodily-injury reserves are maintained by the Reserving team and "
                                "are not reproduced on this page."), title="Indexation"))
    body.append(h(2, "CLARA programs replaced", "replaced"))
    prows = []
    for pid in s["replaces_programs"]:
        pr = W.programs[pid]
        writes_rsv = "yes" if "CLR.T_RESERVE" in pr["writes_tables"] else "no"
        prows.append([f"<code>{e(pid)}</code>", e(pr["description"]), e(pr["type"]), e(writes_rsv)])
    body.append(table(["Program", "Description", "Type", "Writes CLR.T_RESERVE"], prows, tid="replaced-programs"))
    wrows = []
    for pid in W.reserve_writers:
        pr = W.programs[pid]
        wrows.append([f"<code>{e(pid)}</code>", e(pr["description"]), e(svcname(pr["replaced_by"], on) if pr["replaced_by"] else "–")])
    body.append(h(3, "All writers of CLR.T_RESERVE", "writers"))
    body.append(table(["Program", "Description", "Claims Hub owner"], wrows, tid="reserve-writers"))
    body.append(macro("warning", p("CLRGL090 (year-end revaluation) updates CLR.T_RESERVE without writing a reserve movement "
                                   "(internal audit finding IA-25-07; CHUB-284 closed as Won't Do). reserve-engine records "
                                   "revaluations as RV movements instead (DEC-005, 2026-03-05). CLRRS150 writes movements "
                                   "only."), title="Audit finding IA-25-07"))
    body.append(h(2, "Parallel run", "parallel-run"))
    body.append(p("The reserve parallel run compares CLARA and reserve-engine reserves daily from 2026-03-02 to 2026-08-28 "
                  "(CHUB-241). CLARA job CLRDRSV9 (program CLRRS210) produces the CLARA side of the comparison."))
    body.append(h(2, "Movement flow", "flow"))
    body.append(code("text", "Claims Handler -> reserve-engine: POST /reserves/{claimId}/movements\n"
                             "reserve-engine -> reserve-engine: authority check (BR-RSV-003 v3)\n"
                             "reserve-engine -> PostgreSQL: insert reserve.reserve_movement, update reserve.reserve\n"
                             "reserve-engine -> Kafka: reserve.changed.v2 (outbox)\n"
                             "gl-posting-svc <- Kafka: reserve.changed.v2\n"
                             "CLARA CLX-IF-042 -> MQ -> CLX-IF-049 bridge -> claims.reserve.movement.v1 -> reserve-engine",
                     cid="flow-diagram"))
    body.append(h(2, "Business rules implemented", "rules"))
    rrows = []
    for rid, rr in W.rules.items():
        if "reserve-engine" not in rr["implemented_in"]["services"]:
            continue
        v = W.rule_version(rid, on)
        if not v:
            continue
        rrows.append([e(rid), e(f"v{v['version']}"), e(rr["title"]), e(v["effective_from"])])
    body.append(table(["Rule", "Version", "Title", "Effective from"], rrows, tid="rules-table"))
    body.append(h(2, "Process steps supported", "process"))
    prow2 = []
    for st in W.steps.values():
        if "reserve-engine" in st["services"]:
            prow2.append([e(st["id"]), e(st["name"]), e(st["sla"]["text"] if st["id"] != "PS-RSV-03" else f"Tier-3 every {t3} days (BR-RSV-007 v{rv7['version']})")])
    body.append(table(["Step", "Name", "Service level"], prow2, tid="process-table"))
    body.append(h(2, "Non-functional requirements", "nfr"))
    body.append(table(["Area", "Requirement"], [
        ["Availability", "Same service tier as claim-core-svc; runs active in London with DR in Leeds."],
        ["Performance", "Performance tested before each migration wave at a multiple of the expected wave volume."],
        ["Security", "CIS tokens with reserve.read / reserve.write scopes; audit of every movement."],
        ["Data", "Amounts in minor units with the original currency and the GBP equivalent (ADR-016)."],
        ["Observability", "Structured logs, traces and SLO dashboards (ADR-024)."]], tid="nfr-table", raw=False))
    body.append(h(2, "Open questions", "open-questions"))
    body.append(ul(["Confirm with Reserving whether month-end snapshots stay in CLARA until Wave 2.",
                    "Agree the cut-over plan for review schedules when the 14-day cadence is approved.",
                    "Decide how long the CLX-IF-049 bridge runs after the last CLARA reserve writer is retired."]))
    body.append(h(2, "Replaced program detail", "replaced-detail"))
    body.append(p("Table access of the CLARA programs that reserve-engine replaces, taken from the program inventory. "
                  "It shows which CLARA data each program touches today."))
    pdrows = []
    for pid in s["replaces_programs"]:
        pr = W.programs[pid]
        ref_ = f"PROGRAM:{pid}"
        acc = []
        for t_ in pr["reads_tables"]:
            if may(fid, ref_, f"reads_tables:{t_}"):
                acc.append([f"<code>{e(t_)}</code>", "read"])
        for t_ in pr["writes_tables"]:
            if may(fid, ref_, f"writes_tables:{t_}"):
                acc.append([f"<code>{e(t_)}</code>", "write"])
        nested = table(["Table", "Access"], acc, tid=f"access-{pid}", cls="confluenceTable nested") if acc else "–"
        pdrows.append([f"<code>{e(pid)}</code>", e(pr["type"]), e(pr.get("jcl_job") or pr.get("cics_transaction") or "–"), nested])
    body.append(table(["Program", "Type", "Job / transaction", "Tables"], pdrows, tid="replaced-detail-table"))
    body.append(h(2, "Consumed event schema", "event-schema"))
    body.append(p("Avro value schema of claims.reserve.movement.v1 as agreed in the CLX-IF-049 data contract (schema "
                  "version 3). reserve-engine applies each movement idempotently on movement_id."))
    import json as _json
    avro = {"type": "record", "name": "ReserveMovement", "namespace": "com.corvane.claims.reserve",
            "fields": [{"name": n, "type": {"string": "string", "long": "long", "int": "int", "enum": "string",
                                            "date": {"type": "int", "logicalType": "date"},
                                            "timestamp-millis": {"type": "long", "logicalType": "timestamp-millis"}}[ty],
                        "doc": dsc} for n, ty, src, dsc in MOVEMENT_FIELDS]}
    body.append(code("json", _json.dumps(avro, indent=2), cid="movement-avro"))
    body.append(table(["Avro field", "RSVMOVE source"], [[f"<code>{e(n)}</code>", f"<code>{e(src)}</code>"]
                                                          for n, ty, src, dsc in MOVEMENT_FIELDS], tid="movement-mapping"))
    body.append(h(2, "Error codes", "error-codes"))
    body.append(table(["Code", "Meaning"], [[f"<code>{e(c)}</code>", e(m)] for c, m in RSV_ERROR_CODES], tid="error-codes-table"))
    body.append(h(2, "Operational runbook", "runbook"))
    body.append("<ol id=\"runbook-steps\">" + "".join(f"<li>{e(x)}</li>" for x in r.sample(phrases.BANKS["runbook_if"], 6)) + "</ol>")
    body.append(h(2, "Test approach", "tests"))
    body.append(ul(r.sample(phrases.BANKS["tests"], 7), uid="test-approach"))
    body.append(h(2, "Design principles", "principles"))
    body.append(ul(r.sample(phrases.BANKS["design"], 7)))
    body.append(h(2, "Decisions", "decisions"))
    body.append(table(["ID", "Date", "Decision"], [[e(d), e(W.decisions[d]["date"]), e(W.decisions[d]["statement"])]
                                                  for d in ["DEC-005", "DEC-006", "DEC-017", "DEC-018"]], tid="design-decisions"))
    body.append(h(2, "Related pages", "related"))
    body.append(related_links(fid))
    content = render_page(fid, "\n".join(body), ["reserve-engine", "design", "architecture"],
                          comments_for(fid, ["P009", "P053", "P018"]), attachments=["reserve-engine-context.png"])
    F.add("alias_use", "reserve-engine design page: reserve-svc was renamed reserve-engine on 2026-02-10 (CHUB-233, ADR-019).",
          hloc("//div[contains(@class,'confluence-information-macro-information')]"), "renamed reserve-engine on 2026-02-10",
          world_ref="SERVICE:reserve-engine#renames")
    F.add("temporal", "As of 2026-03-09 reserve-engine config tier3-review-days is 21 (BR-RSV-007 v2).",
          hloc("//table[@id='config-table']//tr[td[1]='tier3-review-days']"), "tier3-review-days 21",
          world_ref="SERVICE:reserve-engine#config.config_history")
    F.add("general", "Eight CLARA programs write CLR.T_RESERVE, including CLRFN030, CLRST040, CLRRC050 and CLRGL090.",
          hloc("//table[@id='reserve-writers']"), "CLRGL090", world_ref="TABLE:CLR.T_RESERVE#writers")
    F.add("general", "reserve-engine consumes claims.reserve.movement.v1 from CLX-IF-049 and produces reserve.changed.v2.",
          hloc("//table[@id='events-table']"), "claims.reserve.movement.v1 CLX-IF-049", world_ref="SERVICE:reserve-engine#kafka_topics")
    F.add("general", "DEC-005: reserve-engine records currency revaluations as RV movements (closing IA-25-07 in the target).",
          hloc("//table[@id='design-decisions']"), "record currency revaluations as RV movements", world_ref="DECISION:DEC-005")
    F.add("general", "reserve-engine error RSV-AUT-010: amount exceeds the caller's reserve authority (BR-RSV-003 v3).",
          hloc("//table[@id='error-codes-table']//tr[td[1]/code='RSV-AUT-010']"), "exceeds the caller's reserve authority",
          world_ref="RULE:BR-RSV-003@v3")
    return Built(fid, content, F.items, f"{len(apis) + len(prows) + len(wrows)} rows")


# ---------------------------------------------------------------------------------------------
# ST059 Fraud rules 2026
# ---------------------------------------------------------------------------------------------

def build_ST059(out_dir: pathlib.Path) -> Built:
    fid = "ST059"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:fraud")
    t2 = rule_params_ok(fid, "BR-FRD-031", 2)
    body = [macro("information", p("From 2026-10-01 Tier-3 claims are referred to SIU at a Sentinel score of 60 or more; "
                                   "all other claims stay at 65 (Fraud Rules Workshop 2026-09-17, DEC-014). This page "
                                   "replaces the April 2026 version."), title="What changed on 2026-10-01")]
    body.append(h(2, "Rules in force", "in-force"))
    summary_rows = [
        ["BR-FRD-031 v2", f"{t2['threshold']}; Tier-3 {t2['tier3_threshold']} from 2026-10-01"],
        ["BR-FRD-032 v2", "customer notice within 10 business days of referral"],
        ["BR-FRD-033", "no decline, reduction or repudiation on the score alone"],
        ["BR-FRD-034", "NISA-FR1 within 30 days after each quarter end"],
        ["BR-FRD-035 v2", "SIU triage within 3 business days"],
        ["BR-FRD-036 v2", "notice deferral up to 60 days; beyond 30 days needs the Head of Counter-Fraud & SIU"],
    ]
    inforce = table(["Rule", "In short"], [[e(a_), e(b_)] for a_, b_ in summary_rows], tid="in-force-2026-10-01",
                    cls="confluenceTable nested")
    rows = []
    for rid in ["BR-FRD-031", "BR-FRD-032", "BR-FRD-033", "BR-FRD-034", "BR-FRD-035", "BR-FRD-036"]:
        rr = W.rules[rid]
        vrows = []
        for v in sorted(rr["versions"], key=lambda x: -x["version"]):
            if v["status"] == "draft":
                continue
            prm = rule_params_ok(fid, rid, v["version"])
            txt = v["text"] if rule_text_ok(fid, rid, v["version"]) else "Superseded wording – see the April 2026 page history."
            vrows.append([e(f"v{v['version']}"), e(v["status"]), e(v["effective_from"]), e(v["effective_to"] or "–"),
                          e(", ".join(f"{k}={val}" for k, val in prm.items()) or "–"), e(txt)])
        vt = table(["Version", "Status", "From", "To", "Parameters", "Wording"], vrows, tid=f"versions-{rid}",
                   cls="confluenceTable nested")
        rows.append([f"<strong>{e(rid)}</strong>", e(rr["title"]), vt,
                     e(", ".join(rr["implemented_in"]["services"] + rr["implemented_in"]["programs"]) or "–")])
    body.append(table(["Summary"], [[inforce]], tid="summary-wrapper"))
    body.append(table(["Rule", "Title", "Versions", "Implemented in"], rows, tid="fraud-rules-2026"))
    body.append(h(2, "Superseded and withdrawn", "superseded"))
    body.append(table(["Rule", "Title", "Status", "Replaced by"], [
        ["BR-FRD-012", e(W.rules["BR-FRD-012"]["title"]), "superseded 2026-04-01 (was 70 from 2023-04-01; 75 before)", "BR-FRD-031"],
        ["BR-FRD-019", e(W.rules["BR-FRD-019"]["title"]), "withdrawn from 2026-04-01 (NISA Circular 2026/04 §3.1)", "BR-FRD-033"],
    ], tid="superseded-table"))
    body.append(h(2, "Tier-3 definition", "tier3"))
    tri = W.rule_version("BR-TRI-003", on)
    body.append(macro("tip", p(f"BR-TRI-003 v{tri['version']}: {tri['text']}"), title="Who counts as Tier-3?"))
    body.append(h(2, "Pre-screen indicators", "indicators"))
    irows = []
    for rid in ["BR-FRD-001", "BR-FRD-002", "BR-FRD-003", "BR-FRD-004", "BR-FRD-006", "BR-FRD-007", "BR-FRD-008",
                "BR-FRD-009", "BR-FRD-014", "BR-FRD-015", "BR-FRD-016"]:
        v = W.rule_version(rid, on)
        irows.append([e(rid), e(W.rules[rid]["title"].replace("Indicator: ", "")), e(rule_params_ok(fid, rid, v["version"]).get("pts"))])
    body.append(table(["Rule", "Indicator", "Points"], irows, tid="indicator-table"))
    body.append(h(2, "Implementation status", "implementation"))
    body.append(table(["System", "Change", "Ticket", "Status"], [
        ["CLARA", e("CLR.T_PARAM FRD_REFER_THRESH = 65 from 2026-04-01"), "CHUB-205", status("done", "success")],
        ["CLARA", e("CLR.T_PARAM FRD_REFER_T3_THRESH = 60 valid from 2026-10-01"), "CHUB-395", status("done", "success")],
        ["Claims Hub", e("fraud-referral-svc Tier-3 threshold 60 from 2026-10-01"), "CHUB-388", status("done", "success")],
        ["CLARA", e("CLRFR040 batch sweep still uses a hard-coded threshold instead of CLR.T_PARAM (INC-2026-0518)"),
         "CHUB-298", status("open", "error")],
    ], tid="implementation-table"))
    body.append(macro("warning", p("Until CHUB-298 is fixed, referrals from the nightly batch sweep (job CLRNFR01) must be "
                                   "cross-checked against the online referrals each morning."), title="Known issue"))
    body.append(h(2, "Regulatory basis", "regulatory"))
    circ = W.circulars["CIRC-2026-04"]
    body.append(table(["Paragraph", "Requirement"], [[e(x["para"]), e(x["text"])] for x in circ["requirements"]],
                      tid="circular-table"))
    body.append(h(2, "Workshop decisions (2026-09-17)", "decisions"))
    body.append(table(["ID", "Decision", "Decided by"], [[e(d), e(W.decisions[d]["statement"]),
                                                         e(", ".join(pname(x, on) for x in W.decisions[d]["decided_by"]))]
                                                        for d in ["DEC-014", "DEC-015", "DEC-016"]], tid="workshop-decisions"))
    body.append(h(2, "Threshold history", "threshold-history"))
    hrows = []
    for rid, ver in (("BR-FRD-012", 1), ("BR-FRD-012", 2), ("BR-FRD-031", 1), ("BR-FRD-031", 2)):
        v = rule_ver(rid, ver)
        prm = rule_params_ok(fid, rid, ver)
        hrows.append([e(f"{rid} v{ver}"), e(v["effective_from"]), e(v["effective_to"] or "–"), e(prm.get("threshold")),
                      e(prm.get("tier3_threshold") or "–"), e(v["source"])])
    body.append(table(["Rule", "From", "To", "Threshold", "Tier-3 threshold", "Source"], hrows, tid="threshold-history"))
    body.append(h(2, "Worked examples", "examples"))
    body.append(table(["Claim", "Tier", "Sentinel score", "Threshold applied", "Referred?"], [
        ["Example A", "Tier-2", "64", "65", "No"], ["Example B", "Tier-3", "62", "60", "Yes"],
        ["Example C", "Tier-1", "71", "65", "Yes"], ["Example D", "Tier-3", "59", "60", "No (handler may still refer)"]],
        tid="worked-examples", raw=False))
    body.append(h(2, "FAQ", "faq"))
    body.append("<dl>" + "".join(f"<dt>{e(q)}</dt><dd>{e(a_)}</dd>" for q, a_ in [
        ("Does the Tier-3 threshold apply to claims referred before 2026-10-01?", "No. The threshold in force on the scoring date applies."),
        ("Can a claim be declined because of a high score?", "No. BR-FRD-033 requires a documented human review by SIU for every adverse outcome."),
        ("When must the customer be told?", "Within 10 business days of the referral, unless the notice is deferred under BR-FRD-036."),
        ("Who defines Tier-3?", "BR-TRI-003 v3 (Claims Operations)."),
    ]) + "</dl>")
    body.append(h(2, "Referral process", "process"))
    frows = []
    for sid in W.stages["S5"]["steps"]:
        st = W.steps[sid]
        dec = ""
        if st["decision"]:
            dec = "; ".join(b["condition"] for b in st["decision"]["branches"])
        frows.append([e(sid), e(st["name"]), e(st["sla"]["text"]), e(dec or "–")])
    body.append(table(["Step", "Name", "Service level", "Decision"], frows, tid="referral-process"))
    body.append(h(2, "NISA-FR1 timetable", "fr1"))
    fr1 = W.reports["NISA-FR1"]["submissions"]
    body.append(table(["Period", "Due", "Submitted"], [
        ["2026Q2", e(fr1["2026Q2"]["due"]), e(fr1["2026Q2"]["submitted"])],
        ["2026Q3", e(fr1["2026Q3"]["due"]), "in preparation"]], tid="fr1-timetable"))
    body.append(h(2, "Contacts", "contacts"))
    body.append(table(["Role", "Name"], [[e(ptitle(x, on)), e(pname(x, on))] for x in ["P008", "P028", "P027", "P037", "P042"]],
                      tid="fraud-contacts"))
    body.append(h(2, "All fraud rules in force on 2026-10-01", "all-rules"))
    arows2 = []
    for rid2, rr2 in W.rules.items():
        if not rid2.startswith("BR-FRD-"):
            continue
        v2 = W.rule_version(rid2, "2026-10-01")
        if not v2 or not may(fid, f"RULE:{rid2}"):
            continue
        impl = ", ".join(rr2["implemented_in"]["services"] + rr2["implemented_in"]["programs"]) or "–"
        arows2.append([e(rid2), e(f"v{v2['version']}"), e(rr2["title"]), e(pname(rr2["owner"], on)),
                       e(v2["effective_from"]), e(impl)])
    body.append(table(["Rule", "Version", "Title", "Owner", "Effective from", "Implemented in"], arows2, tid="all-fraud-rules"))
    body.append(h(2, "Where the 2026 rules are implemented", "implementation-detail"))
    idrows = []
    for rid2 in ["BR-FRD-031", "BR-FRD-032", "BR-FRD-033", "BR-FRD-034", "BR-FRD-035", "BR-FRD-036"]:
        rr2 = W.rules[rid2]
        comps = [[f"<code>{e(svcname(x, on))}</code>", "Claims Hub service", e(W.services[x]["description"])]
                 for x in rr2["implemented_in"]["services"]]
        comps += [[f"<code>{e(x)}</code>", "CLARA program", e(W.programs[x]["description"])]
                  for x in rr2["implemented_in"]["programs"]]
        nested = (table(["Component", "Kind", "Description"], comps, tid=f"impl-{rid2}", cls="confluenceTable nested")
                  if comps else "–")
        idrows.append([f"<strong>{e(rid2)}</strong>", e(rr2["title"]), nested])
    body.append(table(["Rule", "Title", "Components"], idrows, tid="implementation-detail-table"))
    body.append(h(2, "Related tickets", "tickets"))
    tk_rows = []
    for t in sorted(W.tickets.values(), key=lambda x: x["id"]):
        if str(t["created"]) > on or str(t["created"]) < "2026-01-01" or not may(fid, f"TICKET:{t['id']}"):
            continue
        if t.get("component") not in ("Fraud", "fraud-referral-svc") and "BR-FRD" not in t["summary"]:
            continue
        res = str(t.get("resolved") or "")
        st_ = "Done" if res and res <= on else "Open"
        tk_rows.append([e(t["id"]), e(t["summary"]), e(t.get("component") or "–"),
                        status(st_, "success" if st_ == "Done" else "error"), e(res if st_ == "Done" else "–")])
    body.append(table(["Key", "Summary", "Component", "Status", "Resolved"], tk_rows, tid="related-tickets"))
    body.append(h(2, "Configuration example", "config"))
    body.append(code("yaml", "referral:\n  threshold:\n    default: 65\n    tier3: 60\n    tier3.effective-from: 2026-10-01\n"
                             "notice:\n  business-days: 10\n  max-deferral-days: 60\nauto-decline:\n  enabled: false",
                     cid="config-example"))
    body.append(p(phrases.paragraph(r, "governance", 2)))
    body.append(h(2, "Related pages", "related"))
    body.append(related_links(fid))
    content = render_page(fid, "\n".join(body), ["fraud", "rules", "nisa-2026-04", "siu"],
                          comments_for(fid, ["P027", "P037", "P042"]))
    F.add("needle", "Wiki fraud rules 2026 nested table: BR-FRD-031 v2 (65; Tier-3 60 from 2026-10-01), BR-FRD-032 v2, BR-FRD-033, BR-FRD-034, BR-FRD-036 v2.",
          hloc("//table[@id='in-force-2026-10-01']"), "BR-FRD-031 v2 65; Tier-3 60 from 2026-10-01",
          world_ref="RULE:BR-FRD-031@v2", placement="PL-188")
    F.add("general", "Wiki fraud rules: BR-FRD-036 v2 – deferral up to 60 days; beyond 30 days needs the Head of Counter-Fraud & SIU.",
          hloc("//table[@id='in-force-2026-10-01']"), "BR-FRD-036 v2 notice deferral up to 60 days", world_ref="RULE:BR-FRD-036@v2")
    F.add("general", "Wiki fraud rules: BR-FRD-019 auto-decline withdrawn from 2026-04-01 and replaced by BR-FRD-033.",
          hloc("//table[@id='superseded-table']"), "withdrawn from 2026-04-01", world_ref="RULE:BR-FRD-019")
    F.add("general", "Wiki fraud rules: CLRFR040 hard-coded threshold defect CHUB-298 still open on 2026-10-02.",
          hloc("//table[@id='implementation-table']"), "CHUB-298", world_ref="TICKET:CHUB-298")
    F.add("general", "DEC-016: lowering the general referral threshold to 60 for all claims was rejected.",
          hloc("//table[@id='workshop-decisions']"), "Option to lower the general referral threshold to 60 for all claims rejected",
          world_ref="DECISION:DEC-016")
    F.add("general", "NISA Circular 2026/04 §3.3: score cut-offs on a 0–100 scale must not exceed 65.",
          hloc("//table[@id='circular-table']"), "must not exceed 65", world_ref="CIRCULAR:CIRC-2026-04#requirements")
    F.add("general", "BR-FRD-034 (quarterly NISA-FR1 return) is owned by Ruth Okafor and implemented in reporting-feed-svc and CLRFR090.",
          hloc("//table[@id='all-fraud-rules']//tr[td[1]='BR-FRD-034']"), "Ruth Okafor", world_ref="RULE:BR-FRD-034#owner")
    return Built(fid, content, F.items, f"{len(rows) + len(irows)} rows")


# ---------------------------------------------------------------------------------------------
# ST060 Release notes (stop at R2026.09 Wave1)
# ---------------------------------------------------------------------------------------------

LAST_RELEASE = "R2026.09 Wave1"
SUMMARY_OVERRIDES = {"CHUB-262": "Wave 0 Denmark migration"}


def build_ST060(out_dir: pathlib.Path) -> Built:
    fid = "ST060"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:releases")
    fvs = W.raw["key_tickets"]["fix_versions"]
    names = [f["name"] for f in fvs]
    published = names[: names.index(LAST_RELEASE) + 1]
    body = [macro("information", p(f"Release notes are published here after CAB approval. The latest published release is "
                                   f"{LAST_RELEASE} ({fvs[names.index(LAST_RELEASE)]['release_date']})."),
                  title="Publication")]
    body.append(h(2, "Releases", "releases"))
    body.append(table(["Release", "Date", "Highlights"], [
        [f'<a href="#rel-{e(n.split()[0])}">{e(n)}</a>', e(fvs[names.index(n)]["release_date"]),
         e(len([t for t in W.tickets.values() if t.get("fix_version") == n]))] for n in reversed(published)],
        tid="release-index"))
    total_rows = 0
    for n in reversed(published):
        rel = fvs[names.index(n)]
        tks = sorted([t for t in W.tickets.values() if t.get("fix_version") == n], key=lambda t: t["id"])
        done = [t for t in tks if t["status"] == "Done"]
        carried = [t for t in tks if t["status"] != "Done"]
        body.append(f'<h2 id="rel-{e(n.split()[0])}">{e(n)} – released {e(rel["release_date"])}</h2>')
        comps = sorted({t.get("component") or "General" for t in done})
        body.append(p(f"This release delivered {len(done)} change(s) across {', '.join(comps)}. " +
                      phrases.sentence(r, "wiki")))
        rows = []
        for t in done:
            summ = SUMMARY_OVERRIDES.get(t["id"], t["summary"])
            rows.append([e(t["id"]), e(t["type"]), e(summ), e(t.get("component") or "–"),
                         e(pname(t["assignee"], rel["release_date"]) if t.get("assignee") else "–"), e(t.get("resolved") or "–")])
        total_rows += len(rows)
        inner = table(["Key", "Type", "Summary", "Component", "Assignee", "Resolved"], rows,
                      tid=f"tickets-{n.split()[0]}", cls="confluenceTable nested")
        known = table(["Key", "Summary", "Status"], [[e(t["id"]), e(t["summary"]), e(t["status"])] for t in carried] or
                      [["–", "No known issues carried over", "–"]], tid=f"known-{n.split()[0]}", cls="confluenceTable nested")
        cc: dict = {}
        for t in done:
            cc[t.get("component") or "General"] = cc.get(t.get("component") or "General", 0) + 1
        comp_t = table(["Component", "Changes"], [[e(k), e(v)] for k, v in sorted(cc.items())],
                       tid=f"components-{n.split()[0]}", cls="confluenceTable nested")
        contrib = sorted({pname(t["assignee"], rel["release_date"]) for t in done if t.get("assignee")})
        body.append(table(["Section", "Content"], [["Changes", inner], ["Components", comp_t],
                                                   ["Contributors", e(", ".join(contrib) or "–")],
                                                   ["Carried over / known issues", known],
                                                   ["Deployment", e("Rolling deployment through GitOps after CAB approval; "
                                                                    "rollback by reverting the release tag.")]],
                          tid=f"release-{n.split()[0]}"))
    body.append(h(2, "How releases are made", "release-process"))
    body.append("<ol id=\"release-process-list\">" + "".join(f"<li>{e(x)}</li>" for x in r.sample(phrases.BANKS["release_process"], 7)) + "</ol>")
    body.append(h(2, "Checking what is deployed", "deployed-version"))
    body.append(p("The running image tag of a service shows which release it belongs to. For example:"))
    body.append(code("bash", "oc -n chub-reserve get deploy reserve-engine \\\n"
                             "  -o jsonpath='{.spec.template.spec.containers[0].image}{\"\\n\"}'\n"
                             "# image tags follow the release name, e.g. r2026.09.<patch>\n"
                             "argocd app get claims-hub-prod --show-operation", cid="deployed-version-cmd"))
    body.append(h(2, "Related pages", "related"))
    body.append(related_links(fid))
    content = render_page(fid, "\n".join(body), ["release-notes", "releases"], comments_for(fid, ["P032", "P048"]))
    assert b"R2026.11" not in content
    F.add("general", "Release notes stop at R2026.09 Wave1 (released 2026-09-14); later releases are not published on the page.",
          hloc("//div[contains(@class,'confluence-information-macro-information')]"),
          "latest published release is R2026.09 Wave1 (2026-09-14)", world_ref="ANCHOR:ST060",
          notes="Deliberate: the follow-up commit (R2026.11) is a re-sync-only fact.")
    F.add("general", "R2026.09 Wave1 included CHUB-371: duplicate payment instructions for 18 claims on the Wave 1 weekend (INC-2026-0914).",
          hloc("//table[@id='tickets-R2026.09']"), "Duplicate payment instructions for 18 claims", world_ref="TICKET:CHUB-371")
    F.add("general", "R2026.04 NISA delivered CHUB-209: fraud-referral-svc customer-notice endpoint and 10-business-day deadline.",
          hloc("//table[@id='tickets-R2026.04']"), "customer-notice endpoint and 10-business-day deadline",
          world_ref="TICKET:CHUB-209")
    F.add("general", "R2026.02 delivered CHUB-233: rename reserve-svc to reserve-engine per ADR-019.",
          hloc("//table[@id='tickets-R2026.02']"), "Rename reserve-svc to reserve-engine", world_ref="TICKET:CHUB-233")
    F.add("general", "R2026.07 delivered CHUB-322: reserve-engine still scheduled Tier-3 reviews at 21 days (INC-2026-0702).",
          hloc("//table[@id='tickets-R2026.07']"), "reserve-engine still schedules Tier-3 reviews at 21 days",
          world_ref="TICKET:CHUB-322")
    return Built(fid, content, F.items, f"{total_rows} rows")


BUILDERS = {
    "ST053": build_ST053, "ST054": build_ST054, "ST055": build_ST055, "ST056": build_ST056,
    "ST057": build_ST057, "ST058": build_ST058, "ST059": build_ST059, "ST060": build_ST060,
}
