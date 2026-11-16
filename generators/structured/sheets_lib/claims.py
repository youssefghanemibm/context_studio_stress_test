"""Synthetic claims population (ST013) and the event streams derived from it.

The 15,000-row claims extract is generated from world/data/claims_profile.yaml with seeded rng.
Movements (ST004/ST014), payments (ST016), recoveries (ST017) and assessor assignments (ST018)
are simulated per claim from the same rows so that the files join on claim_id and agree with
each other (closed claims have no later activity, payments never exceed paid_to_date, ...).
"""
from __future__ import annotations

import bisect
import datetime as dt
import math
from functools import lru_cache

from .common import D, W, add_bd, batch_window, first_bd_of_month, iso, next_weekday, rng

P = W.claims_profile
LOSS_FROM = D(P["date_range"]["loss_date_from"])
LOSS_TO = D(P["date_range"]["loss_date_to"])
EXTRACT_DATE = D("2026-11-02")
LAST_DAY = D("2026-10-31")

LINE_OF = {pid: p["line"] for pid, p in W.products.items()}
REGION_OF = {pid: p["region"] for pid, p in W.products.items()}
CCY = P["currency_by_region"]
PRODUCT_CODE = {pid: p["code"] for pid, p in W.products.items()}

# migration to Claims Hub (timeline.migration_waves)
MIGRATION = {}
for w in W.waves.values():
    if w["status"] == "complete":
        for pid in [x.strip() for x in w["scope"].split("(")[-1].rstrip(")").split(",")] if "(" in w["scope"] else [w["scope"]]:
            MIGRATION[pid] = D(w["date"])


def on_hub(product: str, d: dt.date) -> bool:
    m = MIGRATION.get(product)
    return bool(m and d >= m)


# ---------------------------------------------------------------------------------------------
# FX (quarter-end rate of the loss quarter; latest available for an unfinished quarter)
# ---------------------------------------------------------------------------------------------

FX_DATES = sorted(P["fx_to_gbp_quarter_end"])


def quarter_end(d: dt.date) -> dt.date:
    q = (d.month - 1) // 3
    m = 3 * q + 3
    nd = dt.date(d.year + (m == 12), 1 if m == 12 else m + 1, 1)
    return nd - dt.timedelta(days=1)


def fx_rate(ccy: str, d: dt.date) -> float:
    if ccy == "GBP":
        return 1.0
    qe = iso(quarter_end(d))
    keys = [k for k in FX_DATES if k <= qe]
    k = keys[-1] if keys else FX_DATES[0]
    return float(P["fx_to_gbp_quarter_end"][k][ccy])


def fx_latest(ccy: str) -> float:
    if ccy == "GBP":
        return 1.0
    return float(P["fx_to_gbp_quarter_end"][FX_DATES[-1]][ccy])


# ---------------------------------------------------------------------------------------------
# Rules applied by the generator (all taken from the world model)
# ---------------------------------------------------------------------------------------------

def tier_for(est_gbp: float, est_local: float, ccy: str, claim_type: str, loss_date: dt.date) -> int:
    """BR-TRI-003 at loss_date (v2 before 2025-01-01, v3 from 2025-01-01)."""
    v = W.rule_version("BR-TRI-003", iso(loss_date))
    prm = v["parameters"]
    if claim_type == "CT-BIJ":
        return 3
    if ccy == "GBP":
        t3 = est_gbp >= prm["tier3_min_gbp"]
    else:
        t3 = est_local >= prm[f"tier3_min_{ccy.lower()}"]
    if t3:
        return 3
    if est_gbp >= prm["tier2_min_gbp"] or claim_type in ("CT-TPD", "CT-PLB"):
        return 2
    return 1


REFERRAL_RULES = [(D(x["from"]), D(x["to"]), x["rule"]) for x in P["referral_rule_by_date"]]


def referral_rule_at(d: dt.date) -> str | None:
    for a, b, rule in REFERRAL_RULES:
        if a <= d <= b:
            return rule
    return None


def rule_label(rule_ref: str) -> str:
    rid, v = rule_ref.split("@v")
    return f"{rid} v{v}"


def refer(score: int, tier: int, d: dt.date) -> tuple[bool, str | None]:
    rule = referral_rule_at(d)
    if rule is None:
        return False, None
    rid, ver = rule.split("@v")
    prm = W.rules[rid]["versions"][int(ver) - 1]["parameters"]
    th = prm["threshold"]
    ok = score >= th
    if not ok and "tier3_threshold" in prm and tier == 3 and score >= prm["tier3_threshold"]:
        ok = True
    return ok, (rule if ok else None)


def threshold_for(rule: str, tier: int, score: int) -> int:
    """The referral threshold that applied to the claim: a rule's Tier-3 threshold applies to every Tier-3 claim
    (whatever its score), the general threshold to every other claim."""
    rid, ver = rule.split("@v")
    prm = W.rules[rid]["versions"][int(ver) - 1]["parameters"]
    if "tier3_threshold" in prm and tier == 3:
        return prm["tier3_threshold"]
    return prm["threshold"]


# ---------------------------------------------------------------------------------------------
# Sampling helpers
# ---------------------------------------------------------------------------------------------

def wchoice(r, items: list, weights: list[float]):
    tot = sum(weights)
    x = r.random() * tot
    acc = 0.0
    for it, w in zip(items, weights):
        acc += w
        if x < acc:
            return it
    return items[-1]


def lognorm_gbp(r, ct: str) -> float:
    g = P["incurred_gbp_ranges"][ct]
    mu = math.log(g["median"])
    sigma = math.log(g["p95"] / g["median"]) / 1.6449
    for _ in range(20):
        x = math.exp(r.gauss(mu, sigma))
        if g["min"] <= x <= g["max"]:
            return x
    return min(max(x, g["min"]), g["max"])


SEASON = {
    "CT-FRO": {1: 4.0, 2: 4.0, 3: 1.5, 12: 1.5, "other": 0.25},
    "CT-SNO": {1: 4.0, 2: 4.0, 3: 4.0, 12: 1.5, "other": 0.15},
    "CT-STM": {11: 2.2, 12: 2.2, 1: 2.2, 2: 2.2, "other": 1.0},
    "CT-EOW": {12: 2.0, 1: 2.0, 2: 2.0, "other": 1.0},
}
MONTHS = []
_y, _m = LOSS_FROM.year, LOSS_FROM.month
while (_y, _m) <= (LOSS_TO.year, LOSS_TO.month):
    MONTHS.append((_y, _m))
    _m += 1
    if _m == 13:
        _y, _m = _y + 1, 1


def month_days(y, m):
    nd = dt.date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return (nd - dt.timedelta(days=1)).day


@lru_cache(maxsize=None)
def _month_weights(ct: str):
    s = SEASON.get(ct)
    out = []
    for i, (y, m) in enumerate(MONTHS):
        w = month_days(y, m) * (1.0 + 0.006 * i)  # mild book growth
        if s:
            w *= s.get(m, s["other"])
        out.append(w)
    return out


def sample_loss_date(r, ct: str) -> dt.date:
    y, m = wchoice(r, MONTHS, _month_weights(ct))
    return dt.date(y, m, r.randint(1, month_days(y, m)))


def claim_types_for(product: str) -> tuple[list[str], list[float]]:
    line = LINE_OF[product]
    weights = P["claim_type_weights"][line]
    allowed = W.products[product]["claim_types"]
    cts = [c for c in allowed if c in weights]
    return cts, [weights[c] for c in cts]


POP_PER_YEAR = {"UK": 151000, "NO": 26000, "SE": 21000, "DK": 15500}
SEQ_BASE = 100000


# ---------------------------------------------------------------------------------------------
# ST013 rows
# ---------------------------------------------------------------------------------------------

def generate_claims() -> list[dict]:
    r = rng("ST013:claims")
    n_rows = int(P["rows"])
    products = list(P["products"].keys())
    pweights = [P["products"][p] for p in products]
    chan_items = list(P["channels"].keys())
    chan_w = [P["channels"][c] for c in chan_items]
    aa = P["assessor_assignment"]

    handlers = {}
    hr = rng("ST013:handlers")
    pool = hr.sample(range(1000, 10000), 160 + 30 + 25 + 20)
    handlers["UK"], handlers["NO"], handlers["SE"], handlers["DK"] = (
        pool[:160], pool[160:190], pool[190:215], pool[215:235])

    rows = []
    for i in range(n_rows):
        prod = wchoice(r, products, pweights)
        line = LINE_OF[prod]
        region = REGION_OF[prod]
        ccy = CCY[region]
        cts, cw = claim_types_for(prod)
        ct = wchoice(r, cts, cw)
        loss = sample_loss_date(r, ct)
        x = r.random()
        lag = 0 if x < 0.55 else 1 if x < 0.75 else r.randint(2, 7) if x < 0.93 else r.randint(8, 30)
        notified = min(loss + dt.timedelta(days=lag), LAST_DAY)
        sub_region = r.choice(P["sub_regions"][region])
        if line == "Motor":
            ch = wchoice(r, chan_items, chan_w)
        else:
            ch = wchoice(r, chan_items[:-1], chan_w[:-1]) if chan_items[-1] == "TL" else wchoice(r, chan_items, chan_w)
        est_gbp = lognorm_gbp(r, ct)
        rate = fx_rate(ccy, loss)
        est_local = est_gbp / rate
        tier = tier_for(est_gbp, est_local, ccy, ct, loss)

        # status
        age = (LAST_DAY - notified).days
        if loss >= D("2026-08-01"):
            sw = {"OP": 0.80, "CS": 0.12, "CN": 0.06, "RO": 0.0, "RC": 0.02}
        else:
            op = 0.119 * (1.8 if age < 180 else 1.0 if age < 450 else 0.45)
            if ct == "CT-BIJ" or tier == 3:
                op *= 2.5
            sw = {"OP": op, "CS": 0.692, "CN": 0.115, "RO": 0.022, "RC": 0.053}
        status = wchoice(r, list(sw), list(sw.values()))
        closed = None
        if status in ("CS", "CN"):
            med = {"Motor": 25, "Home": 35, "Commercial Property": 60, "SME Liability": 120}[line]
            if ct == "CT-BIJ":
                med *= 4
            for k in range(6):
                l2 = max(1, int(math.exp(r.gauss(math.log(med), 0.7)) / (1 + k)))
                cd = notified + dt.timedelta(days=l2)
                if cd <= LAST_DAY:
                    closed = cd
                    break
            if closed is None:
                status = "OP"
        if status == "RC" and age < 20:
            status = "OP"

        # amounts (local currency)
        incurred = round(est_local, 2)
        if status == "CN":
            reserve = paid = incurred = 0.0
        else:
            lo, hi = P["reserve_share_of_incurred"][status]
            share = lo + (hi - lo) * r.random() if hi > lo else lo
            reserve = round(incurred * share, 2)
            paid = round(incurred - reserve, 2)
        incurred = round(reserve + paid, 2)
        incurred_gbp = round(incurred * rate, 2) if ccy != "GBP" else incurred

        # fraud score (beta(2.2, 6.5) scaled 0-100; linked-claim uplift)
        score = round(r.betavariate(2.2, 6.5) * 100)
        if r.random() < (0.10 if ct in ("CT-THF", "CT-BIJ") else 0.05):
            score = min(100, score + int(P["sentinel_score"]["linked_claim_uplift"]))

        # assessor
        if ct == "CT-WSC" or (tier == 1 and line != "Motor" and r.random() < 0.25):
            atype = "desk"
        elif r.random() < aa["internal_share_by_line"][line]:
            atype = "internal"
        else:
            atype = "vendor"
        if atype in ("internal", "desk"):
            aref = r.choice(aa["internal_refs"][region])
        else:
            if region == "UK":
                fell = tier == 3 and notified < D("2026-02-01") and r.random() < 0.55
                aref = W.vendors["VEN-03" if fell else "VEN-01"]["code"]
            else:
                aref = W.vendors["VEN-02"]["code"]
        handler = f"H-{r.choice(handlers[region])}"
        rec = "Y" if (status == "RC" or r.random() < P["recovery_flag_share"][line]) else "N"
        rows.append({
            "_i": i, "product_code": prod, "claim_type": ct, "region": region, "sub_region": sub_region,
            "channel": ch, "loss_date": loss, "notified_date": notified, "status": status, "tier": tier,
            "currency": ccy, "reserve_outstanding": reserve, "paid_to_date": paid, "incurred": incurred,
            "incurred_gbp": incurred_gbp, "sentinel_score": score, "assessor_type": atype,
            "assessor_ref": aref, "handler_ref": handler, "recovery_flag": rec, "closed_date": closed,
            "_est_gbp": est_gbp, "_est_local": est_local, "_line": line, "_rate": rate,
        })

    _ensure_tier3_band(rows)
    for row in rows:
        ok, rule = refer(row["sentinel_score"], row["tier"], row["notified_date"])
        row["fraud_referred"] = "Y" if ok else "N"
        row["referral_rule"] = rule_label(rule) if rule else ""
    _assign_ids(rows)
    rows.sort(key=lambda x: (x["notified_date"], x["claim_id"]))
    for k, row in enumerate(rows, 1):
        row["_row"] = k
    return rows


def _ensure_tier3_band(rows: list[dict]) -> None:
    """Guarantee a handful of Tier-3 claims scored 60-64 under BR-FRD-031 v2 (and Tier-1/2 controls)."""
    r = rng("ST013:band")
    v2_from = D("2026-10-01")
    t3 = [x for x in rows if x["notified_date"] >= v2_from and x["tier"] == 3]
    have = [x for x in t3 if 60 <= x["sentinel_score"] <= 64]
    want = 5
    cand = [x for x in t3 if x["sentinel_score"] < 60]
    r.shuffle(cand)
    for x in cand[: max(0, want - len(have))]:
        x["sentinel_score"] = r.randint(60, 64)
    lo = [x for x in rows if x["notified_date"] >= v2_from and x["tier"] in (1, 2)]
    have_lo = [x for x in lo if 60 <= x["sentinel_score"] <= 64]
    cand = [x for x in lo if x["sentinel_score"] < 60]
    r.shuffle(cand)
    for x in cand[: max(0, 4 - len(have_lo))]:
        x["sentinel_score"] = r.randint(60, 64)
    pre = [x for x in rows if D("2026-04-01") <= x["notified_date"] < v2_from and x["tier"] == 3]
    have_pre = [x for x in pre if 60 <= x["sentinel_score"] <= 64]
    cand = [x for x in pre if x["sentinel_score"] < 60]
    r.shuffle(cand)
    for x in cand[: max(0, 3 - len(have_pre))]:
        x["sentinel_score"] = r.randint(60, 64)


SAMPLE_SEQS: dict[tuple[str, int], set[int]] = {}


def _assign_ids(rows: list[dict]) -> None:
    r = rng("ST013:ids")
    groups: dict[tuple[str, int], list[dict]] = {}
    for x in rows:
        groups.setdefault((x["region"], x["notified_date"].year), []).append(x)
    for key in sorted(groups):
        g = groups[key]
        g.sort(key=lambda x: (x["notified_date"], x["_i"]))
        region, year = key
        days = 365 if year < 2026 else 304
        pop = int(POP_PER_YEAR[region] * days / 365)
        seqs = sorted(r.sample(range(1, pop), len(g)))
        SAMPLE_SEQS[key] = set(seqs)
        for x, s in zip(g, seqs):
            num = SEQ_BASE + s
            x["claim_id"] = f"CLM-{region}-{year}-{num:06d}"
            x["legacy_claim_id"] = f"{region}{year}{num:06d}"


ST013_COLUMNS = list(P["columns"])


def st013_record(x: dict) -> list:
    out = []
    for c in ST013_COLUMNS:
        v = x[c]
        if isinstance(v, dt.date):
            v = iso(v)
        elif v is None:
            v = ""
        elif c in ("reserve_outstanding", "paid_to_date", "incurred", "incurred_gbp"):
            v = f"{v:.2f}"
        out.append(v)
    return out


# ---------------------------------------------------------------------------------------------
# Population claim ids outside the sample (for the company-wide referral extract ST015)
# ---------------------------------------------------------------------------------------------

class IdPool:
    def __init__(self, key: str):
        self.r = rng(key)
        self.used: dict[tuple[str, int], set[int]] = {k: set(v) for k, v in SAMPLE_SEQS.items()}

    def claim_id(self, region: str, d: dt.date) -> tuple[str, str]:
        year = d.year
        pop = POP_PER_YEAR[region]
        doy = (d - dt.date(year, 1, 1)).days
        used = self.used.setdefault((region, year), set())
        centre = int(pop * doy / 365)
        while True:
            s = max(1, centre + self.r.randint(-400, 400))
            if s not in used:
                used.add(s)
                break
        num = SEQ_BASE + s
        return f"CLM-{region}-{year}-{num:06d}", f"{region}{year}{num:06d}"


# ---------------------------------------------------------------------------------------------
# Derived event streams
# ---------------------------------------------------------------------------------------------

def life_end(x: dict) -> dt.date:
    return x["closed_date"] or LAST_DAY


def reserve_types(x: dict) -> list[str]:
    out = ["ID"]
    if x["assessor_type"] == "vendor" or x["tier"] >= 2:
        out.append("EX")
    if x["claim_type"] in ("CT-BIJ", "CT-PLB"):
        out.append("LG")
    return out


def tier3_cadence(d: dt.date) -> int:
    v = W.rule_version("BR-RSV-007", iso(d))
    return int(v["parameters"]["review_days"])


CLARA_MOVE_PGM = {"IN_FNOL": "CLRFN030", "IN": "CLRRS010", "AD": "CLRRS020", "RV": "CLRRS110",
                  "IX": "CLRRS130", "ST": "CLRST040", "RC": "CLRRC050", "CORR": "CLRRS150"}
HUB_SERVICE = "reserve-engine"


def movements(rows: list[dict], start: dt.date, end: dt.date, key: str) -> list[dict]:
    """Reserve movements for sample claims dated within [start, end]."""
    r = rng(f"moves:{key}")
    out = []
    for x in rows:
        if x["notified_date"] > end or life_end(x) < start:
            continue
        if x["status"] == "CN" and x["closed_date"] and x["closed_date"] < start:
            continue
        cr = rng(f"moves:claim:{x['claim_id']}")
        base_rsv = 3000000000 + x["_i"] * 10
        est = x["_est_local"]
        for k, rt in enumerate(reserve_types(x)):
            rsv_id = base_rsv + k
            share = {"ID": 1.0, "EX": 0.08, "LG": 0.15}[rt]
            outstanding = 0.0
            evs = []  # (date, type, amount, pgm_key)
            d0 = x["notified_date"]
            init = round(est * share * (0.55 + 0.45 * cr.random()), 2)
            if rt == "ID":
                evs.append((d0, "IN", init, "IN_FNOL"))
            else:
                evs.append((d0 + dt.timedelta(days=cr.randint(1, 6)), "IN", init, "IN"))
            d_end = life_end(x)
            # adjustments
            d = d0
            rate_days = 21 if x["tier"] == 3 else 26
            while True:
                d = d + dt.timedelta(days=max(2, int(cr.expovariate(1 / rate_days))))
                if d >= d_end:
                    break
                evs.append((d, "AD", None, "AD"))
            # tier-3 reviews at the cadence in force (BR-RSV-007)
            if x["tier"] == 3 and rt == "ID":
                d = d0
                while True:
                    d = d + dt.timedelta(days=tier3_cadence(d))
                    if d >= d_end:
                        break
                    evs.append((d, "RV", None, "RV"))
            # monthly indexation for bodily-injury reserves (first business day)
            if x["claim_type"] == "CT-BIJ" and rt in ("ID", "LG"):
                y, m = d0.year, d0.month
                while True:
                    m += 1
                    if m == 13:
                        y, m = y + 1, 1
                    dd = first_bd_of_month(y, m)
                    if dd >= d_end:
                        break
                    evs.append((dd, "IX", None, "IX"))
            if x["recovery_flag"] == "Y" and rt == "ID" and x["status"] in ("RC", "CS", "RO"):
                dd = d0 + dt.timedelta(days=cr.randint(20, 120))
                if dd < d_end:
                    evs.append((dd, "RC", None, "RC"))
            if x["closed_date"]:
                evs.append((x["closed_date"], "ST", None, "ST"))
            evs.sort(key=lambda e: (e[0], {"IN": 0, "AD": 1, "IX": 2, "RV": 3, "RC": 4, "ST": 5}[e[1]]))
            seq = 0
            for d, typ, amt, pk in evs:
                if typ == "IN":
                    amt = init
                elif typ == "AD":
                    amt = round(outstanding * cr.uniform(-0.25, 0.30), 2)
                elif typ == "RV":
                    amt = round(outstanding * cr.choice([0.0, 0.0, cr.uniform(-0.1, 0.12)]), 2)
                elif typ == "IX":
                    amt = round(outstanding * cr.uniform(0.0015, 0.0040), 2)
                elif typ == "RC":
                    amt = round(-outstanding * cr.uniform(0.05, 0.25), 2)
                elif typ == "ST":
                    amt = round(-outstanding, 2)
                outstanding = round(outstanding + amt, 2)
                seq += 1
                if not (start <= d <= end):
                    continue
                if pk == "AD" and cr.random() < 0.006:
                    pk = "CORR"
                hub = on_hub(x["product_code"], d)
                pgm = HUB_SERVICE if hub else CLARA_MOVE_PGM[pk]
                hh = cr.randint(7, 19) if typ in ("IN", "AD", "RC") else 1
                mm = cr.randint(0, 59)
                if typ in ("RV", "IX") and not hub:
                    hh, mm = 1, cr.randint(30, 59)
                ss = cr.randint(0, 59)
                win = None if hub else batch_window(pgm)
                if win:
                    # batch-only program: inside its JCL job's run window (same draws, so amounts are unchanged)
                    start_min, elapsed = win
                    hh, mm = divmod(start_min + (hh * 60 + mm) % elapsed, 60)
                ts = dt.datetime(d.year, d.month, d.day, hh, mm, ss)
                rate = fx_latest(x["currency"]) if d >= D("2026-07-01") else fx_rate(x["currency"], d)
                out.append({
                    "movement_id": f"{base_rsv * 100 + seq}",
                    "claim_id": x["claim_id"], "reserve_id": str(rsv_id), "reserve_type": rt,
                    "movement_ts": ts, "movement_type": typ, "currency": x["currency"], "amount": amt,
                    "amount_gbp": round(amt * rate, 2), "product_code": x["product_code"], "region": x["region"],
                    "tier": x["tier"], "source_system": "Claims Hub" if hub else "CLARA",
                    "program_or_service": pgm, "user_id": (x["handler_ref"] if typ in ("IN", "AD") and pk != "IN_FNOL" else "BATCH"),
                    "_claim": x,
                })
    out.sort(key=lambda m: (m["movement_ts"], m["movement_id"]))
    return out


PAYEE_VENDOR = {
    ("Motor", "UK"): "THISTLCB", ("Motor", "NO"): "VARDHOLM", ("Home", "UK"): "KILNMOOR",
}


def payments(rows: list[dict], start: dt.date, end: dt.date, key: str) -> list[dict]:
    """Payments within [start, end]; per-claim totals never exceed paid_to_date."""
    out = []
    for x in rows:
        if x["paid_to_date"] <= 0 or x["notified_date"] > end or life_end(x) < start:
            continue
        cr = rng(f"pay:claim:{x['claim_id']}")
        paid = x["paid_to_date"]
        line = x["_line"]
        k = 1 + min(6, int(cr.expovariate(1 / (1.6 if line == "Motor" else 2.2))))
        if x["tier"] == 3:
            k += 2
        d0 = x["notified_date"] + dt.timedelta(days=cr.randint(2, 15))
        d1 = life_end(x)
        if d0 > d1:
            d0 = d1
        span = (d1 - d0).days
        dates = sorted(d0 + dt.timedelta(days=cr.randint(0, max(0, span))) for _ in range(k))
        cuts = sorted(cr.random() for _ in range(k - 1))
        parts = [b - a for a, b in zip([0.0] + cuts, cuts + [1.0])]
        amts = [round(paid * p, 2) for p in parts]
        amts[-1] = round(paid - sum(amts[:-1]), 2)
        payees = []
        for j in range(k):
            pv = PAYEE_VENDOR.get((line, x["region"]))
            if j == 0 and x["assessor_type"] == "vendor" and x["assessor_ref"] == "BRACKFLD":
                payees.append(("vendor_fee", "BRACKFLD"))
            elif pv and cr.random() < 0.55:
                payees.append(("repairer", pv))
            elif x["claim_type"] in ("CT-BIJ", "CT-PLB") and cr.random() < 0.2:
                payees.append(("solicitor", "RAVPIKE" if x["region"] == "UK" else "CLAIMANT"))
            else:
                payees.append(("claimant", "CLAIMANT"))
        # fixed vendor fees from vendors.yaml (Brackenfield only; Norrvik fees are never shown)
        if payees and payees[0][0] == "vendor_fee":
            fees = W.vendors["VEN-01"]["fees"]
            fee = fees["site_visit_gbp"] if x["tier"] >= 2 else fees["desk_assessment_gbp"]
            if amts[0] >= fee and k > 1:
                diff = round(amts[0] - fee, 2)
                amts[0] = float(fee)
                amts[1] = round(amts[1] + diff, 2)
            else:
                payees[0] = ("claimant", "CLAIMANT")
        for j, (d, a, (ptype, pref)) in enumerate(zip(dates, amts, payees)):
            hub = on_hub(x["product_code"], d)
            if not hub:
                d = next_weekday(d)
                if x["closed_date"] and d > x["closed_date"]:
                    d = x["closed_date"]
                    while d.weekday() >= 5:
                        d -= dt.timedelta(days=1)
            if not (start <= d <= end) or a <= 0:
                continue
            status = "CONFIRMED"
            if d >= end - dt.timedelta(days=1):
                status = "SENT"
            out.append({
                "claim": x, "date": d, "payee_type": ptype, "payee_ref": pref, "amount": a,
                "currency": x["currency"], "hub": hub, "status": status, "seq": j,
            })
    out.sort(key=lambda p: (p["date"], p["claim"]["claim_id"], p["seq"]))
    return out
