"""NISA-FR1 figures computed from the referral data model behind ST015 (fraud referrals 2026).

The FR1 returns (ST038 for 2026Q2, ST034 for 2026Q3) must reconcile with the ST015 referral extract. We import
the sheets generator's ST015 model (sheets_lib.csv_files.st015_referrals over claims.generate_claims(); read-only
import) and aggregate its rows. We never read the CSV from disk: the two generators run in parallel.

Everything ST015 carries (region, product, tier, referral source, system, referral date, notice due date,
deferral flag) is aggregated as-is. Fields ST015 does not carry are derived per referral, deterministically
(rng keyed by referral id), so every breakdown still sums to the referral total:
- claim type and notification channel: from the ST013 claim when the referral is for a sample claim,
  otherwise drawn from the claims profile for the product (the same weights ST013 uses);
- notice issue lag (1-10 business days, never after the ST015 due date): splits the non-deferred notices into
  'within 5', '6-10' and 'pending at period end' (issue date after the period end);
- deferral length for deferred notices (12-58 days, inside the 60-day BR-FRD-036 v1 maximum).
"""
from __future__ import annotations

import datetime as dt
import functools

from generators.common import util

from .core import W

REGIONS = ["UK", "NO", "SE", "DK"]
LINES = ["Motor", "Home", "Commercial Property", "SME Liability"]
TIER_LABEL = {"1": "Tier-1", "2": "Tier-2", "3": "Tier-3"}
SOURCE_LABEL = {"ON": "online referral (ON)", "BS": "batch sweep (BS)", "MN": "manual referral (MN)"}
SYSTEMS = ["CLARA", "Claims Hub"]
CHANNEL_LABEL = {"PH": "telephone", "WB": "portal", "AP": "app", "BR": "broker", "TL": "telematics"}
TIMING = ["within 5 business days", "6-10 business days", "deferred (BR-FRD-036)", "pending at period end"]
LAG_WEIGHTS = [9, 14, 15, 13, 11, 9, 8, 8, 8, 5]   # notice issue lag 1..10 business days


@functools.lru_cache(maxsize=1)
def _source() -> tuple[list[dict], dict[str, dict]]:
    """ST015 rows (as written to the CSV, all values str) and the ST013 claims by claim id."""
    from generators.structured.sheets_lib import claims as C
    from generators.structured.sheets_lib import csv_files
    if hasattr(csv_files, "st015_referrals"):
        # the sheets generator's importable ST015 model (same rows build_st015 writes)
        claim_rows = C.generate_claims()
        raw = csv_files.st015_referrals(claim_rows)
        rows = [dict(zip(csv_files.REF_HEADER, ["" if v is None else str(v) for v in rec])) for rec in raw]
    else:
        # older sheets_lib: run its builders up to ST015 with an empty --only set (nothing is written)
        from generators.structured.sheets_lib.ctx import Ctx
        ctx = Ctx(util.UPLOAD / "structured", set())
        for build in csv_files.CSV_BUILDERS:
            build(ctx)
            if build is csv_files.build_st015:
                break
        else:  # pragma: no cover - the sheets generator changed shape
            raise RuntimeError("sheets_lib.csv_files.CSV_BUILDERS has no build_st015")
        rows, claim_rows = ctx.data["ST015:rows"], ctx.data["claims"]
    claims = {x["claim_id"]: x for x in claim_rows}
    return rows, claims


def _add_weekdays(d: dt.date, n: int) -> dt.date:
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def _derive(row: dict, claims: dict[str, dict]) -> dict:
    from generators.structured.sheets_lib import claims as C
    r = util.rng(f"FR1:{row['referral_id']}")
    prod = row["product_code"]
    cl = claims.get(row["claim_id"])
    if cl is not None:
        ct, ch = cl["claim_type"], cl["channel"]
    else:
        cts, cw = C.claim_types_for(prod)
        ct = r.choices(cts, weights=cw)[0]
        chans = list(W.claims_profile["channels"])
        ch = r.choices(chans, weights=[W.claims_profile["channels"][c] for c in chans])[0]
    lag = r.choices(range(1, 11), weights=LAG_WEIGHTS)[0]
    defer_days = r.randint(12, 58)
    rd = dt.date.fromisoformat(row["referral_date"])
    due = dt.date.fromisoformat(row["customer_notice_due"])
    issue = min(_add_weekdays(rd, lag), due)
    return {"claim_type": ct, "channel": ch, "lag": lag, "issue": issue, "due": due, "rd": rd,
            "defer_days": defer_days}


def _count(keys, values) -> dict:
    out = {k: 0 for k in keys}
    for v in values:
        out[v] += 1
    return out


def quarter(start: str, end: str) -> dict:
    """All FR1 figures for referrals dated start..end (inclusive), reconciled with ST015."""
    rows, claims = _source()
    q = [x for x in rows if start <= x["referral_date"] <= end]
    e0 = dt.date.fromisoformat(end)
    s0 = dt.date.fromisoformat(start)
    der = {x["referral_id"]: _derive(x, claims) for x in q}
    months = sorted({x["referral_date"][:7] for x in q})
    line_of = {p: W.products[p]["line"] for p in W.products}

    timing = []
    for x in q:
        dx = der[x["referral_id"]]
        if x["notice_deferred"] == "Y":
            timing.append(TIMING[2])
        elif dx["issue"] > e0:
            timing.append(TIMING[3])
        elif dx["lag"] <= 5:
            timing.append(TIMING[0])
        else:
            timing.append(TIMING[1])
    nt = _count(TIMING, timing)

    products = [p for p in W.products if any(x["product_code"] == p for x in q)]
    ctypes = [c for c in W.claim_types if any(der[x["referral_id"]]["claim_type"] == c for x in q)]

    weeks = []
    cur = s0
    while cur <= e0:
        we = min(cur + dt.timedelta(days=6 - cur.weekday()), e0)
        n = sum(1 for x in q if cur.isoformat() <= x["referral_date"] <= we.isoformat())
        weeks.append({"weekStart": cur.isoformat(), "weekEnd": we.isoformat(), "referrals": n})
        cur = we + dt.timedelta(days=1)

    deferrals = []
    for x in q:
        if x["notice_deferred"] != "Y":
            continue
        dx = der[x["referral_id"]]
        deferrals.append({"claimRef": x["claim_id"], "region": x["region"], "product": x["product_code"],
                          "tier": TIER_LABEL[x["tier"]], "referralDate": x["referral_date"],
                          "noticeDueDate": x["customer_notice_due"], "deferralDays": dx["defer_days"],
                          "deferredUntil": (dx["due"] + dt.timedelta(days=dx["defer_days"])).isoformat(),
                          "reason": "SIU certified tipping-off risk"})
    deferrals.sort(key=lambda d_: (d_["referralDate"], d_["claimRef"]))

    by_region = _count(REGIONS, [x["region"] for x in q])
    by_line = _count(LINES, [line_of[x["product_code"]] for x in q])
    by_tier = _count(TIER_LABEL.values(), [TIER_LABEL[x["tier"]] for x in q])
    out = {
        "total": len(q),
        "byRegion": by_region,
        "byLine": by_line,
        "byTier": by_tier,
        "bySource": _count(SOURCE_LABEL.values(), [SOURCE_LABEL[x["referral_source"]] for x in q]),
        "bySystem": _count(SYSTEMS, [x["system"] for x in q]),
        "byMonth": _count(months, [x["referral_date"][:7] for x in q]),
        "byProduct": [{"product": p, "name": W.products[p]["name"], "region": W.products[p]["region"],
                       "referrals": sum(1 for x in q if x["product_code"] == p)} for p in products],
        "byClaimType": [{"claimType": c, "name": W.claim_types[c]["name"],
                         "referrals": sum(1 for x in q if der[x["referral_id"]]["claim_type"] == c)} for c in ctypes],
        "byChannel": _count(CHANNEL_LABEL.values(), [CHANNEL_LABEL[der[x["referral_id"]]["channel"]] for x in q]),
        "noticeTiming": nt,
        "customerNotices": {"issuedWithin10BusinessDays": nt[TIMING[0]] + nt[TIMING[1]], "deferred": nt[TIMING[2]],
                            "pendingAtPeriodEnd": nt[TIMING[3]]},
        "byRegionAndMonth": {rg: _count(months, [x["referral_date"][:7] for x in q if x["region"] == rg])
                             for rg in REGIONS},
        "byLineAndTier": {ln: _count(TIER_LABEL.values(), [TIER_LABEL[x["tier"]] for x in q
                                                           if line_of[x["product_code"]] == ln]) for ln in LINES},
        "weekly": weeks,
        "deferrals": deferrals,
        "hubProducts": sorted({x["product_code"] for x in q if x["system"] == "Claims Hub"}),
    }
    _check(out)
    return out


def _check(f: dict) -> None:
    """Every breakdown sums to the total; the deferral annex, notices and timing agree."""
    t = f["total"]
    for k in ("byRegion", "byLine", "byTier", "bySource", "bySystem", "byMonth", "byChannel", "noticeTiming"):
        assert sum(f[k].values()) == t, (k, f[k], t)
    for k in ("byProduct", "byClaimType"):
        assert sum(x["referrals"] for x in f[k]) == t, k
    assert sum(f["customerNotices"].values()) == t
    assert sum(w["referrals"] for w in f["weekly"]) == t
    assert len(f["deferrals"]) == f["customerNotices"]["deferred"] == f["noticeTiming"][TIMING[2]]
    for rg in REGIONS:
        assert sum(x["referrals"] for x in f["byProduct"] if x["region"] == rg) == f["byRegion"][rg], rg
        assert sum(f["byRegionAndMonth"][rg].values()) == f["byRegion"][rg], rg
    for ln in LINES:
        assert sum(f["byLineAndTier"][ln].values()) == f["byLine"][ln], ln
    for tr in TIER_LABEL.values():
        assert sum(f["byLineAndTier"][ln][tr] for ln in LINES) == f["byTier"][tr], tr
    for m in f["byMonth"]:
        assert sum(f["byRegionAndMonth"][rg][m] for rg in REGIONS) == f["byMonth"][m], m
    assert all(0 < d_["deferralDays"] <= 60 for d_ in f["deferrals"])
