"""Root files, .github/CODEOWNERS, docs/adr and docs/diagrams."""
from __future__ import annotations

import datetime as dt
import io

from lib import W, SVC, OLD_RESERVE, NEW_RESERVE, HEAD_DATE, rng, person
from services import T
from infra import ORDER, namespaces, topics, FRAUD_NOTICE_TOPIC
from generators.common import util

# ---------------------------------------------------------------------------------------------
# CODEOWNERS
# ---------------------------------------------------------------------------------------------

def codeowners_lines(variant: str) -> list[tuple[str, str]]:
    plan = W.corpus_plan
    code = [f for f in plan["families"] if f["family"] == "CODE"][0]
    mapping = dict(code["codeowners_variant_a"])
    if variant == "c":
        mapping.update(code["codeowners_variant_c_changes"])
    out = []
    for key, owners in mapping.items():
        for path in str(key).split():
            out.append((path, owners))
    if variant == "c":
        # c changes are separate keys that re-assign single paths: keep the first occurrence order
        seen, merged = set(), []
        for path, owners in out:
            if path in seen:
                continue
            seen.add(path)
            merged.append((path, mapping.get(path, owners)))
        out = merged
    return out


def codeowners(variant: str) -> str:
    rows = codeowners_lines(variant)
    head = [
        "# CODEOWNERS for the Claims Hub / CLARA monorepo.",
        "# Each line is a path pattern followed by its owners; owners are requested as reviewers",
        "# automatically and one owner approval is required to merge.",
        "",
    ]
    groups = [
        ("# CLARA mainframe sources", lambda p: p.startswith("/legacy/")),
        ("# Claims Hub services", lambda p: p.startswith("/services/")),
        ("# Platform: infrastructure and deployment", lambda p: p in ("/infra/", "/deploy/")),
        ("# Architecture decision records", lambda p: p.startswith("/docs/adr/")),
    ]
    width = max(len(p) for p, _ in rows) + 2
    body = []
    for title, pred in groups:
        sel = [(p, o) for p, o in rows if pred(p)]
        if not sel:
            continue
        body.append(title)
        for p, o in sel:
            body.append(f"{p.ljust(width)}{o}")
        body.append("")
    return "\n".join(head + body)


# ---------------------------------------------------------------------------------------------
# Root files
# ---------------------------------------------------------------------------------------------

GITIGNORE = """
# Build output
target/
build/
*.class
*.jar

# IDEs
.idea/
*.iml
.vscode/
.DS_Store

# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
!*.example.tfvars

# Python tooling
__pycache__/
*.pyc
.venv/

# Local environment files (never commit credentials)
.env
*.local.yaml
"""


def makefile() -> str:
    services = " \\\n            ".join(ORDER)
    return (
        "# Convenience targets for the Claims Hub monorepo.\n"
        "# Java services build with Maven; infrastructure is validated with Terraform.\n\n"
        f"SERVICES := {services}\n\n"
        "SERVICE ?=\n"
        "MVN ?= mvn -B -ntp\n\n"
        ".PHONY: help build test tf-fmt tf-validate k8s-lint clean\n\n"
        "help:\n"
        "\t@echo \"make build [SERVICE=<name>]   build one service or all of them\"\n"
        "\t@echo \"make test [SERVICE=<name>]    run unit tests\"\n"
        "\t@echo \"make tf-validate              validate the Terraform environment root\"\n\n"
        "build:\n"
        "ifeq ($(SERVICE),)\n"
        "\t@for s in $(SERVICES); do $(MVN) -f services/$$s/pom.xml package -DskipTests || exit 1; done\n"
        "else\n"
        "\t$(MVN) -f services/$(SERVICE)/pom.xml package -DskipTests\n"
        "endif\n\n"
        "test:\n"
        "ifeq ($(SERVICE),)\n"
        "\t@for s in $(SERVICES); do $(MVN) -f services/$$s/pom.xml test || exit 1; done\n"
        "else\n"
        "\t$(MVN) -f services/$(SERVICE)/pom.xml test\n"
        "endif\n\n"
        "tf-fmt:\n"
        "\tterraform fmt -recursive infra/terraform\n\n"
        "tf-validate:\n"
        "\tcd infra/terraform/envs/prod && terraform init -backend=false && terraform validate\n\n"
        "k8s-lint:\n"
        "\t@for f in deploy/k8s/*/*.yaml; do kubectl apply --dry-run=client -f $$f >/dev/null || exit 1; done\n\n"
        "clean:\n"
        "\t@for s in $(SERVICES); do rm -rf services/$$s/target; done\n"
    )


def root_readme() -> str:
    clara = W.systems["SYS01"]
    lines = [
        "# Corvane Claims Platform monorepo",
        "",
        "This repository holds both halves of Programme Skerry: the CLARA mainframe sources that are",
        "being retired and the Claims Hub services that replace them (ADR-001, strangler-fig migration).",
        "",
        "| Path | Contents |",
        "|---|---|",
        "| `legacy/clara/` | CLARA (Claims Ledger And Reserve Application): COBOL programs, copybooks, JCL, BMS maps and DB2 DDL |",
        "| `services/` | Claims Hub services (Java 21, Spring Boot), one Maven module per service |",
        "| `infra/terraform/` | Terraform modules, one per service (ADR-007), and the `envs/prod` root |",
        "| `deploy/k8s/` | OpenShift manifests, one folder per namespace |",
        "| `api/openapi/` | OpenAPI descriptions of the service REST APIs |",
        "| `docs/adr/` | Architecture decision records |",
        "| `docs/diagrams/` | Event-flow and sequence diagrams |",
        "",
        "## Claims Hub services",
        "",
        "| Service | Namespace | Status | Go-live |",
        "|---|---|---|---|",
    ]
    for n in ORDER:
        s = SVC[n]
        lines.append(f"| `{n}` | `{s['k8s_namespace']}` | {s['status']} | {s['go_live']} |")
    lines += [
        "",
        "Services exchange domain events on the Event Streaming Platform (cluster `esp-prd`); topic names",
        "follow `<domain>.<event>.v<n>` (ADR-002). Each service owns its PostgreSQL database (ADR-003).",
        "",
        "## Building",
        "",
        "Run `make build SERVICE=<name>` to build one service, or `make build` for all of them. Java 21 and",
        "Maven 3.9 are required; `make help` lists the other targets.",
        "",
        "## Documentation",
        "",
        "- Architecture decisions: [docs/adr](docs/adr/)",
        "- Diagrams: [docs/diagrams](docs/diagrams/)",
        "- Code owners: [.github/CODEOWNERS](.github/CODEOWNERS)",
        "",
    ]
    return "\n".join(lines)


def root_readme_mods(repo, path):
    repo.modify(path, "F-25",
                "Run `make build` from the repository root. Java 21 and\nMaven 3.9 are required; `make help` lists the other targets.\n",
                "Run `make build SERVICE=<name>` to build one service, or `make build` for all of them. Java 21 and\n"
                "Maven 3.9 are required; `make help` lists the other targets.\n")
    repo.modify(path, "F-24", "- Architecture decisions: [docs/adr](docs/adrs/)\n- Diagrams: [docs/diagrams](docs/diagram/)\n",
                "- Architecture decisions: [docs/adr](docs/adr/)\n- Diagrams: [docs/diagrams](docs/diagrams/)\n")
    repo.modify(path, "CM-04", f"| `{OLD_RESERVE}` |", f"| `{NEW_RESERVE}` |")


# ---------------------------------------------------------------------------------------------
# ADRs
# ---------------------------------------------------------------------------------------------

ADR_TEXT = {
    "ADR-001": ("CLARA has been the claims system of record since 1994 and every open claim lives in it. Replacing it in one cut-over would put the whole claims operation at risk at once.",
                "Replace CLARA capability by capability with Claims Hub services and move traffic to each new service as its capability and region migrate."),
    "ADR-002": ("Claims Hub services must share domain events without point-to-point coupling, and the Integration Platform team already runs the Event Streaming Platform.",
                "Use Kafka on the Event Streaming Platform as the event backbone for every Claims Hub service."),
    "ADR-003": ("A shared database would couple the data models and release cycles of independent services.",
                "Each Claims Hub service owns exactly one PostgreSQL database; no other service reads or writes it."),
    "ADR-004": ("CLARA's interfaces run over MQ Backbone. Rewriting them before CLARA is switched off would add risk for no lasting benefit.",
                "Keep MQ for every CLARA-facing interface until CLARA is decommissioned, and do not build new MQ flows from Claims Hub."),
    "ADR-005": ("Claims Hub needs CLARA's reserve movements during the reserve parallel run and for later synchronisation.",
                "Capture changes from DB2 with change data capture on CLR.T_RESERVE_MOVEMENT."),
    "ADR-006": ("Claims Hub needs a container platform with a primary and a disaster-recovery site.",
                "Run all Claims Hub services on OpenShift."),
    "ADR-007": ("Platform resources were being created by hand and drifted between environments.",
                "Describe each service's platform resources in its own Terraform module."),
    "ADR-008": ("Staff and partner users need one identity across Claims Hub and the partner portal.",
                "Authenticate workforce and partner users through Corvane Identity Service using OIDC."),
    "ADR-009": ("Claim documents are large binaries with their own retention rules.",
                "Keep document binaries in DOCSTOR (renamed Evidence Vault in November 2025) and expose only metadata through document-svc."),
    "ADR-010": ("Business rules such as referral cut-offs change on dates set by the business and the regulator, often between releases.",
                "Hold business rules as versioned configuration with effective dates instead of introducing a rules engine."),
    "ADR-011": ("Several CLARA programs write to the reserve table, which makes reserve changes hard to audit.",
                "In Claims Hub only the reserve service writes reserves; every other service requests a reserve movement through its API."),
    "ADR-012": ("Change data capture cannot see every reserve change in CLARA (see ADR-005), but the CLX-IF-042 extract already carries every movement record.",
                "Bridge the CLX-IF-042 records from MQ to Kafka (CLX-IF-049) and let reserve-engine consume them."),
    "ADR-013": ("Fraud scores are needed at triage time, and Sentinel offers a synchronous REST scoring API.",
                "Call Sentinel synchronously over REST from triage-svc."),
    "ADR-014": ("Fraud referral notices have a regulatory deadline and must use approved wording.",
                "Send all customer notifications through notification-svc and the Notify platform."),
    "ADR-015": ("Migrating every claim at once would concentrate risk on one weekend.",
                "Migrate claims in waves by region and line of business."),
    "ADR-016": ("Nordic claims are paid and reserved in local currency, but authority checks and finance reporting work in GBP.",
                "Store every amount in its original currency and as a GBP equivalent."),
    "ADR-017": ("CDC on the movement table misses reserve changes made by CLRGL090, which updates CLR.T_RESERVE directly (the reason ADR-005 failed).",
                "Synchronise reserves through the batch-to-event bridge (ADR-012) instead of CDC."),
    "ADR-018": ("Several services needed the claim tier and were each re-implementing BR-TRI-003.",
                "Publish the tier calculation as a shared Java library."),
    "ADR-019": ("The reserve service had grown beyond simple CRUD: it runs Tier-3 review scheduling, indexation and currency revaluation.",
                "Rename reserve-svc to reserve-engine (CHUB-233), including the repository path, the Terraform module and the reserve change event."),
    "ADR-020": ("NISA Circular 2026/04 and the fraud rules workshops change referral thresholds on fixed dates.",
                "Configure fraud referral thresholds as effective-dated values in fraud-referral-svc's configuration."),
    "ADR-021": ("INC-2026-0914: duplicate payment instructions were sent on the Wave 1 cut-over because payment-orchestrator retried after a Corvane Payments Gateway timeout without an idempotency key.",
                "Every payment instruction sent to the Corvane Payments Gateway carries an idempotency key."),
    "ADR-022": ("Subrogation cases move to recovery-svc with Wave 1, leaving the Subrogation Tracker (SUBTRAK) with no new work.",
                "Retire SUBTRAK once Wave 1 recoveries are stable in recovery-svc."),
    "ADR-023": ("Producers and consumers of Kafka topics are released independently, so schema changes can break consumers silently.",
                "Every Kafka topic has contract tests and a registered schema."),
    "ADR-024": ("Services need common dashboards, alerting and service-level objectives before go-live.",
                "Adopt one observability stack and define SLOs per service."),
    "ADR-025": ("Migration rehearsals copy production claim data into non-production environments.",
                "Use masked data for every migration rehearsal."),
    "ADR-026": ("Claims handlers still need to look up history in CLARA after their claims have migrated.",
                "Keep CICS enquiry transactions available read-only after cut-over until CLARA is decommissioned."),
    "ADR-027": ("reporting-feed-svc will take over regulatory extracts from CLARA, and returns must not change unnoticed.",
                "Run the CLARA and Claims Hub regulatory extracts side by side for two quarters."),
    "ADR-028": ("CLRGL090 revalues Nordic reserves without writing reserve movements, which left an audit gap (finding IA-25-07).",
                "From Wave 2 use the reserve-engine revaluation run instead of CLRGL090."),
    "ADR-029": ("Partner traffic from the Assessor Portal can spike and affect internal users.",
                "Apply API gateway rate limits to partner traffic."),
    "ADR-030": ("The shared tier library (ADR-018) let services drift onto different library versions with different thresholds.",
                "Replace the shared library with the triage-svc API; tiering is centralised in triage-svc."),
}

STATUS_LABEL = {"accepted": "Accepted", "superseded": "Superseded", "deprecated": "Deprecated", "proposed": "Proposed"}
FOLLOW_UP = [
    "Teams record follow-up work in the Claims Hub backlog and link it to this record.",
    "Changes to this decision need a new ADR reviewed by the Design Authority.",
    "Implementation details live in the service repositories and are not repeated here.",
    "Questions about this decision go to the Design Authority agenda.",
]


def adr(a: dict) -> str:
    d = dt.date.fromisoformat(a["date"])
    deciders = ", ".join(f"{W.name_of(p, d)} ({W.title_of(p, d)})" for p in a["deciders"])
    forum = W.committees[a["forum"]]["name"] if a.get("forum") in W.committees else a.get("forum", "")
    sup = ", ".join(a["supersedes"]) if a["supersedes"] else "none"
    supby = a["superseded_by"] or "none"
    ctx, dec = ADR_TEXT[a["id"]]
    r = rng(f"adr:{a['id']}")
    num = a["id"].split("-")[1]
    lines = [
        f"# {a['id']}: {a['title']}",
        "",
        f"- Status: {STATUS_LABEL[a['status']]}",
        f"- Date: {a['date']}",
        f"- Deciders: {deciders}",
        f"- Forum: {forum}",
        f"- Supersedes: {sup}",
        f"- Superseded by: {supby}",
        "",
        "## Context",
        "",
        ctx,
        "",
        "## Decision",
        "",
        dec,
        "",
        "## Consequences",
        "",
        a["consequences"],
        "",
    ]
    if a["status"] == "superseded":
        lines += [f"> This record is superseded by {a['superseded_by']} and is kept for history.", ""]
    elif a["status"] == "deprecated":
        lines += [f"> Deprecated; see {a['superseded_by']}.", ""]
    elif a["status"] == "proposed":
        lines += ["> Proposed: not yet agreed by the Design Authority.", ""]
    lines += ["## Notes", "", r.choice(FOLLOW_UP), ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------
# Diagrams (Mermaid)
# ---------------------------------------------------------------------------------------------

def mid(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name)


def event_flows() -> str:
    lines = [
        "# Claims Hub event flows",
        "",
        "Producers and consumers of the Claims Hub Kafka topics on the Event Streaming Platform",
        "(cluster `esp-prd`). Each arrow is labelled with the topic it carries.",
        "",
        "```mermaid",
        "flowchart LR",
    ]
    nodes = []
    for n in ORDER:
        nodes.append(f'    {mid(n)}["{n}"]')
    externals = set()
    edges = []
    for t in W.topics.values():
        if t["name"] == FRAUD_NOTICE_TOPIC:
            continue
        prod = t["producer"]
        for c in t["consumers"]:
            for x in (prod, c):
                if x not in SVC:
                    externals.add(x)
            edges.append(f"    {mid(prod)} -->|{t['name']}| {mid(c)}")
    for x in sorted(externals):
        nodes.append(f'    {mid(x)}(["{x}"])')
    lines += nodes + edges + ["```", ""]
    lines += [
        "Notes:",
        "",
        "- `claims.reserve.movement.v1` is published by the MQ-to-Kafka bridge CLX-IF-049 from the CLARA",
        "  CLX-IF-042 extract (ADR-012).",
        "- `reserve.changed.v2` replaced v1 when reserve-svc was renamed to reserve-engine (ADR-019).",
        "",
    ]
    return "\n".join(lines)


def sequences() -> str:
    return T("""
        # Sequence diagrams

        ## Reserve movement synchronisation (CLARA to Claims Hub)

        ```mermaid
        sequenceDiagram
            participant RS as CLARA CLRRS170
            participant MQ as MQ queue CLR.RSVMOVE.OUT
            participant BR as Bridge CLX-IF-049
            participant K as Kafka claims.reserve.movement.v1
            participant RE as reserve-engine
            participant GL as gl-posting-svc
            participant LED as Group Ledger
            RS->>MQ: MQPUT RSVMOVE records (CLX-IF-042)
            RS->>RS: set EXTRACTED_FLAG = 'Y' on CLR.T_RESERVE_MOVEMENT
            BR->>MQ: daily 02:45 read RSVMOVE records
            BR->>K: publish Avro schema v3, key claim_id
            K->>RE: consume for parallel run and Wave 2 sync
            RE->>GL: reserve.changed.v2
            GL->>LED: journals posted hourly (CLX-IF-050)
        ```

        ## Fraud referral and customer notice

        ```mermaid
        sequenceDiagram
            participant TR as triage-svc
            participant SN as Sentinel
            participant FR as fraud-referral-svc
            participant SIU as SIU Case Manager
            participant NS as notification-svc
            participant NT as Notify
            TR->>SN: score claim over REST, timeout 800 ms (CLX-IF-036)
            SN-->>TR: Sentinel score
            TR->>FR: fraud.score.received.v1
            FR->>FR: refer if score >= 65; Tier-3 claims >= 60 from 2026-10-01
            FR->>SIU: create SIU referral (CLX-IF-041)
            FR->>NS: fraud.referral.notice-due.v1
            NS->>NS: due date = referral date + 10 business days
            NS->>NT: send notice FRN01 (letter) or FRN02 (SMS)
        ```
    """)


# ---------------------------------------------------------------------------------------------
# Diagrams (PNG)
# ---------------------------------------------------------------------------------------------

INK = (20, 24, 32)
BOX = (232, 240, 250)
EDGE = (40, 70, 120)


def _canvas(w, h):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (w, h), (255, 255, 255))
    return img, ImageDraw.Draw(img)


def _box(d, xy, text_lines, f, fill=BOX):
    x0, y0, x1, y1 = xy
    d.rectangle(xy, fill=fill, outline=EDGE, width=3)
    asc, desc = f.getmetrics()
    lh = asc + desc + 6
    y = y0 + (y1 - y0 - lh * len(text_lines) + 6) // 2
    for t in text_lines:
        w = d.textlength(t, font=f)
        d.text((x0 + (x1 - x0 - w) / 2, y), t, fill=INK, font=f)
        y += lh


def _arrow(d, p0, p1, label=None, f=None, label_at=None):
    d.line([p0, p1], fill=EDGE, width=4)
    import math
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (-0.45, 0.45):
        d.line([p1, (p1[0] - 20 * math.cos(ang + s), p1[1] - 20 * math.sin(ang + s))], fill=EDGE, width=4)
    if label and f:
        lx, ly = label_at or ((p0[0] + p1[0]) // 2, (p0[1] + p1[1]) // 2)
        bb = f.getbbox(label)
        wv, hv = bb[2] - bb[0], bb[3] - bb[1]
        d.rectangle([lx - wv // 2 - 6, ly - hv // 2 - 6, lx + wv // 2 + 6, ly + hv // 2 + 6], fill=(255, 255, 255))
        d.text((lx - wv // 2, ly - hv // 2 - bb[1]), label, fill=INK, font=f)


def _png(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def png_reserve_sync() -> bytes:
    img, d = _canvas(1900, 760)
    fb, f, fs = util.font(34, bold=True), util.font(28), util.font(24)
    d.text((40, 30), "Reserve movement synchronisation", fill=INK, font=fb)
    boxes = [
        ((40, 160, 330, 300), ["CLARA", "CLRRS170"]),
        ((420, 160, 760, 300), ["MQ queue", "CLR.RSVMOVE.OUT"]),
        ((850, 160, 1170, 300), ["Bridge", "CLX-IF-049"]),
        ((1260, 160, 1860, 300), ["Kafka topic", "claims.reserve.movement.v1"]),
        ((1260, 460, 1860, 600), ["reserve-engine"]),
        ((420, 460, 760, 600), ["gl-posting-svc"]),
        ((40, 460, 330, 600), ["Group Ledger"]),
    ]
    for xy, t in boxes:
        _box(d, xy, t, f)
    _arrow(d, (330, 230), (420, 230))
    _arrow(d, (760, 230), (850, 230))
    _arrow(d, (1170, 230), (1260, 230))
    _arrow(d, (1560, 300), (1560, 460))
    _arrow(d, (1260, 530), (760, 530), "reserve.changed.v2", fs, label_at=(1010, 490))
    _arrow(d, (420, 530), (330, 530), None)
    d.text((850, 330), "daily 02:45", fill=INK, font=f)
    d.text((40, 660), "Journals to Group Ledger: hourly (CLX-IF-050)", fill=INK, font=f)
    return _png(img)


def png_namespaces() -> bytes:
    ns = namespaces()
    cols, bw, bh, gap = 3, 590, 200, 40
    rows = (len(ns) + cols - 1) // cols
    img, d = _canvas(cols * bw + (cols + 1) * gap, rows * bh + (rows + 1) * gap + 120)
    fb, f = util.font(34, bold=True), util.font(28)
    d.text((gap, 30), "Claims Hub namespaces on ocp-prd-lon1", fill=INK, font=fb)
    for i, (name, svcs) in enumerate(ns.items()):
        r, c = divmod(i, cols)
        x0 = gap + c * (bw + gap)
        y0 = 120 + gap + r * (bh + gap)
        lines = [name] + [f"{s} x{SVC[s]['replicas']}" for s in svcs]
        _box(d, (x0, y0, x0 + bw, y0 + bh), lines, f)
    return _png(img)


def png_context() -> bytes:
    img, d = _canvas(1900, 1100)
    fb, f, fs = util.font(34, bold=True), util.font(28), util.font(24)
    d.text((40, 30), "Claims Hub system context", fill=INK, font=fb)
    hub = (700, 420, 1200, 640)
    _box(d, hub, ["Claims Hub", "13 services on OpenShift"], f, fill=(220, 236, 220))
    ext = {
        "Sentinel": (80, 140, 480, 260),
        "SIU Case Manager": (750, 120, 1150, 240),
        "Notify": (1420, 140, 1820, 260),
        "Corvane Payments Gateway": (1360, 470, 1860, 590),
        "Group Ledger": (1420, 820, 1820, 940),
        "Evidence Vault": (750, 840, 1150, 960),
        "PALM": (80, 820, 480, 940),
        "CLARA": (60, 470, 460, 590),
    }
    for k, xy in ext.items():
        _box(d, xy, [k], f)
    _arrow(d, (760, 420), (420, 260), "CLX-IF-036", fs, label_at=(560, 330))
    _arrow(d, (950, 420), (950, 240), "CLX-IF-041", fs, label_at=(1060, 330))
    _arrow(d, (1140, 420), (1480, 260), "CLX-IF-037", fs, label_at=(1350, 330))
    _arrow(d, (1200, 530), (1360, 530), "CLX-IF-038", fs, label_at=(1280, 490))
    _arrow(d, (1140, 640), (1480, 820), "CLX-IF-050", fs, label_at=(1350, 740))
    _arrow(d, (950, 640), (950, 840), "CLX-IF-039", fs, label_at=(1060, 740))
    _arrow(d, (420, 820), (760, 640), "CLX-IF-054", fs, label_at=(560, 740))
    _arrow(d, (460, 530), (700, 530), "CLX-IF-049", fs, label_at=(580, 490))
    return _png(img)


# ---------------------------------------------------------------------------------------------

def build(repo):
    p = repo.add("README.md", root_readme(), "F-01", author="P053")
    root_readme_mods(repo, p.path)
    repo.add(".gitignore", GITIGNORE.lstrip("\n"), "F-01", author="P053")
    p = repo.add("Makefile", makefile(), "F-01", author="P053")
    repo.modify(p.path, "CM-04", f" {OLD_RESERVE} \\", f" {NEW_RESERVE} \\")

    p = repo.add(".github/CODEOWNERS", codeowners("a"), "F-02", author="P018")
    owners = repo.files[p.path].content
    line_new = next(l for l in owners.splitlines() if l.startswith(f"/services/{NEW_RESERVE}/"))
    line_old = line_new.replace(f"/services/{NEW_RESERVE}/", f"/services/{OLD_RESERVE}/").replace(
        f"{OLD_RESERVE}/ ", f"{OLD_RESERVE}/    ", 1)
    repo.modify(p.path, "CM-04", line_old + "\n", line_new + "\n")
    repo.c_overrides[".github/CODEOWNERS"] = codeowners("c")

    for a in sorted(W.adrs.values(), key=lambda a: a["id"]):
        num = int(a["id"].split("-")[1])
        repo.add(f"docs/adr/adr-{num:03d}.md", adr(a), "F-22", author="P018")

    repo.add("docs/diagrams/event-flows.md", event_flows(), "F-23", author="P049")
    repo.add("docs/diagrams/sequences.md", sequences(), "F-23", author="P049")
    repo.add("docs/diagrams/system-context.png", png_context(), "F-23", binary=True, author="P049")
    repo.add("docs/diagrams/namespaces.png", png_namespaces(), "F-23", binary=True, author="P049")
    repo.add("docs/diagrams/reserve-sync.png", png_reserve_sync(), "F-23", binary=True, author="P049")
