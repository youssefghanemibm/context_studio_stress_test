"""YAML / YML files ST043-ST052."""
from __future__ import annotations

import pathlib

import yaml

from generators.common import util

from .core import (W, Built, Facts, DOC_PREFIX, fauthor, fdate, fstatus, ftitle, may, need, pname, ptitle, pemail,
                   rule_params_ok, rule_text_ok, rule_ver, svcname, sysname, team_name, version_history)
from . import phrases
from .json_specs import svc_owner, svc_topics, topics_as_of, TOPIC_IFACE, topic_owner_team


class _Dumper(yaml.SafeDumper):
    pass


def _str_repr(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str_repr)
_Dumper.ignore_aliases = lambda self, data: True


def ydump(obj) -> str:
    return yaml.dump(obj, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=110, default_flow_style=False)


def ydump_all(objs) -> str:
    return yaml.dump_all(objs, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=110,
                         default_flow_style=False, explicit_start=True)


def yloc(path: str, doc_index: int | None = None) -> dict:
    loc = {"kind": "yaml_path", "path": path}
    if doc_index is not None:
        loc["doc_index"] = doc_index
    return loc


def header(fid: str, extra: list[str] | None = None) -> str:
    on = fdate(fid)
    a = fauthor(fid)
    hist = version_history(fid, [a])
    lines = [f"# Corvane Mutual – {ftitle(fid)}",
             f"# Document {DOC_PREFIX[fid]} version {hist[-1]['version']} ({fstatus(fid)}), {on}",
             f"# Owner: {pname(a, on)}, {ptitle(a, on)}",
             "# Classification: Internal – Programme Skerry",
             "# Change history:"]
    for h in hist:
        lines.append(f"#   {h['version']:<4} {h['date']}  {h['author']}: {h['change']}")
    for e in extra or []:
        lines.append(f"# {e}")
    return "\n".join(lines) + "\n"


def doc_meta(fid: str, approvers: list[str]) -> dict:
    on = fdate(fid)
    a = fauthor(fid)
    hist = version_history(fid, [a])
    return {"documentId": DOC_PREFIX[fid], "version": hist[-1]["version"], "status": fstatus(fid), "date": on,
            "owner": pname(a, on), "approvers": [f"{pname(p, on)} ({ptitle(p, on)})" for p in approvers]}


def problem_schema() -> dict:
    return {"type": "object", "description": "RFC 7807 problem details with a stable error code.",
            "required": ["type", "title", "status", "code"],
            "properties": {"type": {"type": "string", "format": "uri"}, "title": {"type": "string"},
                           "status": {"type": "integer"}, "detail": {"type": "string"},
                           "code": {"type": "string", "example": "CHUB-VAL-001"},
                           "correlationId": {"type": "string"}}}


def std_responses(extra: dict | None = None) -> dict:
    base = {
        "400": {"description": "Request failed validation.", "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/Problem"}}}},
        "401": {"description": "Missing or invalid CIS token."},
        "403": {"description": "Caller lacks the required scope or authority."},
        "404": {"description": "Resource not found.", "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/Problem"}}}},
        "500": {"description": "Unexpected error.", "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/Problem"}}}},
    }
    if extra:
        base.update(extra)
    return dict(sorted(base.items()))


COMMON_PARAMS = {
    "CorrelationId": {"name": "X-Correlation-Id", "in": "header", "required": True, "schema": {"type": "string"},
                      "description": "Correlation identifier, echoed in the response and in logs."},
    "IdempotencyKey": {"name": "Idempotency-Key", "in": "header", "required": True, "schema": {"type": "string"},
                       "description": "Client-generated key; repeating a request with the same key returns the original result."},
}


def money() -> dict:
    return {"type": "object", "required": ["amountMinor", "currency"],
            "properties": {"amountMinor": {"type": "integer", "format": "int64", "description": "Amount in minor units (pence/øre)."},
                           "currency": {"type": "string", "enum": ["GBP", "NOK", "SEK", "DKK"]}}}


_DATE_RX = __import__("re").compile(r"20\d\d-\d\d-\d\d")


def data_model(svc: str, on: str) -> list[dict]:
    """The service's PostgreSQL tables as of a date (column descriptions that mention a later date are dropped)."""
    out = []
    for t in W.services[svc].get("postgres_tables", []):
        tb = W.tables[t]
        cols = []
        for c in tb["columns"]:
            col = {"name": c["name"], "type": c["type"] + (f"({c['length']})" if c.get("length") and c["type"] in ("VARCHAR", "CHAR") else ""),
                   "nullable": c["nullable"]}
            desc = c.get("description") or ""
            if desc and "SMS" not in desc and all(x <= on for x in _DATE_RX.findall(desc)):
                col["description"] = desc
            if c["name"] in tb.get("primary_key", []):
                col["primaryKey"] = True
            cols.append(col)
        out.append({"table": t, "database": tb.get("database"), "columns": cols})
    return out


def api_consumers(svc: str, on: str) -> list[dict]:
    out = []
    for i in W.interfaces.values():
        if svc in i["services"] and str(i["since"]) <= on:
            out.append({"interface": i["id"], "name": i["name"], "protocol": i["protocol"],
                        "from": sysname(i["source_system"], on), "to": sysname(i["target_system"], on)})
    return out


def shared_components() -> tuple[dict, dict]:
    headers = {
        "X-Correlation-Id": {"description": "Echo of the request correlation identifier.", "schema": {"type": "string"}},
        "Retry-After": {"description": "Seconds to wait before retrying.", "schema": {"type": "integer"}},
        "Location": {"description": "URI of the created resource.", "schema": {"type": "string", "format": "uri"}},
    }
    responses = {
        "TooManyRequests": {"description": "Client rate limit reached; retry after the indicated delay.",
                            "headers": {"Retry-After": {"$ref": "#/components/headers/Retry-After"},
                                        "X-Correlation-Id": {"$ref": "#/components/headers/X-Correlation-Id"}},
                            "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/Problem"}}}},
        "ServiceUnavailable": {"description": "The service is temporarily unavailable (for example during a rolling deployment).",
                               "headers": {"Retry-After": {"$ref": "#/components/headers/Retry-After"}},
                               "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/Problem"}}}},
    }
    return headers, responses


def problem_examples(prefix: str, codes: list[tuple[str, str]], on: str) -> dict:
    status = {"VAL": 400, "AUT": 409, "BUS": 422, "SYS": 500}
    out = {}
    for k, (c, m) in enumerate(codes, 1):
        kind = c.split("-")[1]
        st = status.get(kind, 400)
        out[f"{prefix}{c.replace('-', '')}"] = {
            "summary": f"{c}: {m}",
            "value": {"type": f"https://errors.corvane.internal/{c.lower()}", "title": m[0].upper() + m[1:],
                      "status": st, "code": c, "detail": m[0].upper() + m[1:] + ".",
                      "correlationId": f"req-{on.replace('-', '')}-{k:04d}"}}
    return out


# ---------------------------------------------------------------------------------------------
# ST043 OpenAPI reserve-svc (pre-rename)
# ---------------------------------------------------------------------------------------------

RSV_ERROR_CODES = [
    ("RSV-VAL-001", "claimId does not match the claim reference format"),
    ("RSV-VAL-004", "currency does not match the reserve currency"),
    ("RSV-AUT-010", "amount exceeds the caller's reserve authority (BR-RSV-003 v3)"),
    ("RSV-BUS-020", "movement would make the outstanding reserve negative"),
    ("RSV-BUS-021", "claim is closed; reopen before posting a movement (BR-RSV-017)"),
    ("RSV-SYS-500", "unexpected error; retry with the same Idempotency-Key"),
]


def st43_examples(r, fid: str, spec: dict, on: str, rsv3: dict, llnt: dict, cfg_t3: int) -> None:
    """Examples, shared components, data model and consumers for the reserve API (as of 2025-12-01)."""
    import datetime as _dt
    from .json_specs import claim_ref
    used: set = set()
    hdrs, resps = shared_components()
    comp = spec["components"]
    comp["headers"] = hdrs
    comp["responses"] = resps
    d0 = _dt.date.fromisoformat(on)

    def ts(days_back: int, hh: int, mm: int) -> str:
        return f"{(d0 - _dt.timedelta(days=days_back)).isoformat()}T{hh:02d}:{mm:02d}:00Z"

    uk = claim_ref(r, "UK", 2025, used)
    se = claim_ref(r, "SE", 2025, used)
    no = claim_ref(r, "NO", 2025, used)
    last = r.randint(3, 9)

    def authority(gbp_minor: int) -> str:
        gbp = gbp_minor // 100
        for lvl, key in (("CLAIMS_HANDLER", "claims_handler"), ("TEAM_LEADER", "team_leader"),
                         ("CLAIMS_MANAGER", "claims_manager"), ("CLAIMS_DIRECTOR", "claims_director")):
            if gbp <= rsv3[key]:
                return lvl
        return "RESERVING_COMMITTEE"

    ind = r.randint(62, 140) * 100000
    leg = r.randint(8, 24) * 100000
    se_gbp = r.randint(18, 40) * 100000
    se_sek = se_gbp * 135 // 10
    exs = {
        "ReserveTier3UKMotor": {"summary": "Tier-3 UK motor claim with indemnity and legal reserves", "value": {
            "claimId": uk, "tier": "Tier-3", "source": "CLAIMS_HUB",
            "nextReviewDate": (d0 - _dt.timedelta(days=last) + _dt.timedelta(days=cfg_t3)).isoformat(),
            "lines": [
                {"reserveType": "INDEMNITY", "outstanding": {"amountMinor": ind, "currency": "GBP"},
                 "paidToDate": {"amountMinor": r.randint(5, 30) * 100000, "currency": "GBP"},
                 "authorityLevel": authority(ind), "lastChangedAt": ts(last, 10, 12)},
                {"reserveType": "LEGAL", "outstanding": {"amountMinor": leg, "currency": "GBP"},
                 "paidToDate": {"amountMinor": 0, "currency": "GBP"}, "authorityLevel": authority(leg),
                 "lastChangedAt": ts(last, 10, 14)}]}},
        "ReserveTier2HomeSE": {"summary": "Tier-2 Swedish home claim in SEK with GBP equivalent", "value": {
            "claimId": se, "tier": "Tier-2", "source": "CLARA_BRIDGE",
            "lines": [{"reserveType": "INDEMNITY", "outstanding": {"amountMinor": se_sek, "currency": "SEK"},
                       "paidToDate": {"amountMinor": r.randint(3, 8) * 1000000, "currency": "SEK"},
                       "gbpEquivalent": {"amountMinor": se_gbp, "currency": "GBP"},
                       "authorityLevel": authority(se_gbp), "lastChangedAt": ts(r.randint(10, 20), 8, 41)}]}},
    }
    adj = r.randint(15, 90) * 10000
    exs["MovementAdjustmentGBP"] = {"summary": "Adjustment within Claims Handler authority", "value": {
        "movementId": "6b1f0c52-3d7e-4a19-9c2b-5e8d7a40f%03d" % r.randint(100, 999), "claimId": uk, "movementType": "AD",
        "amount": {"amountMinor": adj, "currency": "GBP"}, "gbpAmount": {"amountMinor": adj, "currency": "GBP"},
        "createdAt": ts(1, 14, 3), "createdBy": "handler.uk.%04d" % r.randint(1000, 9999), "largeLoss": False}}
    big_gbp = llnt["threshold_gbp"] + r.randint(20, 80) * 1000
    exs["MovementLargeLossNOK"] = {"summary": "Initial reserve above the large loss threshold (Reinsurance notified)", "value": {
        "movementId": "0d4e8a71-92c3-4f60-8b15-27c9e1a3b%03d" % r.randint(100, 999), "claimId": no, "movementType": "IN",
        "amount": {"amountMinor": big_gbp * 1350, "currency": "NOK"}, "gbpAmount": {"amountMinor": big_gbp * 100, "currency": "GBP"},
        "createdAt": ts(2, 9, 27), "createdBy": "handler.no.%04d" % r.randint(1000, 9999), "largeLoss": True}}
    items = []
    for k, mt in enumerate(["IN", "AD", "AD", "RV", "RC"]):
        amt = r.randint(2, 40) * 50000 * (-1 if mt == "RC" else 1)
        items.append({"movementId": "9a7c%04d-1e2f-4b3a-8c5d-6e7f8091a2b3" % r.randint(1000, 9999), "claimId": uk,
                      "movementType": mt, "amount": {"amountMinor": amt, "currency": "GBP"},
                      "gbpAmount": {"amountMinor": amt, "currency": "GBP"}, "createdAt": ts(60 - k * 11, 11, 5 + k),
                      "createdBy": "handler.uk.%04d" % r.randint(1000, 9999), "largeLoss": False})
    exs["MovementHistoryPage"] = {"summary": "First page of a claim's movement history (newest first)",
                                  "value": {"items": list(reversed(items)), "nextCursor": "eyJwIjoyfQ"}}
    exs.update(problem_examples("Problem", [(e["code"], e["meaning"]) for e in spec["x-error-codes"]], on))
    comp["examples"] = exs
    spec["x-data-model"] = {"note": "Persistence owned by the service (PostgreSQL); not exposed directly to consumers.",
                            "tables": data_model("reserve-engine", on)}
    cons = api_consumers("reserve-engine", on)
    if cons:
        spec["x-consumers"] = cons
    spec["x-guidelines"] = r.sample(phrases.BANKS["design"], 4) + r.sample(phrases.BANKS["api"], 3)


def build_ST043(out_dir: pathlib.Path) -> Built:
    fid = "ST043"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:openapi")
    name = svcname("reserve-engine", on)
    assert name == "reserve-svc"
    s = W.services["reserve-engine"]
    cfg_t3 = 21  # config_history: tier3-review-days 21 until 2026-07-02
    assert any(h["key"] == "tier3-review-days" and h["value"] == cfg_t3 and h["to"] > on for h in s["config"]["config_history"])
    rsv3 = rule_params_ok(fid, "BR-RSV-003", 3)
    rsv7 = W.rule_version("BR-RSV-007", on)
    llnt = rule_params_ok(fid, "BR-RSV-011", 2)
    apis = [a for a in s["apis"] if a["path"] != "/revaluation-runs"]  # revaluation run decided 2026-03 (ADR-028)
    move_types = {"IN": "initial", "AD": "adjustment", "IX": "indexation", "RV": "review", "ST": "settlement close",
                  "RC": "recovery"}
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": f"{name} API",
            "version": "1.4",
            "description": (f"Case reserves and reserve movements for Claims Hub ({name}). Replaces the CLARA reserve "
                            "programs as they are migrated. Movements are authority-checked against BR-RSV-003 v3. "
                            + phrases.paragraph(r, "api", 2)),
            "contact": {"name": pname("P041", on), "email": pemail("P041", on)},
            "x-owner-team": team_name("T28", on),
            "x-document-control": doc_meta(fid, ["P049", "P018"]),
        },
        "servers": [{"url": f"https://{name}.apps.ocp-prd-lon1.corvane.internal/v1", "description": "Production"},
                    {"url": f"https://{name}.apps.ocp-pre-lon1.corvane.internal/v1", "description": "Pre-production"}],
        "security": [{"cis": ["reserve.read"]}],
        "tags": [{"name": "reserves", "description": "Current reserves per claim"},
                 {"name": "movements", "description": "Reserve movements and history"}],
        "paths": {},
        "components": {
            "parameters": {
                "ClaimId": {"name": "claimId", "in": "path", "required": True,
                            "schema": {"type": "string", "pattern": "^CLM-(UK|NO|SE|DK)-\\d{4}-\\d{6}$"},
                            "description": "Claim reference, e.g. CLM-UK-2025-318204."},
                **COMMON_PARAMS,
            },
            "schemas": {
                "Money": money(),
                "Reserve": {"type": "object", "required": ["claimId", "lines"],
                            "properties": {"claimId": {"type": "string"}, "tier": {"type": "string", "enum": ["Tier-1", "Tier-2", "Tier-3"],
                                                                                   "description": "Tier per BR-TRI-003 v3."},
                                           "lines": {"type": "array", "items": {"$ref": "#/components/schemas/ReserveLine"}},
                                           "nextReviewDate": {"type": "string", "format": "date",
                                                              "description": f"Tier-3 reserves are reviewed every {rsv7['parameters']['review_days']} days (BR-RSV-007 v{rsv7['version']}; config tier3-review-days={cfg_t3})."},
                                           "source": {"type": "string", "enum": ["CLAIMS_HUB", "CLARA_BRIDGE"]}}},
                "ReserveLine": {"type": "object",
                                "properties": {"reserveType": {"type": "string", "description": "Reserve type code (indemnity, expense, legal, recovery estimate)."},
                                               "outstanding": {"$ref": "#/components/schemas/Money"},
                                               "paidToDate": {"$ref": "#/components/schemas/Money"},
                                               "gbpEquivalent": {"$ref": "#/components/schemas/Money"},
                                               "authorityLevel": {"$ref": "#/components/schemas/AuthorityLevel"},
                                               "lastChangedAt": {"type": "string", "format": "date-time"}}},
                "AuthorityLevel": {"type": "string",
                                   "enum": ["CLAIMS_HANDLER", "TEAM_LEADER", "CLAIMS_MANAGER", "CLAIMS_DIRECTOR", "RESERVING_COMMITTEE"],
                                   "description": (f"Reserve authority (BR-RSV-003 v3): Claims Handler £{rsv3['claims_handler']:,}; "
                                                   f"Team Leader £{rsv3['team_leader']:,}; Claims Manager £{rsv3['claims_manager']:,}; "
                                                   f"Claims Director £{rsv3['claims_director']:,}; above that the Reserving Committee.")},
                "MovementType": {"type": "string", "enum": list(move_types),
                                 "description": "; ".join(f"{k} {v}" for k, v in move_types.items()) + " (CLR.T_RESERVE_MOVEMENT.MOVE_TYPE_CD)."},
                "MovementRequest": {"type": "object", "required": ["reserveType", "movementType", "amount", "reasonCode"],
                                    "properties": {"reserveType": {"type": "string"},
                                                   "movementType": {"$ref": "#/components/schemas/MovementType"},
                                                   "amount": {"$ref": "#/components/schemas/Money"},
                                                   "reasonCode": {"type": "string", "description": "Reason code from code list RSNC (BR-RSV-015)."},
                                                   "comment": {"type": "string", "maxLength": 500}}},
                "Movement": {"type": "object",
                             "properties": {"movementId": {"type": "string", "format": "uuid"}, "claimId": {"type": "string"},
                                            "movementType": {"$ref": "#/components/schemas/MovementType"},
                                            "amount": {"$ref": "#/components/schemas/Money"},
                                            "gbpAmount": {"$ref": "#/components/schemas/Money"},
                                            "createdAt": {"type": "string", "format": "date-time"},
                                            "createdBy": {"type": "string"},
                                            "largeLoss": {"type": "boolean",
                                                          "description": f"True when the GBP movement exceeds £{llnt['threshold_gbp']:,} (BR-RSV-011 v2); Reinsurance is notified within {llnt['notify_hours']} hours."}}},
                "MovementPage": {"type": "object", "properties": {"items": {"type": "array", "items": {"$ref": "#/components/schemas/Movement"}},
                                                                  "nextCursor": {"type": "string"}}},
                "Problem": problem_schema(),
            },
            "securitySchemes": {"cis": {"type": "oauth2", "flows": {"clientCredentials": {
                "tokenUrl": "https://cis.corvane.internal/oauth2/token",
                "scopes": {"reserve.read": "Read reserves", "reserve.write": "Post reserve movements"}}}}},
        },
        "x-events": {"produces": ["reserve.changed.v1"], "consumes": ["triage.completed.v1"],
                     "note": "Events are published after commit (outbox)."},
        "x-replaces-programs": [p for p in s["replaces_programs"] if p != "CLRGL090"],
        "x-error-codes": [{"code": c, "meaning": m} for c, m in RSV_ERROR_CODES],
        "x-changelog": [{"version": v, "date": d_, "change": c} for v, d_, c in [
            ("1.0", "2025-07-14", "First contract for the reserve and movement API (CHUB-193)"),
            ("1.1", "2025-08-26", "Added reserve history paging"),
            ("1.2", "2025-09-22", "Authority levels aligned with BR-RSV-003 v3"),
            ("1.3", "2025-10-30", "Large loss flag on movements (BR-RSV-011 v2)"),
            ("1.4", "2025-12-01", "Problem details error format; approved for build")]],
    }
    st43_examples(r, fid, spec, on, rsv3, llnt, cfg_t3)
    for a in apis:
        op = {"summary": a["summary"], "operationId": a["summary"].split(" (")[0].title().replace(" ", "").replace("-", ""),
              "tags": ["movements" if "movement" in a["path"] or "history" in a["path"] else "reserves"],
              "parameters": [{"$ref": "#/components/parameters/ClaimId"}, {"$ref": "#/components/parameters/CorrelationId"}]}
        if a["method"] == "POST":
            op["parameters"].append({"$ref": "#/components/parameters/IdempotencyKey"})
            op["security"] = [{"cis": ["reserve.write"]}]
            op["requestBody"] = {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MovementRequest"},
                                                                                    "example": {"reserveType": "INDEMNITY", "movementType": "AD",
                                                                                                "amount": {"amountMinor": 1250000, "currency": "GBP"},
                                                                                                "reasonCode": "EST1"}}}}
            op["responses"] = std_responses({"201": {"description": "Movement recorded.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Movement"}}}},
                                             "409": {"description": "Amount exceeds the caller's authority; routed for approval (BR-RSV-003 v3)."},
                                             "422": {"description": "Movement would make the outstanding reserve negative."}})
        elif "history" in a["path"]:
            op["parameters"] += [{"name": "cursor", "in": "query", "schema": {"type": "string"}},
                                 {"name": "limit", "in": "query", "schema": {"type": "integer", "maximum": 200}}]
            op["responses"] = std_responses({"200": {"description": "Movement history, newest first.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MovementPage"}}}}})
        else:
            op["responses"] = std_responses({"200": {"description": "Current reserves.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Reserve"}}}}})
        op["responses"]["429"] = {"$ref": "#/components/responses/TooManyRequests"}
        op["responses"]["503"] = {"$ref": "#/components/responses/ServiceUnavailable"}
        ex = {"POST": {"201": ["MovementAdjustmentGBP", "MovementLargeLossNOK"]},
              "GET": {"200": ["ReserveTier3UKMotor", "ReserveTier2HomeSE"] if "history" not in a["path"] else ["MovementHistoryPage"]}}
        for code, names in ex[a["method"]].items():
            if code in op["responses"] and "content" in op["responses"][code]:
                op["responses"][code]["content"]["application/json"]["examples"] = {
                    n: {"$ref": f"#/components/examples/{n}"} for n in names}
        if a["method"] == "POST":
            op["responses"]["201"]["headers"] = {"Location": {"$ref": "#/components/headers/Location"},
                                                 "X-Correlation-Id": {"$ref": "#/components/headers/X-Correlation-Id"}}
        op["responses"] = dict(sorted(op["responses"].items()))
        spec["paths"].setdefault(a["path"], {})[a["method"].lower()] = op
    text = header(fid, [f"Service {name}, namespace {s['k8s_namespace']}, repository path services/{name}."]) + ydump(spec)
    F.add("contradiction_old", "OpenAPI info.title 'reserve-svc API' (version 1.4, 2025-12-01).",
          yloc("info.title"), "reserve-svc API", world_ref="SERVICE:reserve-engine#renames", placement="PL-178",
          notes="C09: the same service is reserve-engine in ST049 (renamed 2026-02-10).")
    F.add("general", "reserve-svc API version is 1.4.", yloc("info.version"), "1.4", world_ref="SERVICE:reserve-engine#apis")
    F.add("temporal", "In the reserve-svc API (2025-12-01) Tier-3 reserves are reviewed every 21 days (BR-RSV-007 v2).",
          yloc("components.schemas.Reserve.properties.nextReviewDate.description"), "reviewed every 21 days (BR-RSV-007 v2",
          world_ref="RULE:BR-RSV-007@v2#parameters.review_days")
    F.add("general", "Reserve authority limits (BR-RSV-003 v3): Claims Handler £25,000; Team Leader £100,000; Claims Manager £500,000; Claims Director £2,000,000.",
          yloc("components.schemas.AuthorityLevel.description"), "Team Leader £100,000", world_ref="RULE:BR-RSV-003@v3")
    F.add("general", "POST /reserves/{claimId}/movements is authority-checked against BR-RSV-003.",
          yloc('paths."/reserves/{claimId}/movements".post.summary'), "authority checked against BR-RSV-003",
          world_ref="SERVICE:reserve-engine#apis")
    F.add("general", "Large reserve movements above £250,000 are flagged and notified to Reinsurance within 24 hours (BR-RSV-011 v2).",
          yloc("components.schemas.Movement.properties.largeLoss.description"), "£250,000 (BR-RSV-011 v2)",
          world_ref="RULE:BR-RSV-011@v2#parameters.threshold_gbp")
    F.add("general", "reserve-svc keeps Tier-3 review dates in PostgreSQL table reserve.review_schedule (database chub_reserve).",
          yloc("x-data-model.tables[2]"), "table: reserve.review_schedule database: chub_reserve",
          world_ref="TABLE:reserve.review_schedule")
    return Built(fid, text.encode("utf-8"), F.items, f"{len(spec['paths'])} rows")


# ---------------------------------------------------------------------------------------------
# ST044 OpenAPI fraud-referral-svc
# ---------------------------------------------------------------------------------------------

def st44_examples(r, fid: str, spec: dict, on: str, cfg: dict, v36: dict) -> None:
    """Examples, shared components, data model and consumers for the fraud referral API (as of 2026-09-29)."""
    import datetime as _dt
    from .core import add_business_days
    from .json_specs import claim_ref
    used: set = set()
    hdrs, resps = shared_components()
    comp = spec["components"]
    comp["headers"] = hdrs
    comp["responses"] = resps
    d0 = _dt.date.fromisoformat(on)
    default = cfg["referral.threshold.default"]

    def wd(days_back: int) -> _dt.date:
        x = d0 - _dt.timedelta(days=days_back)
        while x.weekday() >= 5:
            x -= _dt.timedelta(days=1)
        return x

    def rid() -> str:
        return f"FRF-2026-{r.randint(10000, 99999):05d}"

    c1, c2, c3, c4 = (claim_ref(r, "UK", 2026, used), claim_ref(r, "UK", 2026, used),
                      claim_ref(r, "NO", 2026, used), claim_ref(r, "UK", 2026, used))
    s1 = r.randint(default + 2, 88)
    s2 = r.randint(30, default - 12)
    rd1, rd2, rd3 = wd(r.randint(2, 6)), wd(r.randint(9, 16)), wd(r.randint(40, 70))
    exs = {
        "ScoreReferralTier2": {"summary": "Score-based referral at or above the general threshold", "value": {
            "claimId": c1, "score": s1, "tier": "Tier-2", "source": "SCORE"}},
        "HandlerReferral": {"summary": "Handler referral below the score threshold, with indicators", "value": {
            "claimId": c2, "score": s2, "tier": "Tier-1", "source": "HANDLER",
            "indicators": ["BR-FRD-001", "BR-FRD-002"]}},
        "ReferralCreated": {"summary": "Referral created from a score above the threshold", "value": {
            "referralId": rid(), "claimId": c1, "referralDate": rd1.isoformat(), "score": s1, "tier": "Tier-2",
            "thresholdApplied": default, "siuTriageDueBy": add_business_days(rd1, 3).isoformat(),
            "noticeDueDate": add_business_days(rd1, cfg["notice.business-days"]).isoformat(), "status": "OPEN"}},
        "ReferralInTriage": {"summary": "Referral awaiting SIU triage", "value": {
            "referralId": rid(), "claimId": c3, "referralDate": rd2.isoformat(), "score": r.randint(default, 95),
            "tier": "Tier-3", "thresholdApplied": default, "siuTriageDueBy": add_business_days(rd2, 3).isoformat(),
            "noticeDueDate": add_business_days(rd2, cfg["notice.business-days"]).isoformat(), "status": "SIU_TRIAGE"}},
        "ReferralClosed": {"summary": "Referral closed with no fraud found", "value": {
            "referralId": rid(), "claimId": c4, "referralDate": rd3.isoformat(), "score": r.randint(default, 80),
            "tier": "Tier-2", "thresholdApplied": default, "siuTriageDueBy": add_business_days(rd3, 3).isoformat(),
            "noticeDueDate": add_business_days(rd3, cfg["notice.business-days"]).isoformat(), "status": "CLOSED_NF"}},
    }
    sent = add_business_days(rd1, r.randint(2, 8))
    dd = r.randint(10, v36["head_approval_after_days"] - 2)
    due2 = add_business_days(rd2, cfg["notice.business-days"])
    exs["NoticeSent"] = {"summary": "Record that the customer notice letter was sent",
                         "value": {"action": "RECORD_SENT", "sentOn": sent.isoformat(), "channel": "LETTER"}}
    exs["NoticeDeferred"] = {"summary": "Defer the notice where SIU certifies a tipping-off risk",
                             "value": {"action": "DEFER", "deferralDays": dd, "approverId": "siu.approver.%03d" % r.randint(100, 999)}}
    exs["NoticeStatusSent"] = {"summary": "Notice recorded as sent", "value": {
        "referralId": exs["ReferralCreated"]["value"]["referralId"],
        "deadline": add_business_days(rd1, cfg["notice.business-days"]).isoformat(), "status": "SENT"}}
    exs["NoticeStatusDeferred"] = {"summary": "Notice deferred", "value": {
        "referralId": exs["ReferralInTriage"]["value"]["referralId"], "deadline": due2.isoformat(), "status": "DEFERRED"}}
    exs.update(problem_examples("Problem", [(e["code"], e["meaning"]) for e in spec["x-error-codes"]], on))
    comp["examples"] = exs
    spec["x-data-model"] = {"note": "Persistence owned by the service (PostgreSQL); not exposed directly to consumers.",
                            "tables": data_model("fraud-referral-svc", on)}
    spec["x-consumers"] = api_consumers("fraud-referral-svc", on)
    spec["x-guidelines"] = r.sample(phrases.BANKS["design"], 4) + r.sample(phrases.BANKS["api"], 3)


def build_ST044(out_dir: pathlib.Path) -> Built:
    fid = "ST044"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:openapi")
    s = W.services["fraud-referral-svc"]
    cfg = s["config"]
    v36 = rule_params_ok(fid, "BR-FRD-036", 2)
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "fraud-referral-svc API", "version": "2.3",
            "description": ("Fraud referral decisions, SIU hand-off and customer-notice deadlines (NISA Circular 2026/04). "
                            "Implements BR-FRD-031, BR-FRD-032, BR-FRD-033, BR-FRD-035 and BR-FRD-036. "
                            + phrases.paragraph(r, "api", 2)),
            "contact": {"name": pname("P042", on), "email": pemail("P042", on)},
            "x-owner-team": team_name("T29", on),
            "x-document-control": doc_meta(fid, ["P008", "P049"]),
        },
        "servers": [{"url": "https://fraud-referral-svc.apps.ocp-prd-lon1.corvane.internal/v2", "description": "Production"}],
        "security": [{"cis": ["fraud.read"]}],
        "tags": [{"name": "referrals"}, {"name": "customer-notice"}],
        "paths": {},
        "components": {
            "parameters": {"ReferralId": {"name": "referralId", "in": "path", "required": True,
                                          "schema": {"type": "string", "pattern": "^FRF-\\d{4}-\\d{5}$"}},
                           **COMMON_PARAMS},
            "schemas": {
                "ReferralRequest": {"type": "object", "required": ["claimId", "score", "tier"],
                                    "properties": {"claimId": {"type": "string"},
                                                   "score": {"type": "integer", "minimum": 0, "maximum": 100,
                                                             "description": f"{sysname('SYS03', on)} score (0-100)."},
                                                   "tier": {"type": "string", "enum": ["Tier-1", "Tier-2", "Tier-3"]},
                                                   "source": {"type": "string", "enum": ["SCORE", "HANDLER", "INDICATORS"]},
                                                   "indicators": {"type": "array", "items": {"type": "string"}}}},
                "Referral": {"type": "object",
                             "properties": {"referralId": {"type": "string"}, "claimId": {"type": "string"},
                                            "referralDate": {"type": "string", "format": "date"},
                                            "score": {"type": "integer"}, "tier": {"type": "string"},
                                            "thresholdApplied": {"type": "integer",
                                                                 "description": (f"{cfg['referral.threshold.default']} for all claims; "
                                                                                 f"{cfg['referral.threshold.tier3']} for Tier-3 claims from "
                                                                                 f"{cfg['referral.threshold.tier3.effective-from']} (BR-FRD-031 v2).")},
                                            "siuTriageDueBy": {"type": "string", "format": "date",
                                                               "description": "Referral date + 3 business days (BR-FRD-035 v2)."},
                                            "noticeDueDate": {"type": "string", "format": "date"},
                                            "status": {"type": "string", "enum": ["OPEN", "SIU_TRIAGE", "INVESTIGATION", "CLOSED_NF", "CLOSED_CF", "WITHDRAWN"]}}},
                "CustomerNoticeRequest": {"type": "object", "required": ["action"],
                                          "properties": {"action": {"type": "string", "enum": ["RECORD_SENT", "DEFER"]},
                                                         "sentOn": {"type": "string", "format": "date"},
                                                         "channel": {"type": "string", "enum": ["LETTER", "EMAIL"]},
                                                         "deferralDays": {"type": "integer", "maximum": cfg["notice.max-deferral-days"],
                                                                          "description": (f"Up to {v36['max_deferral_days']} days where SIU certifies a tipping-off risk. "
                                                                                          f"From 2026-10-01 deferrals beyond {v36['head_approval_after_days']} days need the "
                                                                                          f"Head of Counter-Fraud & SIU and {v36['notify']} is notified the same day (BR-FRD-036 v2).")},
                                                         "approverId": {"type": "string"}}},
                "CustomerNotice": {"type": "object",
                                   "properties": {"referralId": {"type": "string"},
                                                  "deadline": {"type": "string", "format": "date",
                                                               "description": f"Referral date + {cfg['notice.business-days']} business days (BR-FRD-032 v2), UK calendar."},
                                                  "status": {"type": "string", "enum": ["DUE", "SENT", "DEFERRED", "OVERDUE"]}}},
                "Problem": problem_schema(),
            },
            "securitySchemes": {"cis": {"type": "oauth2", "flows": {"clientCredentials": {
                "tokenUrl": "https://cis.corvane.internal/oauth2/token",
                "scopes": {"fraud.read": "Read referrals", "fraud.write": "Create referrals and record notices"}}}}},
        },
        "x-events": {"produces": svc_topics(fid, "fraud-referral-svc", "produces", on),
                     "consumes": svc_topics(fid, "fraud-referral-svc", "consumes", on)},
        "x-business-rules": {"autoDecline": {"enabled": cfg["auto-decline.enabled"], "rule": "BR-FRD-033"},
                             "tierDefinition": "BR-TRI-003 v3", "noticeCalendar": "UK business days"},
        "x-error-codes": [{"code": c, "meaning": m} for c, m in [
            ("FRD-VAL-001", "score outside 0-100"), ("FRD-VAL-002", "unknown tier"),
            ("FRD-BUS-010", "score below the applicable threshold and no handler or indicator reason"),
            ("FRD-BUS-020", "deferral longer than the maximum allowed (BR-FRD-036)"),
            ("FRD-BUS-021", "deferral beyond 30 days without the Head of Counter-Fraud & SIU (from 2026-10-01)"),
            ("FRD-BUS-030", "automatic decline requested; not allowed (BR-FRD-033)"),
            ("FRD-SYS-500", "unexpected error; retry with the same Idempotency-Key")]],
        "x-changelog": [{"version": v, "date": d_, "change": c} for v, d_, c in [
            ("2.0", "2026-03-20", "Customer-notice endpoint and 10-business-day deadline (CHUB-209)"),
            ("2.1", "2026-05-11", "SIU triage due date on referrals (BR-FRD-035 v2)"),
            ("2.2", "2026-08-01", "Spring Boot patch upgrade, no contract change (CHUB-182)"),
            ("2.3", "2026-09-29", "Tier-3 threshold 60 from 2026-10-01 and deferral approval rule from 2026-10-01 (CHUB-388)")]],
    }
    st44_examples(r, fid, spec, on, cfg, v36)
    for a in s["apis"]:
        op = {"summary": a["summary"], "tags": ["customer-notice" if "notice" in a["path"] else "referrals"],
              "parameters": [{"$ref": "#/components/parameters/CorrelationId"}]}
        if "{referralId}" in a["path"]:
            op["parameters"].insert(0, {"$ref": "#/components/parameters/ReferralId"})
        if a["method"] == "POST":
            op["parameters"].append({"$ref": "#/components/parameters/IdempotencyKey"})
            op["security"] = [{"cis": ["fraud.write"]}]
            if "notice" in a["path"]:
                op["description"] = ("Records that the customer notice was sent, or defers it under BR-FRD-036. "
                                     "The notice tells the customer that the claim is subject to additional checks.")
                op["requestBody"] = {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/CustomerNoticeRequest"}}}}
                op["responses"] = std_responses({"200": {"description": "Notice updated.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/CustomerNotice"}}}},
                                                 "409": {"description": "Deferral needs a higher approver."}})
            else:
                op["requestBody"] = {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ReferralRequest"}}}}
                op["responses"] = std_responses({"201": {"description": "Referral created.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Referral"}}}},
                                                 "422": {"description": "Score below the applicable threshold and no handler or indicator reason."}})
        else:
            op["responses"] = std_responses({"200": {"description": "The referral.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Referral"}}}}})
        op["responses"]["429"] = {"$ref": "#/components/responses/TooManyRequests"}
        op["responses"]["503"] = {"$ref": "#/components/responses/ServiceUnavailable"}
        if a["method"] == "POST" and "notice" in a["path"]:
            op["requestBody"]["content"]["application/json"]["examples"] = {
                n: {"$ref": f"#/components/examples/{n}"} for n in ("NoticeSent", "NoticeDeferred")}
            op["responses"]["200"]["content"]["application/json"]["examples"] = {
                n: {"$ref": f"#/components/examples/{n}"} for n in ("NoticeStatusSent", "NoticeStatusDeferred")}
        elif a["method"] == "POST":
            op["requestBody"]["content"]["application/json"]["examples"] = {
                n: {"$ref": f"#/components/examples/{n}"} for n in ("ScoreReferralTier2", "HandlerReferral")}
            op["responses"]["201"]["content"]["application/json"]["examples"] = {
                "ReferralCreated": {"$ref": "#/components/examples/ReferralCreated"}}
            op["responses"]["201"]["headers"] = {"Location": {"$ref": "#/components/headers/Location"},
                                                 "X-Correlation-Id": {"$ref": "#/components/headers/X-Correlation-Id"}}
        else:
            op["responses"]["200"]["content"]["application/json"]["examples"] = {
                n: {"$ref": f"#/components/examples/{n}"} for n in ("ReferralInTriage", "ReferralClosed")}
        op["responses"] = dict(sorted(op["responses"].items()))
        spec["paths"].setdefault(a["path"], {})[a["method"].lower()] = op
    text = header(fid) + ydump(spec)
    F.add("needle", "OpenAPI: POST /referrals/{referralId}/customer-notice — deadline is the referral date plus 10 business days.",
          yloc('paths."/referrals/{referralId}/customer-notice".post.summary'), "referral date + 10 business days",
          world_ref="SERVICE:fraud-referral-svc#apis", placement="PL-179")
    F.add("general", "fraud-referral-svc thresholdApplied: 65 for all claims; 60 for Tier-3 claims from 2026-10-01 (BR-FRD-031 v2).",
          yloc("components.schemas.Referral.properties.thresholdApplied.description"), "60 for Tier-3 claims from 2026-10-01",
          world_ref="RULE:BR-FRD-031@v2")
    F.add("general", "Customer notice deferral: up to 60 days; beyond 30 days needs the Head of Counter-Fraud & SIU from 2026-10-01 (BR-FRD-036 v2).",
          yloc("components.schemas.CustomerNoticeRequest.properties.deferralDays.description"),
          "beyond 30 days need the Head of Counter-Fraud & SIU", world_ref="RULE:BR-FRD-036@v2")
    F.add("general", "fraud-referral-svc produces fraud.referral.created.v1 and fraud.referral.notice-due.v1.",
          yloc("x-events.produces"), "fraud.referral.notice-due.v1", world_ref="SERVICE:fraud-referral-svc#kafka_topics")
    F.add("general", "SIU triage due date is the referral date + 3 business days (BR-FRD-035 v2).",
          yloc("components.schemas.Referral.properties.siuTriageDueBy.description"), "3 business days (BR-FRD-035 v2)",
          world_ref="RULE:BR-FRD-035@v2")
    F.add("general", "fraud-referral-svc persists customer notices in PostgreSQL table fraud.customer_notice.",
          yloc("x-data-model.tables[1].table"), "fraud.customer_notice", world_ref="TABLE:fraud.customer_notice")
    return Built(fid, text.encode("utf-8"), F.items, f"{len(spec['paths'])} rows")


# ---------------------------------------------------------------------------------------------
# ST045 Business rules configuration
# ---------------------------------------------------------------------------------------------

ST045_RULES = ["BR-FRD-031", "BR-FRD-032", "BR-FRD-033", "BR-FRD-034", "BR-FRD-035", "BR-FRD-036", "BR-FRD-005",
               "BR-FRD-012", "BR-FRD-019", "BR-TRI-003", "BR-TRI-004", "BR-TRI-006", "BR-TRI-007", "BR-RSV-003",
               "BR-RSV-007", "BR-RSV-011", "BR-STL-002", "BR-STL-014", "BR-REC-003", "BR-REC-005", "BR-REC-011",
               "BR-FNOL-001", "BR-FNOL-003", "BR-FNOL-004"]


def build_ST045(out_dir: pathlib.Path) -> Built:
    fid = "ST045"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    areas: dict[str, dict] = {}
    for rid in ST045_RULES:
        rr = W.rules[rid]
        cur = W.rule_version(rid, on)
        vers = []
        for v in sorted(rr["versions"], key=lambda x: -x["version"]):
            if v["status"] == "draft":
                continue
            ve = {"version": v["version"], "status": v["status"], "effectiveFrom": v["effective_from"],
                  "effectiveTo": v["effective_to"], "parameters": rule_params_ok(fid, rid, v["version"])}
            if rule_text_ok(fid, rid, v["version"]):
                ve["text"] = v["text"]
            ve["approvedOn"] = v["approved_on"]
            vers.append(ve)
        entry = {"title": rr["title"], "owner": pname(rr["owner"], on),
                 "inForce": cur["version"] if cur else None,
                 "implementedIn": {"services": [svcname(x, on) for x in rr["implemented_in"]["services"]],
                                   "programs": rr["implemented_in"]["programs"]},
                 "versions": vers}
        if rr.get("superseded_by"):
            entry["supersededBy"] = rr["superseded_by"]
        areas.setdefault(rr["area"].lower(), {})[rid] = entry
    doc = {
        "apiVersion": "rules.corvane.internal/v1",
        "kind": "RuleSet",
        "metadata": {"name": "claims-business-rules", "effectiveAsOf": on, **doc_meta(fid, ["P008", "P005"]),
                     "decisionRefs": ["DEC-014", "DEC-015"], "adr": "ADR-010, ADR-020"},
        "spec": {"evaluation": "Services read the version whose effective window contains the business date of the event.",
                 "areas": areas},
    }
    text = header(fid, ["Business rules as versioned configuration (ADR-010). Values are effective-dated."]) + ydump(doc)
    F.add("general", "Rules config: BR-FRD-031 v2 effective 2026-10-01 with threshold 65 and tier3_threshold 60.",
          yloc("spec.areas.frd.BR-FRD-031.versions[0].parameters"), "threshold: 65 tier3_threshold: 60",
          world_ref="RULE:BR-FRD-031@v2")
    F.add("general", "Rules config: BR-FRD-036 v2 (from 2026-10-01): max 60 days deferral, Head approval after 30 days, notify Compliance.",
          yloc("spec.areas.frd.BR-FRD-036.versions[0].parameters"), "head_approval_after_days: 30",
          world_ref="RULE:BR-FRD-036@v2")
    F.add("general", "Rules config: Tier-3 definition BR-TRI-003 v3 uses £50,000 (NOK 650,000 / SEK 680,000 / DKK 430,000).",
          yloc("spec.areas.tri.BR-TRI-003.versions[0].parameters"), "tier3_min_gbp: 50000", world_ref="RULE:BR-TRI-003@v3")
    F.add("temporal", "Rules config: BR-RSV-007 v3 (14 days) from 2026-07-01 superseded v2 (21 days).",
          yloc("spec.areas.rsv.BR-RSV-007.versions[1]"), "review_days: 21", world_ref="RULE:BR-RSV-007@v2")
    F.add("general", "Rules config: BR-FRD-019 (auto-decline) is superseded by BR-FRD-033.",
          yloc("spec.areas.frd.BR-FRD-019.supersededBy"), "BR-FRD-033", world_ref="RULE:BR-FRD-019#superseded_by")
    F.add("general", "Rules config: payment authority BR-STL-002 v3 gives a Team Leader £75,000.",
          yloc("spec.areas.stl.BR-STL-002.versions[0].parameters"), "team_leader: 75000", world_ref="RULE:BR-STL-002@v3")
    return Built(fid, text.encode("utf-8"), F.items, f"{len(ST045_RULES)} rows")


# ---------------------------------------------------------------------------------------------
# ST046 Kafka topics (GitOps)
# ---------------------------------------------------------------------------------------------

def build_ST046(out_dir: pathlib.Path) -> Built:
    fid = "ST046"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    docs = []
    index = {}
    for t in sorted(topics_as_of(on), key=lambda x: x["name"]):
        ref = f"TOPIC:{t['name']}"
        labels = {"strimzi.io/cluster": "esp-prd"}
        tm = topic_owner_team(t, on)
        if tm:
            labels["corvane.example/owner-team"] = team_name(tm, on).lower().replace(" – ", "-").replace(" & ", "-").replace(" ", "-")
        if t["name"] in TOPIC_IFACE:
            labels["corvane.example/interface"] = TOPIC_IFACE[t["name"]]
        spec = {"topicName": t["name"]}
        if may(fid, ref, "partitions"):
            spec["partitions"] = t["partitions"]
        spec["replicas"] = 3
        cfg = {"cleanup.policy": "delete", "min.insync.replicas": 2}
        if may(fid, ref, "retention_days"):
            cfg["retention.ms"] = t["retention_days"] * 86400000
        spec["config"] = cfg
        meta = {"name": t["name"], "namespace": "esp", "labels": labels}
        ann = {}
        if may(fid, ref, "producer"):
            p_ = t["producer"]
            ann["corvane.example/producer"] = svcname(p_, on) if p_ in W.services else p_
        if t.get("consumers") and may(fid, ref, "consumers"):
            ann["corvane.example/consumers"] = ", ".join(svcname(c, on) if c in W.services else c for c in t["consumers"])
        if t.get("key") and may(fid, ref, "key"):
            ann["corvane.example/message-key"] = t["key"]
        if t.get("schema_version") and may(fid, ref, "schema_version"):
            ann["corvane.example/schema-version"] = str(t["schema_version"])
        ann["corvane.example/schema-subject"] = f"{t['name']}-value"
        if t.get("ticket"):
            ann["corvane.example/change-ticket"] = t["ticket"]
        if t.get("introduced"):
            ann["corvane.example/introduced"] = str(t["introduced"])
        if "partitions" not in spec:
            ann["corvane.example/note"] = "Bridge topic (ADR-012); partition count and retention are not overridden in this file."
        meta["annotations"] = ann
        index[t["name"]] = len(docs)
        docs.append({"apiVersion": "kafka.strimzi.io/v1beta2", "kind": "KafkaTopic", "metadata": meta, "spec": spec})
    assert "partitions" not in docs[index["claims.reserve.movement.v1"]]["spec"]
    assert "retention.ms" not in docs[index["claims.reserve.movement.v1"]]["spec"]["config"]
    text = header(fid, ["GitOps source for KafkaTopic resources on cluster esp-prd (Strimzi). Applied by Argo CD.",
                        "Topic changes need an Integration Platform change and consumer sign-off."]) + ydump_all(docs)
    i_f = index["fnol.received.v1"]
    F.add("general", "GitOps: fnol.received.v1 has 6 partitions, 3 replicas and retention 604800000 ms (7 days).",
          yloc("spec", i_f), "partitions: 6 replicas: 3", world_ref="TOPIC:fnol.received.v1#partitions")
    i_r = index["reserve.changed.v2"]
    F.add("general", "GitOps: reserve.changed.v2 has 12 partitions and retention 2592000000 ms (30 days).",
          yloc("spec.config", i_r), "retention.ms: 2592000000", world_ref="TOPIC:reserve.changed.v2#retention_days")
    i_m = index["claims.reserve.movement.v1"]
    F.add("general", "GitOps: claims.reserve.movement.v1 is labelled with interface CLX-IF-049.",
          yloc("metadata.labels", i_m), "corvane.example/interface: CLX-IF-049", world_ref="TOPIC:claims.reserve.movement.v1",
          notes="Partitions and retention deliberately absent (exclusive to ST030 and LD013).")
    F.add("scale", f"The GitOps topic file defines {len(docs)} KafkaTopic resources.", yloc("kind", len(docs) - 1),
          "KafkaTopic", world_ref="SYSTEM:SYS15")
    F.add("general", "GitOps: claims.reserve.movement.v1 is consumed by reserve-engine.",
          yloc("metadata.annotations", i_m), "corvane.example/consumers: reserve-engine",
          world_ref="TOPIC:claims.reserve.movement.v1#consumers")
    return Built(fid, text.encode("utf-8"), F.items, f"{len(docs)} rows")


# ---------------------------------------------------------------------------------------------
# ST047 Helm values
# ---------------------------------------------------------------------------------------------

def build_ST047(out_dir: pathlib.Path) -> Built:
    fid = "ST047"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:helm")
    svcs = {}
    for sid, s in W.services_by_id.items():
        name = svcname(sid, on)
        o = svc_owner(fid, s["name"], on)
        dbs = sorted({W.tables[t]["database"] for t in s["postgres_tables"]})
        e = {
            "enabled": s["status"] == "live",
            "image": {"repository": s["image"], "tag": f"r2026.09.{r.randint(1, 6)}"},
            "replicaCount": s["replicas"],
            "namespace": s["k8s_namespace"],
            "labels": {"app.kubernetes.io/part-of": "claims-hub",
                       "corvane.example/squad": team_name(o["team"], on) if o else None},
            "service": {"port": 8080, "managementPort": 8081},
            "ingress": {"enabled": True, "host": f"{name}.apps.ocp-prd-lon1.corvane.internal", "tls": True},
            "database": {"name": dbs[0] if dbs else None, "schemaTables": s["postgres_tables"],
                         "credentialsSecret": f"{name}-db"},
            "kafka": {"produces": svc_topics(fid, s["name"], "produces", on),
                      "consumes": svc_topics(fid, s["name"], "consumes", on),
                      "consumerGroup": f"{name}"},
        }
        if s.get("infra"):
            res = {}
            if may(fid, f"SERVICE:{s['name']}", "infra.cpu_request"):
                res.setdefault("requests", {})["cpu"] = s["infra"]["cpu_request"]
            if may(fid, f"SERVICE:{s['name']}", "infra.memory_limit"):
                res.setdefault("limits", {})["memory"] = s["infra"]["memory_limit"]
            e["resources"] = res
        if s.get("config"):
            e["config"] = {k: v for k, v in s["config"].items()
                           if k != "config_history" and may(fid, f"SERVICE:{s['name']}", f"config.{k}")}
        if not e["labels"]["corvane.example/squad"]:
            e["labels"].pop("corvane.example/squad")
        e["autoscaling"] = {"enabled": True, "minReplicas": s["replicas"], "maxReplicas": s["replicas"] * 2,
                            "targetCPUUtilizationPercentage": 70}
        e["probes"] = {"readiness": "/actuator/health/readiness", "liveness": "/actuator/health/liveness"}
        e["env"] = {"SPRING_PROFILES_ACTIVE": "prod", "MANAGEMENT_SERVER_PORT": "8081",
                    "OTEL_SERVICE_NAME": name, "TZ": "UTC"}
        e["networkPolicy"] = {"allowIngressFrom": ["openshift-ingress", "chub-monitoring"],
                              "allowEgressTo": ["esp", "cis"] + ([f"{s['k8s_namespace']}-db"] if dbs else [])}
        svcs[name] = e
    doc = {
        "global": {
            "environment": "prod", "cluster": "ocp-prd-lon1", "drCluster": "ocp-dr-lds1",
            "imageRegistry": "registry.corvane.internal/chub", "imagePullPolicy": "IfNotPresent",
            "kafka": {"bootstrapServers": "esp-prd-kafka-bootstrap.esp.svc:9093", "securityProtocol": "SASL_SSL",
                      "schemaRegistry": "https://schema-registry.esp.svc:8081"},
            "identity": {"issuer": "https://cis.corvane.internal", "audience": "claims-hub"},
            "observability": {"tracing": True, "metricsPath": "/actuator/prometheus", "logFormat": "json"},
            "defaultResources": {"requests": {"cpu": "250m", "memory": "512Mi"}, "limits": {"memory": "1Gi"}},
            "podDisruptionBudget": {"minAvailable": 1},
            "secrets": {"provider": "external-secrets", "placeholder": "<REDACTED>"},
        },
        "services": svcs,
    }
    text = header(fid, ["Helm values for the claims-hub umbrella chart (prod). Per-environment overrides live next to this file."]) + ydump(doc)
    F.add("general", "Helm: reserve-engine requests 500m CPU and has a 2Gi memory limit.",
          yloc("services.reserve-engine.resources"), "cpu: 500m", world_ref="SERVICE:reserve-engine#infra.cpu_request")
    F.add("general", "Helm: fraud-referral-svc runs 3 replicas in namespace chub-fraud.",
          yloc("services.fraud-referral-svc"), "replicaCount: 3 namespace: chub-fraud", world_ref="SERVICE:fraud-referral-svc#replicas")
    F.add("general", "Helm (2026-10-20): recovery-svc is still labelled with squad Hub Squad – Fraud & Settlement.",
          yloc('services.recovery-svc.labels."corvane.example/squad"'), "Hub Squad – Fraud & Settlement",
          world_ref="SERVICE:recovery-svc#owner_history:T29")
    F.add("general", "Helm: reporting-feed-svc is disabled (in development).", yloc("services.reporting-feed-svc.enabled"),
          "false", world_ref="SERVICE:reporting-feed-svc#status")
    F.add("general", "Helm: reserve-engine consumes claims.reserve.movement.v1 and triage.completed.v1.",
          yloc("services.reserve-engine.kafka.consumes"), "claims.reserve.movement.v1", world_ref="SERVICE:reserve-engine#kafka_topics.consumes:claims.reserve.movement.v1")
    return Built(fid, text.encode("utf-8"), F.items, f"{len(svcs)} rows")


# ---------------------------------------------------------------------------------------------
# ST048 Data contract CLX-IF-049
# ---------------------------------------------------------------------------------------------

MOVEMENT_FIELDS = [
    ("claim_id", "string", "RM-CLAIM-ID", "Claim reference; message key"),
    ("reserve_id", "long", "RM-RSV-ID", "CLARA reserve identifier"),
    ("movement_id", "long", "RM-MOVE-ID", "CLARA movement identifier (idempotency key)"),
    ("movement_type", "enum", "RM-MOVE-TYPE", "IN, AD, IX, RV, ST or RC"),
    ("currency", "string", "RM-CURRENCY", "ISO 4217 currency of the reserve"),
    ("amount_minor", "long", "RM-AMOUNT", "Movement amount in minor units (RM-AMOUNT x 100)"),
    ("gbp_amount_minor", "long", "RM-GBP-AMOUNT", "GBP equivalent in pence (RM-GBP-AMOUNT x 100)"),
    ("product", "string", "RM-PRODUCT", "Product code"),
    ("peril", "string", "RM-PERIL", "Peril (claim type) code"),
    ("tier", "string", "RM-TIER", "Claim tier at extract time"),
    ("movement_ts", "timestamp-millis", "RM-MOVE-TS", "Movement time stamp converted to UTC"),
    ("extract_date", "date", "RM-EXTRACT-DATE", "Business date of the CLX-IF-042 extract"),
    ("record_version", "int", "RM-REC-VERSION", "RSVMOVE record version (02)"),
]


def st48_examples(r, on: str) -> list[dict]:
    """Two sample messages (synthetic values) in the contract's field layout."""
    from .json_specs import claim_ref
    import datetime as _dt
    used: set = set()
    out = []
    prev = (_dt.date.fromisoformat(on) - _dt.timedelta(days=1)).isoformat()
    for country, cur, rate, mt, prod, peril, tier in (("UK", "GBP", 100, "AD", "MOTUK", "COL", "2"),
                                                      ("NO", "NOK", 1350, "IN", "MOTNO", "COL", "3")):
        gbp = r.randint(12, 180) * 10000
        amt = gbp * rate // 100
        out.append({"key": None, "value": {
            "claim_id": claim_ref(r, country, 2025, used), "reserve_id": r.randint(10 ** 8, 10 ** 9),
            "movement_id": r.randint(10 ** 9, 10 ** 10), "movement_type": mt, "currency": cur,
            "amount_minor": amt, "gbp_amount_minor": gbp, "product": prod, "peril": peril, "tier": tier,
            "movement_ts": f"{prev}T{r.randint(9, 16):02d}:{r.randint(10, 59):02d}:{r.randint(10, 59):02d}.000Z", "extract_date": prev,
            "record_version": 2}})
        out[-1]["key"] = out[-1]["value"]["claim_id"]
    return out


def build_ST048(out_dir: pathlib.Path) -> Built:
    fid = "ST048"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:contract")
    i49 = W.interfaces["CLX-IF-049"]
    t = W.topics["claims.reserve.movement.v1"]
    need(fid, "TOPIC:claims.reserve.movement.v1", "schema_version")
    need(fid, "TOPIC:claims.reserve.movement.v1", "key")
    consumer = svcname("reserve-engine", on)
    assert consumer == "reserve-svc"
    fields = MOVEMENT_FIELDS
    doc = {
        "dataContractSpecification": "0.9.3",
        "id": "urn:corvane:contract:clx-if-049",
        "schemaVersion": t["schema_version"],
        "key": t["key"],
        "amounts": "minor units",
        "info": {"title": f"{i49['name']} (CLX-IF-049)", "version": f"{t['schema_version']}.0.0", "status": fstatus(fid),
                 "owner": team_name("T22", on), "interfaceOwner": pname(i49["owner"], on),
                 "author": pname(fauthor(fid), on), "date": on,
                 "description": i49["note"].replace("reserve-engine", consumer) + ". " + phrases.sentence(r, "design")},
        "source": {"interface": "CLX-IF-042", "name": W.interfaces["CLX-IF-042"]["name"], "layout": "RSVMOVE copybook",
                   "queue": "CLR.RSVMOVE.OUT", "queueManager": "CLRQM01", "recordVersion": "02",
                   "system": sysname("SYS01", on)},
        "target": {"topic": t["name"], "cluster": "esp-prd", "format": "Avro", "subject": f"{t['name']}-value",
                   "compatibility": "BACKWARD"},
        "producer": t["producer"],
        "consumers": [consumer],
        "schedule": i49["schedule"],
        "decisions": ["ADR-012 batch-to-event bridge", "ADR-017 replaces CDC (ADR-005)", "DEC-017 (Design Authority 2025-10-21)"],
        "ticket": t["ticket"],
        "fields": [{"name": n, "type": ty, "source": src, "description": dsc, "required": True} for n, ty, src, dsc in fields],
        "quality": [
            "Every message has a non-empty claim_id key.",
            "amount_minor equals RM-AMOUNT multiplied by 100 with the sign preserved.",
            "movement_id is unique per extract date; replays are de-duplicated by the consumer.",
            "record_version is 02; any other value is rejected to the dead-letter topic.",
        ],
        "avroSchema": __import__("json").dumps({"type": "record", "name": "ReserveMovement", "namespace": "com.corvane.claims.reserve",
                                                 "fields": [{"name": n, "type": {"string": "string", "long": "long", "int": "int",
                                                                                 "enum": "string", "date": {"type": "int", "logicalType": "date"},
                                                                                 "timestamp-millis": {"type": "long", "logicalType": "timestamp-millis"}}[ty],
                                                             "doc": dsc} for n, ty, src, dsc in fields]}, indent=2),
        "lineage": [
            {"step": 1, "system": sysname("SYS01", on), "what": "CLRRS170 (job CLRNRSV3) extracts reserve movements from CLR.T_RESERVE_MOVEMENT"},
            {"step": 2, "system": sysname("SYS14", on), "what": "RSVMOVE records are put to queue CLR.RSVMOVE.OUT on CLRQM01 (CLX-IF-042)"},
            {"step": 3, "system": sysname("SYS15", on), "what": "The bridge converts each record to Avro and publishes it keyed by claim_id (CLX-IF-049)"},
            {"step": 4, "system": sysname("SYS02", on), "what": f"{consumer} consumes the topic and applies movements idempotently on movement_id"},
        ],
        "examples": st48_examples(r, on),
        "contacts": [{"role": "Interface owner", "name": pname(i49["owner"], on), "email": pemail(i49["owner"], on)},
                     {"role": "Contract author", "name": pname(fauthor(fid), on), "email": pemail(fauthor(fid), on)},
                     {"role": "Consumer owner", "name": pname(W.services["reserve-engine"]["owner_person"], on),
                      "email": pemail(W.services["reserve-engine"]["owner_person"], on)}],
        "changeManagement": {"breakingChanges": "New major schema version and a new topic; consumers sign off (CHUB-144).",
                             "lessonsLearned": "INC-2025-0412: the RM-AMOUNT widening broke CLX-IF-043; layout changes now need consumer sign-off."},
    }
    text = header(fid, ["Data contract between the MQ-to-Kafka bridge and its consumers."]) + ydump(doc)
    F.add("needle", "Data contract CLX-IF-049: schema version 3, key claim_id, amounts in minor units.",
          yloc(""), "schemaVersion: 3 key: claim_id amounts: minor units",
          world_ref="TOPIC:claims.reserve.movement.v1#schema_version", placement="PL-180")
    F.add("temporal", "As of 2025-12-12 the consumer of claims.reserve.movement.v1 is reserve-svc (renamed reserve-engine on 2026-02-10).",
          yloc("consumers"), "reserve-svc", world_ref="SERVICE:reserve-engine#renames")
    F.add("general", "CLX-IF-049 maps RSVMOVE field RM-AMOUNT to amount_minor (minor units).",
          yloc("fields[5]"), "name: amount_minor", world_ref="COPYBOOK:RSVMOVE#fields")
    F.add("general", "The CLX-IF-049 bridge runs daily at 02:45.", yloc("schedule"), "daily 02:45",
          world_ref="INTERFACE:CLX-IF-049#schedule")
    F.add("general", "CLX-IF-049 was delivered under CHUB-188.", yloc("ticket"), "CHUB-188",
          world_ref="TOPIC:claims.reserve.movement.v1#ticket")
    F.add("general", "CLX-IF-049 lineage: RSVMOVE records arrive on queue CLR.RSVMOVE.OUT (CLX-IF-042) before bridging.",
          yloc("lineage[1].what"), "CLR.RSVMOVE.OUT", world_ref="INTERFACE:CLX-IF-042#mq_queue")
    return Built(fid, text.encode("utf-8"), F.items, f"{len(fields)} rows")


# ---------------------------------------------------------------------------------------------
# ST049 / ST050 Kubernetes deployments
# ---------------------------------------------------------------------------------------------

def k8s_bundle(fid: str, svc: str, env: list[dict], config_text: str, hpa_max: int) -> list[dict]:
    on = fdate(fid)
    s = W.services[svc]
    name = svcname(svc, on)
    o = svc_owner(fid, svc, on)
    labels = {"app.kubernetes.io/name": name, "app.kubernetes.io/part-of": "claims-hub",
              "corvane.example/squad": team_name(o["team"], on).lower().replace(" – ", "-").replace(" & ", "-").replace(" ", "-")}
    res = {"requests": {"cpu": "250m", "memory": "512Mi"}, "limits": {"memory": "1Gi"}}
    if s.get("infra"):
        res = {"requests": {"cpu": s["infra"]["cpu_request"], "memory": "1Gi"}, "limits": {"memory": s["infra"]["memory_limit"]}}
    dep = {
        "apiVersion": "apps/v1", "kind": "Deployment",
        "metadata": {"name": name, "namespace": s["k8s_namespace"], "labels": labels,
                     "annotations": {"corvane.example/owner": pname(o["person"], on), "corvane.example/repo": s["repo_path"]}},
        "spec": {
            "replicas": s["replicas"],
            "selector": {"matchLabels": {"app.kubernetes.io/name": name}},
            "strategy": {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": 1, "maxSurge": 1}},
            "template": {
                "metadata": {"labels": labels},
                "spec": {
                    "serviceAccountName": name,
                    "containers": [{
                        "name": name, "image": f"{s['image']}:r2026.09.{util.rng(fid).randint(1, 5)}",
                        "ports": [{"name": "http", "containerPort": 8080}, {"name": "management", "containerPort": 8081}],
                        "env": env,
                        "envFrom": [{"configMapRef": {"name": f"{name}-config"}}],
                        "resources": res,
                        "readinessProbe": {"httpGet": {"path": "/actuator/health/readiness", "port": "management"}},
                        "livenessProbe": {"httpGet": {"path": "/actuator/health/liveness", "port": "management"}},
                        "volumeMounts": [{"name": "app-config", "mountPath": "/config", "readOnly": True}],
                    }],
                    "volumes": [{"name": "app-config", "configMap": {"name": f"{name}-config"}}],
                },
            },
        },
    }
    svc_doc = {"apiVersion": "v1", "kind": "Service", "metadata": {"name": name, "namespace": s["k8s_namespace"], "labels": labels},
               "spec": {"selector": {"app.kubernetes.io/name": name},
                        "ports": [{"name": "http", "port": 8080, "targetPort": "http"}]}}
    cm = {"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": f"{name}-config", "namespace": s["k8s_namespace"]},
          "data": {"application.yaml": config_text}}
    hpa = {"apiVersion": "autoscaling/v2", "kind": "HorizontalPodAutoscaler",
           "metadata": {"name": name, "namespace": s["k8s_namespace"]},
           "spec": {"scaleTargetRef": {"apiVersion": "apps/v1", "kind": "Deployment", "name": name},
                    "minReplicas": s["replicas"], "maxReplicas": hpa_max,
                    "metrics": [{"type": "Resource", "resource": {"name": "cpu", "target": {"type": "Utilization", "averageUtilization": 70}}}]}}
    tmpl = dep["spec"]["template"]
    tmpl["metadata"]["annotations"] = {"prometheus.io/scrape": "true", "prometheus.io/port": "8081",
                                       "prometheus.io/path": "/actuator/prometheus"}
    pod = tmpl["spec"]
    pod["securityContext"] = {"runAsNonRoot": True, "seccompProfile": {"type": "RuntimeDefault"}}
    pod["terminationGracePeriodSeconds"] = 45
    pod["topologySpreadConstraints"] = [{"maxSkew": 1, "topologyKey": "topology.kubernetes.io/zone",
                                         "whenUnsatisfiable": "ScheduleAnyway",
                                         "labelSelector": {"matchLabels": {"app.kubernetes.io/name": name}}}]
    c0 = pod["containers"][0]
    c0["securityContext"] = {"allowPrivilegeEscalation": False, "readOnlyRootFilesystem": True,
                             "capabilities": {"drop": ["ALL"]}}
    c0["startupProbe"] = {"httpGet": {"path": "/actuator/health/liveness", "port": "management"},
                          "failureThreshold": 30, "periodSeconds": 5}
    c0["lifecycle"] = {"preStop": {"exec": {"command": ["sh", "-c", "sleep 10"]}}}
    c0["volumeMounts"].append({"name": "tmp", "mountPath": "/tmp"})
    pod["volumes"].append({"name": "tmp", "emptyDir": {}})
    sa = {"apiVersion": "v1", "kind": "ServiceAccount", "metadata": {"name": name, "namespace": s["k8s_namespace"], "labels": labels}}
    pdb = {"apiVersion": "policy/v1", "kind": "PodDisruptionBudget", "metadata": {"name": name, "namespace": s["k8s_namespace"]},
           "spec": {"minAvailable": 1, "selector": {"matchLabels": {"app.kubernetes.io/name": name}}}}
    dbs = sorted({W.tables[t]["database"] for t in s["postgres_tables"]})
    egress_ns = ["esp", "cis"] + ([f"{s['k8s_namespace']}-db"] if dbs else [])
    netpol = {"apiVersion": "networking.k8s.io/v1", "kind": "NetworkPolicy",
              "metadata": {"name": f"{name}-default", "namespace": s["k8s_namespace"]},
              "spec": {"podSelector": {"matchLabels": {"app.kubernetes.io/name": name}},
                       "policyTypes": ["Ingress", "Egress"],
                       "ingress": [{"from": [{"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": ns}}}
                                             for ns in ("openshift-ingress", "chub-monitoring")]}],
                       "egress": [{"to": [{"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": ns}}}
                                          for ns in egress_ns]}]}}
    route = {"apiVersion": "route.openshift.io/v1", "kind": "Route",
             "metadata": {"name": name, "namespace": s["k8s_namespace"], "labels": labels},
             "spec": {"host": f"{name}.apps.ocp-prd-lon1.corvane.internal",
                      "to": {"kind": "Service", "name": name}, "port": {"targetPort": "http"},
                      "tls": {"termination": "edge", "insecureEdgeTerminationPolicy": "Redirect"}}}
    return [dep, svc_doc, cm, hpa, sa, pdb, netpol, route]


def build_ST049(out_dir: pathlib.Path) -> Built:
    fid = "ST049"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    s = W.services["reserve-engine"]
    cfg = {k: v for k, v in s["config"].items() if k != "config_history" and may(fid, "SERVICE:reserve-engine", f"config.{k}")}
    assert "bi-index-pct" not in cfg
    db = W.tables["reserve.reserve"]["database"]
    env = [{"name": "SPRING_PROFILES_ACTIVE", "value": "prod"},
           {"name": "DB_URL", "value": f"jdbc:postgresql://{db.replace('_', '-')}-db.chub-reserve.svc:5432/{db}"},
           {"name": "DB_USERNAME", "valueFrom": {"secretKeyRef": {"name": "reserve-engine-db", "key": "username"}}},
           {"name": "DB_PASSWORD", "valueFrom": {"secretKeyRef": {"name": "reserve-engine-db", "key": "password"}}},
           {"name": "KAFKA_CONSUMER_GROUP", "value": "reserve-engine"},
           {"name": "KAFKA_TOPICS_CONSUME", "value": ",".join(svc_topics(fid, "reserve-engine", "consumes", on))},
           {"name": "KAFKA_TOPIC_PRODUCE", "value": ",".join(svc_topics(fid, "reserve-engine", "produces", on))}]
    conf = "reserve:\n" + "".join(f"  {k}: {v}\n" for k, v in cfg.items()) + \
        "  movement-source-topic: claims.reserve.movement.v1\n  events-topic: reserve.changed.v2\n" \
        "management:\n  endpoints:\n    web:\n      exposure:\n        include: health,info,prometheus\n"
    docs = k8s_bundle(fid, "reserve-engine", env, conf, hpa_max=8)
    text = header(fid, ["deploy/k8s/chub-reserve/reserve-engine.yml – Deployment, Service, ConfigMap and HPA.",
                        "Service renamed from reserve-svc on 2026-02-10 (CHUB-233, ADR-019)."]) + ydump_all(docs)
    F.add("contradiction_new", "k8s deployment metadata.name reserve-engine, namespace chub-reserve, replicas 4.",
          yloc("metadata", 0), "name: reserve-engine namespace: chub-reserve", world_ref="SERVICE:reserve-engine#replicas",
          placement="PL-181", notes="C09: ST043 (2025-12-01) still uses reserve-svc.")
    F.add("general", "The reserve-engine Deployment runs 4 replicas.", yloc("spec.replicas", 0), "4",
          world_ref="SERVICE:reserve-engine#replicas")
    F.add("general", "reserve-engine ConfigMap: tier3-review-days 14 and large-loss-threshold-gbp 250000.",
          yloc('data."application.yaml"', 2), "tier3-review-days: 14", world_ref="SERVICE:reserve-engine#config.tier3-review-days")
    F.add("general", "reserve-engine container resources: CPU request 500m, memory limit 2Gi.",
          yloc("spec.template.spec.containers[0].resources", 0), "cpu: 500m", world_ref="SERVICE:reserve-engine#infra.cpu_request")
    F.add("general", "reserve-engine is exposed through an OpenShift Route on reserve-engine.apps.ocp-prd-lon1.corvane.internal.",
          yloc("spec.host", 7), "reserve-engine.apps.ocp-prd-lon1.corvane.internal", world_ref="SERVICE:reserve-engine")
    return Built(fid, text.encode("utf-8"), F.items, f"{len(docs)} rows")


def build_ST050(out_dir: pathlib.Path) -> Built:
    fid = "ST050"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    s = W.services["fraud-referral-svc"]
    cfg = s["config"]
    need(fid, "SERVICE:fraud-referral-svc", "config.referral.threshold.tier3")
    db = W.tables["fraud.referral"]["database"]
    env = [{"name": "SPRING_PROFILES_ACTIVE", "value": "prod"},
           {"name": "DB_URL", "value": f"jdbc:postgresql://{db.replace('_', '-')}-db.chub-fraud.svc:5432/{db}"},
           {"name": "REFERRAL_THRESHOLD_DEFAULT", "value": str(cfg["referral.threshold.default"])},
           {"name": "REFERRAL_THRESHOLD_TIER3", "value": str(cfg["referral.threshold.tier3"])},
           {"name": "REFERRAL_THRESHOLD_TIER3_EFFECTIVE_FROM", "value": cfg["referral.threshold.tier3.effective-from"]},
           {"name": "NOTICE_BUSINESS_DAYS", "value": str(cfg["notice.business-days"])},
           {"name": "NOTICE_MAX_DEFERRAL_DAYS", "value": str(cfg["notice.max-deferral-days"])},
           {"name": "AUTO_DECLINE_ENABLED", "value": str(cfg["auto-decline.enabled"]).lower()},
           {"name": "SIU_CASE_MANAGER_URL", "value": "https://scm.corvane.internal/api/referrals"},
           {"name": "KAFKA_TOPICS_CONSUME", "value": ",".join(svc_topics(fid, "fraud-referral-svc", "consumes", on))},
           {"name": "KAFKA_TOPICS_PRODUCE", "value": ",".join(svc_topics(fid, "fraud-referral-svc", "produces", on))},
           {"name": "DB_PASSWORD", "valueFrom": {"secretKeyRef": {"name": "fraud-referral-svc-db", "key": "password"}}}]
    idx = [e["name"] for e in env].index("REFERRAL_THRESHOLD_TIER3")
    conf = ("fraud:\n  calendar: UK\n  siu-triage-business-days: 3\n  notice-deferral-head-approval-after-days: 30\n"
            "  notice-deferral-notify: Compliance\n  notice-deferral-rules-effective-from: 2026-10-01\nmanagement:\n  endpoints:\n    web:\n      exposure:\n        include: health,info,prometheus\n")
    docs = k8s_bundle(fid, "fraud-referral-svc", env, conf, hpa_max=6)
    text = header(fid, ["deploy/k8s/chub-fraud/fraud-referral-svc.yml – Deployment, Service, ConfigMap and HPA.",
                        "CHUB-388: Tier-3 referral threshold 60 from 2026-10-01 (Fraud Rules Workshop 2026-09-17)."]) + ydump_all(docs)
    F.add("needle", "fraud-referral-svc deployment env REFERRAL_THRESHOLD_TIER3=60.",
          yloc(f"spec.template.spec.containers[0].env[{idx}]", 0), "name: REFERRAL_THRESHOLD_TIER3 value: 60",
          world_ref="SERVICE:fraud-referral-svc#config.referral.threshold.tier3", placement="PL-182")
    F.add("general", "fraud-referral-svc env REFERRAL_THRESHOLD_TIER3_EFFECTIVE_FROM=2026-10-01.",
          yloc(f"spec.template.spec.containers[0].env[{idx + 1}]", 0), "value: 2026-10-01",
          world_ref="SERVICE:fraud-referral-svc#config.referral.threshold.tier3.effective-from")
    F.add("general", "fraud-referral-svc env AUTO_DECLINE_ENABLED=false.",
          yloc(f"spec.template.spec.containers[0].env[{idx + 4}]", 0), "name: AUTO_DECLINE_ENABLED value: false",
          world_ref="SERVICE:fraud-referral-svc#config.auto-decline.enabled")
    F.add("general", "fraud-referral-svc runs 3 replicas in namespace chub-fraud.", yloc("spec", 0), "replicas: 3",
          world_ref="SERVICE:fraud-referral-svc#replicas")
    return Built(fid, text.encode("utf-8"), F.items, f"{len(docs)} rows")


# ---------------------------------------------------------------------------------------------
# ST051 CI pipeline
# ---------------------------------------------------------------------------------------------

def build_ST051(out_dir: pathlib.Path) -> Built:
    fid = "ST051"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    services = [svcname(sid, on) for sid in W.services_by_id]
    wf = {
        "name": "claims-hub-ci",
        "on": {"pull_request": {"branches": ["main"]}, "push": {"branches": ["main"]},
               "workflow_dispatch": {"inputs": {"service": {"description": "Build a single service", "required": False}}}},
        "permissions": {"contents": "read", "packages": "write", "id-token": "write"},
        "concurrency": {"group": "ci-${{ github.ref }}", "cancel-in-progress": True},
        "env": {"JAVA_VERSION": "21", "REGISTRY": "registry.corvane.internal/chub", "GITOPS_REPO": "corvane/platform-config"},
        "jobs": {
            "detect-changes": {"runs-on": "ubuntu-latest", "outputs": {"services": "${{ steps.filter.outputs.changes }}"},
                               "steps": [{"uses": "actions/checkout@v4"},
                                         {"id": "filter", "uses": "dorny/paths-filter@v3",
                                          "with": {"filters": "\n".join(f"{s}: services/{s}/**" for s in services)}}]},
            "build-test": {"needs": "detect-changes", "if": "${{ needs.detect-changes.outputs.services != '[]' }}",
                           "runs-on": "ubuntu-latest",
                           "strategy": {"fail-fast": False, "matrix": {"service": "${{ fromJSON(needs.detect-changes.outputs.services) }}"}},
                           "steps": [{"uses": "actions/checkout@v4"},
                                     {"uses": "actions/setup-java@v4", "with": {"distribution": "temurin", "java-version": "${{ env.JAVA_VERSION }}", "cache": "maven"}},
                                     {"name": "Unit and integration tests", "run": "mvn -B -pl services/${{ matrix.service }} -am verify"},
                                     {"name": "Publish test report", "if": "always()", "uses": "actions/upload-artifact@v4",
                                      "with": {"name": "test-report-${{ matrix.service }}", "path": "services/${{ matrix.service }}/target/surefire-reports"}}]},
            "contract-tests": {"needs": "build-test", "runs-on": "ubuntu-latest",
                               "steps": [{"uses": "actions/checkout@v4"},
                                         {"name": "OpenAPI contract tests", "run": "mvn -B -P contract-tests verify"},
                                         {"name": "Kafka consumer contract tests (ADR-023)", "run": "mvn -B -P kafka-contracts verify"}]},
            "security-scan": {"needs": "build-test", "runs-on": "ubuntu-latest",
                              "steps": [{"uses": "actions/checkout@v4"},
                                        {"name": "Dependency scan", "run": "mvn -B org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=8"},
                                        {"name": "Secret scan", "run": "gitleaks detect --no-banner --redact"}]},
            "legacy-clara-checks": {"runs-on": "ubuntu-latest", "if": "contains(github.event.head_commit.modified, 'legacy/clara/')",
                                    "steps": [{"uses": "actions/checkout@v4"},
                                              {"name": "Copybook and JCL lint", "run": "./tools/clara-lint.sh legacy/clara"},
                                              {"name": "Program inventory drift check", "run": "./tools/inventory-diff.sh legacy/clara/cobol"}]},
            "image": {"needs": ["contract-tests", "security-scan"], "if": "github.ref == 'refs/heads/main'",
                      "runs-on": "ubuntu-latest",
                      "strategy": {"matrix": {"service": "${{ fromJSON(needs.detect-changes.outputs.services) }}"}},
                      "steps": [{"uses": "actions/checkout@v4"},
                                {"name": "Build image", "run": "docker build -t $REGISTRY/${{ matrix.service }}:${{ github.sha }} services/${{ matrix.service }}"},
                                {"name": "Push image", "env": {"REGISTRY_TOKEN": "${{ secrets.REGISTRY_TOKEN }}"},
                                 "run": "echo \"$REGISTRY_TOKEN\" | docker login registry.corvane.internal -u ci --password-stdin && docker push $REGISTRY/${{ matrix.service }}:${{ github.sha }}"}]},
            "lint": {"needs": "detect-changes", "runs-on": "ubuntu-latest",
                     "steps": [{"uses": "actions/checkout@v4"},
                               {"uses": "actions/setup-java@v4", "with": {"distribution": "temurin", "java-version": "${{ env.JAVA_VERSION }}", "cache": "maven"}},
                               {"name": "Formatting check", "run": "mvn -B spotless:check"},
                               {"name": "Static analysis", "run": "mvn -B -DskipTests checkstyle:check spotbugs:check"}]},
            "api-compatibility": {"needs": "detect-changes", "runs-on": "ubuntu-latest",
                                  "steps": [{"uses": "actions/checkout@v4", "with": {"fetch-depth": 0}},
                                            {"name": "OpenAPI breaking-change check against main",
                                             "run": "./tools/openapi-diff.sh origin/main HEAD services/*/src/main/resources/openapi.yaml"},
                                            {"name": "Avro schema compatibility (BACKWARD)",
                                             "run": "./tools/avro-compat.sh --level BACKWARD schemas/"}]},
            "db-migrations": {"needs": "build-test", "runs-on": "ubuntu-latest",
                              "services": {"postgres": {"image": "postgres:16", "env": {"POSTGRES_PASSWORD": "${{ secrets.CI_DB_PASSWORD }}"},
                                                        "ports": ["5432:5432"]}},
                              "strategy": {"matrix": {"service": "${{ fromJSON(needs.detect-changes.outputs.services) }}"}},
                              "steps": [{"uses": "actions/checkout@v4"},
                                        {"name": "Validate Flyway migrations", "run": "mvn -B -pl services/${{ matrix.service }} flyway:validate -Pci-db"}]},
            "sbom": {"needs": "build-test", "runs-on": "ubuntu-latest",
                     "steps": [{"uses": "actions/checkout@v4"},
                               {"name": "Generate CycloneDX SBOM", "run": "mvn -B org.cyclonedx:cyclonedx-maven-plugin:makeAggregateBom"},
                               {"name": "Upload SBOM", "uses": "actions/upload-artifact@v4", "with": {"name": "sbom", "path": "target/bom.json"}}]},
            "deploy-dev": {"needs": "image", "runs-on": "ubuntu-latest", "environment": "dev",
                           "steps": [{"name": "Open GitOps pull request", "run": "./tools/gitops-bump.sh dev ${{ github.sha }}"}]},
            "smoke-dev": {"needs": "deploy-dev", "runs-on": "ubuntu-latest", "environment": "dev",
                          "steps": [{"uses": "actions/checkout@v4"},
                                    {"name": "Wait for Argo CD sync", "run": "./tools/argocd-wait.sh claims-hub-dev --timeout 900"},
                                    {"name": "Smoke tests", "run": "./tools/smoke.sh dev"}]},
            "notify": {"needs": ["smoke-dev"], "if": "failure()", "runs-on": "ubuntu-latest",
                       "steps": [{"name": "Post failure to the squad channel", "run": "./tools/notify-failure.sh \"${{ github.workflow }}\" \"${{ github.run_id }}\""}]},
        },
    }
    text = header(fid, [".github/workflows/claims-hub-ci.yml",
                        "Services built by this workflow: " + ", ".join(services),
                        "Production promotion is a separate, CAB-approved workflow."]) + ydump(wf)
    F.add("general", f"CI pipeline (2026-06-01) builds {len(services)} Claims Hub services including reserve-engine.",
          yloc("jobs.detect-changes.steps[1].with.filters"), "reserve-engine: services/reserve-engine/**",
          world_ref="SERVICE:reserve-engine#repo_path")
    F.add("general", "The CI pipeline runs Kafka consumer contract tests (ADR-023).",
          yloc("jobs.contract-tests.steps[2].name"), "Kafka consumer contract tests (ADR-023)", world_ref="ADR:ADR-023")
    F.add("general", "CI builds with Java 21 and pushes images to registry.corvane.internal/chub.",
          yloc("env"), "JAVA_VERSION: 21 REGISTRY: registry.corvane.internal/chub", world_ref="SYSTEM:SYS02#tech")
    return Built(fid, text.encode("utf-8"), F.items, f"{len(wf['jobs'])} rows")


# ---------------------------------------------------------------------------------------------
# ST052 Alerting rules
# ---------------------------------------------------------------------------------------------

def build_ST052(out_dir: pathlib.Path) -> Built:
    fid = "ST052"
    on = fdate(fid)
    F = Facts(fid, out_dir)

    def rule(alert, expr, for_, sev, team, summary, desc, runbook, ref=None):
        lab = {"severity": sev, "team": team}
        if ref:
            lab["ref"] = ref
        return {"alert": alert, "expr": expr, "for": for_, "labels": lab,
                "annotations": {"summary": summary, "description": desc,
                                "runbook_url": f"https://wiki.corvane.internal/display/CHUB/{runbook}"}}

    groups = [
        {"name": "integration-mq", "rules": [
            rule("MqRsvmoveQueueFilling", "ibmmq_queue_depth{queue=\"CLR.RSVMOVE.OUT\"} / ibmmq_queue_max_depth{queue=\"CLR.RSVMOVE.OUT\"} > 0.8",
                 "15m", "critical", "integration-platform", "CLR.RSVMOVE.OUT above 80% of its maximum depth",
                 "Consumers of CLX-IF-042 (CLX-IF-043, CLX-IF-044, CLX-IF-047, CLX-IF-049) may be stalled.",
                 "CLX-IF-042", "CLX-IF-042"),
            rule("MqChannelStopped", "ibmmq_channel_status{channel=~\"CLRQM01.TO.HUBQM01|HUBQM01.TO.CLRQM01\"} != 3",
                 "5m", "critical", "integration-platform", "MQ channel between CLRQM01 and HUBQM01 not running",
                 "Check channel status and retry count (see INC-2024-0243).", "MQ-Channels", "INC-2024-0243"),
            rule("MqBackoutQueueNotEmpty", "ibmmq_queue_depth{queue=~\"CLR\\\\..*\\\\.BOQ\"} > 0", "30m", "warning",
                 "integration-platform", "Messages parked on a backout queue", "Review parked messages each morning.",
                 "MQ-Backout"),
        ]},
        {"name": "integration-kafka", "rules": [
            rule("Clx049BridgeConsumerLag", "sum(kafka_consumergroup_lag{group=\"reserve-engine\",topic=\"claims.reserve.movement.v1\"}) > 20000",
                 "30m", "critical", "hub-squad-reserve-finance", "reserve-engine lagging on claims.reserve.movement.v1",
                 "Check the consumer count after restarts (INC-2026-0311).", "CLX-IF-049", "INC-2026-0311"),
            rule("KafkaUnderReplicatedPartitions", "sum(kafka_server_replicamanager_underreplicatedpartitions) > 0", "10m",
                 "warning", "integration-platform", "Under-replicated partitions on esp-prd", "Check broker health.", "ESP-Brokers"),
        ]},
        {"name": "reserve-engine", "rules": [
            rule("ReserveTier3ReviewsOverdue", "chub_reserve_tier3_reviews_overdue > 0", "1h", "warning",
                 "hub-squad-reserve-finance", "Tier-3 reserve reviews overdue",
                 "Tier-3 reserves are reviewed every 14 days (BR-RSV-007 v3). Compare config tier3-review-days with CLR.T_PARAM RSV_T3_REVIEW_DAYS (INC-2026-0702).",
                 "reserve-engine", "INC-2026-0702"),
            rule("ReserveLargeLossNotificationPending", "chub_reserve_large_loss_unnotified > 0", "2h", "critical",
                 "hub-squad-reserve-finance", "Large loss movement not yet notified to Reinsurance",
                 "Movements above £250,000 must be notified within 24 hours (BR-RSV-011 v2).", "reserve-engine", "BR-RSV-011"),
        ]},
        {"name": "fraud-referral-svc", "rules": [
            rule("FraudNoticeDeadlineAtRisk", "chub_fraud_notices_due_within_business_days{days=\"2\",status=\"DUE\"} > 0", "1h",
                 "warning", "hub-squad-fraud-settlement", "Customer notices due within 2 business days",
                 "Notices are due 10 business days after referral (BR-FRD-032 v2) unless deferred (BR-FRD-036).",
                 "fraud-referral-svc", "BR-FRD-032"),
            rule("FraudSiuTriageOverdue", "chub_fraud_referrals_untriaged_over_business_days{days=\"3\"} > 0", "1h", "warning",
                 "hub-squad-fraud-settlement", "Referrals not triaged by SIU within 3 business days",
                 "BR-FRD-035 v2 requires SIU triage within 3 business days.", "fraud-referral-svc", "BR-FRD-035"),
            rule("FraudAutoDeclineFlagOn", "chub_feature_flag{key=\"fraud.auto-decline\"} == 1", "0m", "critical",
                 "hub-squad-fraud-settlement", "Auto-decline flag switched on",
                 "Automatic decline on score is prohibited (BR-FRD-033, NISA Circular 2026/04 §3.1).", "fraud-referral-svc", "BR-FRD-033"),
        ]},
        {"name": "clara-batch", "rules": [
            rule("ClaraBatchJobAbended", "bsch_job_status{system=\"CLARA\",status=\"ABEND\"} == 1", "0m", "critical",
                 "batch-ops", "CLARA batch job abended", "Follow the CLARA batch runbook restart table.", "CLARA-Batch-Runbook"),
            rule("ClaraBatchWindowOverrun", "bsch_batch_window_remaining_minutes{system=\"CLARA\"} < 30", "5m", "warning",
                 "batch-ops", "CLARA batch close to the end of the window", "The batch window is 23:30–05:30 UK time.",
                 "CLARA-Batch-Runbook"),
        ]},
        {"name": "slo-claims-hub", "rules": [
            rule("ApiErrorBudgetBurn", "sum(rate(http_server_requests_seconds_count{status=~\"5..\"}[1h])) by (service) / sum(rate(http_server_requests_seconds_count[1h])) by (service) > 0.02",
                 "15m", "warning", "tech-delivery", "API error rate above SLO burn threshold", "SLOs per ADR-024.", "SLOs", "ADR-024"),
            rule("ApiLatencyHigh", "histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket[5m])) by (le, service)) > 1.5",
                 "15m", "warning", "tech-delivery", "p95 latency above 1.5 s", "SLOs per ADR-024.", "SLOs", "ADR-024"),
        ]},
    ]
    doc = {"apiVersion": "monitoring.coreos.com/v1", "kind": "PrometheusRule",
           "metadata": {"name": "claims-hub-alerts", "namespace": "chub-monitoring",
                        "labels": {"prometheus": "platform", "role": "alert-rules"}},
           "spec": {"groups": groups}}
    text = header(fid, ["PrometheusRule for Claims Hub and the CLARA integration estate. Routing: Alertmanager by team label."]) + ydump(doc)
    F.add("general", "Alert ReserveTier3ReviewsOverdue references INC-2026-0702 and the 14-day Tier-3 review (BR-RSV-007 v3).",
          yloc("spec.groups[2].rules[0].annotations.description"), "every 14 days (BR-RSV-007 v3)",
          world_ref="INCIDENT:INC-2026-0702")
    F.add("general", "Alert MqRsvmoveQueueFilling lists the CLX-IF-042 consumers CLX-IF-043, CLX-IF-044, CLX-IF-047 and CLX-IF-049.",
          yloc("spec.groups[0].rules[0].annotations.description"), "CLX-IF-043, CLX-IF-044, CLX-IF-047, CLX-IF-049",
          world_ref="INTERFACE:CLX-IF-042#dependents")
    F.add("general", "Alert Clx049BridgeConsumerLag watches reserve-engine on claims.reserve.movement.v1 (INC-2026-0311).",
          yloc("spec.groups[1].rules[0].labels.ref"), "INC-2026-0311", world_ref="INCIDENT:INC-2026-0311")
    F.add("general", "Alert FraudAutoDeclineFlagOn fires if fraud.auto-decline is switched on (BR-FRD-033).",
          yloc("spec.groups[3].rules[2].annotations.description"), "BR-FRD-033", world_ref="RULE:BR-FRD-033@v1")
    return Built(fid, text.encode("utf-8"), F.items, f"{sum(len(g['rules']) for g in groups)} rows")


BUILDERS = {
    "ST043": build_ST043, "ST044": build_ST044, "ST045": build_ST045, "ST046": build_ST046, "ST047": build_ST047,
    "ST048": build_ST048, "ST049": build_ST049, "ST050": build_ST050, "ST051": build_ST051, "ST052": build_ST052,
}
