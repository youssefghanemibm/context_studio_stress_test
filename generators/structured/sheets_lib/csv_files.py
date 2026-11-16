"""CSV extracts ST013-ST026."""
from __future__ import annotations

import datetime as dt
import math
import re

from . import claims as C
from .common import (D, W, add_bd, adate, csv_text, iso, may, money, next_weekday, pname, program_id_asof,
                     placement, require, rng, svcname, sysname, team_name, temporalize)

NON_MOTOR = [p for p, x in W.products.items() if x["line"] != "Motor"]


def _d(v) -> str:
    return iso(v) if isinstance(v, dt.date) else ("" if v is None else str(v))


# =============================================================================================
# ST013 claims extract
# =============================================================================================

def build_st013(ctx):
    fid = "ST013"
    rows = C.generate_claims()
    ctx.data["claims"] = rows
    header = C.ST013_COLUMNS
    recs = [C.st013_record(x) for x in rows]
    R = ctx.write_csv(fid, header, recs)
    pl_tier = placement(fid, "st13_agg_tier")
    pl_t360 = placement(fid, "st13_agg_t3_60")
    sup = "supports PL-162 (aggregates of the claims extract)"

    def cnt(v):
        return f"{v:,}"

    ctx.agg(fid, {}, "count", lambda v: f"The synthetic claims extract 2024-2026 contains exactly {v:,} claim rows.",
            needle_col="claim_id", notes="row count of ST013", world_ref="PROFILE:rows")
    ctx.agg(fid, {"product_code": "PRD-HOM-UK", "claim_type": "CT-EOW", "tier": "3"}, "count",
            lambda v: f"The claims extract holds {cnt(v)} Tier-3 Escape of Water (CT-EOW) claims on Home Buildings & Contents UK (PRD-HOM-UK).",
            placement=pl_tier)
    combos = [("CT-EOW", "UK", "2025", "Escape of Water"), ("CT-COL", "UK", "2024", "Collision"),
              ("CT-FRO", "NO", "2026", "Frost Damage"), ("CT-STM", "SE", "2025", "Storm"),
              ("CT-THF", "DK", "2025", "Theft"), ("CT-SNO", "NO", "2024", "Snow Load"),
              ("CT-BIJ", "UK", "2026", "Bodily Injury"), ("CT-WSC", "SE", "2026", "Windscreen")]
    for ct, reg, yr, nm in combos:
        ctx.agg(fid, {"claim_type": ct, "region": reg, "loss_date": {"prefix": yr}}, "count",
                lambda v, ct=ct, reg=reg, yr=yr, nm=nm: f"The claims extract has {cnt(v)} {nm} ({ct}) claims in region {reg} with a loss date in {yr}.",
                notes=sup)
    ctx.agg(fid, {"claim_type": "CT-SUB", "region": "DK"}, "count",
            lambda v: f"There are {v} Subsidence (CT-SUB) claims in Denmark in the claims extract (Subsidence is a UK-only claim type).",
            rep={"region": "DK"}, expect=0, world_ref="CLAIMTYPE:CT-SUB#uk_only", notes="negation")
    ctx.agg(fid, {"claim_type": {"in": ["CT-FRO", "CT-SNO"]}, "region": "UK"}, "count",
            lambda v: f"There are {v} Frost Damage or Snow Load claims in the UK in the claims extract (both are Nordic-only claim types).",
            rep={"region": "UK"}, expect=0, world_ref="CLAIMTYPE:CT-FRO#nordic_only", notes="negation")
    ctx.agg(fid, {"claim_type": "CT-BIN", "region": {"in": ["NO", "SE", "DK"]}}, "count",
            lambda v: f"There are {v} Business Interruption (CT-BIN) claims in the Nordic regions in the claims extract.",
            rep={"region": "NO"}, expect=0, world_ref="CLAIMTYPE:CT-BIN#uk_only", notes="negation")
    for prod, ccy in (("PRD-MOT-UK", "GBP"), ("PRD-HOM-NO", "NOK"), ("PRD-HOM-SE", "SEK"), ("PRD-LIA-UK", "GBP")):
        ctx.agg(fid, {"product_code": prod}, "sum",
                lambda v, prod=prod, ccy=ccy: f"Sum of reserve_outstanding for {prod} in the claims extract is {ccy} {v:,.2f}.",
                column="reserve_outstanding", notes=sup)
    ctx.agg(fid, {"product_code": "PRD-COM-UK"}, "sum",
            lambda v: f"Sum of incurred_gbp for Commercial Property UK (PRD-COM-UK) in the claims extract is GBP {v:,.2f}.",
            column="incurred_gbp", notes=sup)
    ctx.agg(fid, {"region": {"in": ["NO", "SE", "DK"]}, "loss_date": {"prefix": "2026"}}, "sum",
            lambda v: f"Sum of incurred_gbp for Nordic claims with 2026 loss dates is GBP {v:,.2f}.",
            column="incurred_gbp", rep={"region": "NO", "loss_date": {"prefix": "2026"}}, notes=sup)
    ctx.agg(fid, {"tier": "3", "fraud_referred": "Y"}, "count",
            lambda v: f"{v} Tier-3 claims in the claims extract were referred for fraud (fraud_referred = Y).",
            world_ref="RULE:BR-FRD-031")
    ctx.agg(fid, {"tier": "3", "fraud_referred": "Y", "notified_date": {"gte": "2026-10-01"},
                  "sentinel_score": {"gte": 60, "lte": 64}}, "count",
            lambda v: f"{v} Tier-3 claims notified from 2026-10-01 were referred with Sentinel scores of 60-64 (BR-FRD-031 v2 Tier-3 threshold 60).",
            world_ref="PROFILE:referral_rule_by_date", placement=pl_t360)
    ctx.agg(fid, {"tier": {"in": ["1", "2"]}, "notified_date": {"gte": "2026-10-01"},
                  "sentinel_score": {"gte": 60, "lte": 64}, "fraud_referred": "Y"}, "count",
            lambda v: f"{v} Tier-1/Tier-2 claims scored 60-64 from 2026-10-01 were referred (the 60 threshold applies to Tier-3 only).",
            rep={"tier": {"in": ["1", "2"]}, "notified_date": {"gte": "2026-10-01"}, "sentinel_score": {"gte": 60, "lte": 64}},
            expect=0, world_ref="RULE:BR-FRD-031@v2#parameters.tier3_threshold", notes="negation")
    for rule in ("BR-FRD-012 v2", "BR-FRD-031 v1", "BR-FRD-031 v2"):
        ctx.agg(fid, {"referral_rule": rule}, "count",
                lambda v, rule=rule: f"{v} claims in the claims extract were referred under {rule}.",
                world_ref=f"RULE:{rule.replace(' v', '@v')}")
    ctx.agg(fid, {"assessor_type": "vendor"}, "top",
            lambda v: f"The vendor with the most Claims Assessor assignments in the claims extract is {v[0]} (Brackenfield Loss Adjusting) with {v[1]:,} claims.",
            column="assessor_ref", rep={"assessor_ref": "BRACKFLD"}, world_ref="VENDOR:VEN-01")
    ctx.agg(fid, {"assessor_ref": "FELLGATE", "notified_date": {"gte": "2026-02-01"}}, "count",
            lambda v: f"{v} claims notified on or after 2026-02-01 are assigned to FELLGATE (Fellgate left the panel on 2026-01-31).",
            rep={"assessor_ref": "FELLGATE"}, expect=0, world_ref="VENDOR:VEN-03#panel_to", notes="negation")
    ctx.agg(fid, {"assessor_ref": "FELLGATE"}, "count",
            lambda v: f"{v} claims in the claims extract are assigned to Fellgate (FELLGATE), all UK Tier-3 claims notified before 2026-02-01.",
            world_ref="VENDOR:VEN-03")
    ctx.agg(fid, {}, "top_month",
            lambda v: f"The month with the most FNOLs (notified_date) in the claims extract is {v[0]} with {v[1]:,} claims.",
            column="notified_date", rep={}, needle_col="notified_date")
    ctx.agg(fid, {"status": "OP"}, "count", lambda v: f"{v:,} claims in the claims extract have status OP (open).")
    ctx.agg(fid, {}, "distinct", lambda v: f"The claims extract references {v} distinct handler_ref values.",
            column="handler_ref", rep={}, needle_col="handler_ref")
    ctx.agg(fid, {}, "max", lambda v: f"The largest incurred_gbp in the claims extract is GBP {v:,.2f}.",
            column="incurred_gbp", rep={}, needle_col="incurred_gbp")
    ctx.agg(fid, {"channel": "TL", "product_code": {"in": NON_MOTOR}}, "count",
            lambda v: f"{v} non-motor claims were notified through the telematics channel (TL) in the claims extract.",
            rep={"channel": "TL"}, expect=0, notes="negation")
    ctx.agg(fid, {"recovery_flag": "Y", "product_code": "PRD-MOT-UK"}, "count",
            lambda v: f"{v:,} Motor Private UK claims in the claims extract carry recovery_flag = Y.")
    ctx.agg(fid, {"product_code": "PRD-LIA-UK", "tier": "3"}, "count",
            lambda v: f"{v} SME Liability UK claims in the claims extract are Tier-3.", notes=sup)

    # max-incurred claim and a sample claim id/legacy id pair
    i_max = max(range(len(R)), key=lambda k: float(R[k]["incurred_gbp"]))
    ctx.cfact(fid, i_max + 1, "claim_id", R[i_max]["claim_id"],
              f"The claim with the largest incurred_gbp in the extract is {R[i_max]['claim_id']} ({R[i_max]['claim_type']}, GBP {float(R[i_max]['incurred_gbp']):,.2f}).")
    ctx.cfact(fid, 1, "legacy_claim_id", R[0]["legacy_claim_id"],
              f"Claim {R[0]['claim_id']} has CLARA legacy id {R[0]['legacy_claim_id']} (format CLM-<region>-<yyyy>-<6 digits> vs <region><yyyy><6 digits>).",
              world_ref="TABLE:CLR.T_CLAIM#columns.CLAIM_ID")
    ctx.done(fid, f"{len(recs)} rows")


# =============================================================================================
# ST014 reserve movements October 2026
# =============================================================================================

MOVE_HEADER = ["movement_id", "claim_id", "reserve_id", "reserve_type", "movement_ts", "movement_type", "currency",
               "movement_amount", "movement_amount_gbp", "product_code", "region", "tier", "source_system",
               "program_or_service", "user_id"]


def move_record(m) -> list:
    return [m["movement_id"], m["claim_id"], m["reserve_id"], m["reserve_type"],
            m["movement_ts"].strftime("%Y-%m-%d %H:%M:%S"), m["movement_type"], m["currency"], money(m["amount"]),
            money(m["amount_gbp"]), m["product_code"], m["region"], m["tier"], m["source_system"],
            m["program_or_service"], m["user_id"]]


def build_st014(ctx):
    fid = "ST014"
    rows = ctx.data["claims"]
    mv = C.movements(rows, D("2026-10-01"), D("2026-10-31"), "oct")
    ctx.data["moves_oct"] = mv
    recs = [move_record(m) for m in mv]
    ctx.write_csv(fid, MOVE_HEADER, recs)
    pl = placement(fid, "st14_agg")
    names = {"IN": "initial", "AD": "adjustment", "IX": "indexation", "RV": "review", "ST": "settlement close",
             "RC": "recovery"}
    first = True
    for t in ("ST", "IN", "AD", "IX", "RV", "RC"):
        ctx.agg(fid, {"movement_type": t}, "sum",
                lambda v, t=t: f"October 2026 reserve movements of type {t} ({names[t]}) total GBP {v:,.2f} (movement_amount_gbp).",
                column="movement_amount_gbp", world_ref="TABLE:CLR.T_RESERVE_MOVEMENT", placement=pl if first else None,
                notes=None if first else "supports PL-164")
        first = False
        ctx.agg(fid, {"movement_type": t}, "count",
                lambda v, t=t: f"There are {v:,} October 2026 reserve movements of type {t} ({names[t]}).",
                world_ref="TABLE:CLR.T_RESERVE_MOVEMENT", notes="supports PL-164")
    ctx.agg(fid, {"program_or_service": "CLRGL090"}, "count",
            lambda v: f"{v} October 2026 reserve movements were written by CLRGL090 (it updates CLR.T_RESERVE without writing movements).",
            rep={"source_system": "CLARA"}, expect=0, world_ref="PROGRAM:CLRGL090#writes_tables", notes="negation")
    ctx.agg(fid, {"source_system": "Claims Hub"}, "count",
            lambda v: f"{v:,} October 2026 reserve movements came from Claims Hub (reserve-engine); the rest from CLARA.",
            world_ref="SERVICE:reserve-engine")
    ctx.agg(fid, {"program_or_service": "CLRRS150"}, "count",
            lambda v: f"{v} October 2026 movements were written by the movement correction utility CLRRS150.",
            world_ref="PROGRAM:CLRRS150")
    ctx.done(fid, f"{len(recs)} rows")


# =============================================================================================
# ST015 fraud referrals 2026 (company-wide; Q2/Q3 counts agree with timeline metrics)
# =============================================================================================

REF_HEADER = ["referral_id", "claim_id", "product_code", "region", "tier", "sentinel_score", "score_date",
              "referral_date", "referral_ts", "rule_applied", "threshold_applied", "referral_source", "system",
              "siu_case_id", "referral_status", "customer_notice_due", "notice_deferred", "outcome", "outcome_date"]

PERIODS = [("Q1", D("2026-01-01"), D("2026-03-31"), 1402), ("Q2", D("2026-04-01"), D("2026-06-30"), None),
           ("Q3", D("2026-07-01"), D("2026-09-30"), None), ("OCT", D("2026-10-01"), D("2026-10-31"), 548)]


def _tail_score(r, th: int, hi: int = 100) -> int:
    for _ in range(10000):
        s = round(r.betavariate(2.2, 6.5) * 100)
        if r.random() < 0.08:
            s = min(100, s + 10)
        if th <= s <= hi:
            return s
    return th


def build_st015(ctx):
    fid = "ST015"
    rows = ctx.data["claims"]
    met = W.timeline["metrics"]["fraud_referrals_count"]
    targets = {"Q1": 1402, "Q2": int(met["2026Q2"]), "Q3": int(met["2026Q3"]), "OCT": 548}
    r = rng("ST015:referrals")
    pool = C.IdPool("ST015:ids")
    products = list(C.P["products"])
    pw = [C.P["products"][p] for p in products]
    inc_518 = W.incidents["INC-2026-0518"]
    inc_1007 = W.incidents["INC-2026-1007"]
    n518 = int(re.match(r"(\d+)", inc_518["impact"]).group(1))
    n1007 = int(re.match(r"(\d+)", inc_1007["impact"]).group(1))
    hub_products = [p for p in C.MIGRATION]

    recs = []

    def period_of(d):
        for name, a, b, _ in PERIODS:
            if a <= d <= b:
                return name
        return None

    # (1) referrals of sample claims (ST013) notified in 2026
    for x in rows:
        if x["fraud_referred"] != "Y" or x["notified_date"].year != 2026:
            continue
        d = x["notified_date"]
        hub = C.on_hub(x["product_code"], d)
        rule = x["referral_rule"].replace(" v", "@v")
        src = "ON"
        rd = d
        sd = d
        if (not hub and x["sentinel_score"] >= 70 and r.random() < 0.35
                and C.referral_rule_at(d + dt.timedelta(days=1)) == rule):
            src, rd = "BS", d + dt.timedelta(days=1)
        if (hub and x["tier"] == 3 and 60 <= x["sentinel_score"] <= 64 and D("2026-10-01") <= d <= D("2026-10-05")):
            src, rd = "MN", D("2026-10-06")
        recs.append({"claim_id": x["claim_id"], "product": x["product_code"], "region": x["region"],
                     "tier": x["tier"], "score": x["sentinel_score"], "sd": sd, "rd": rd, "rule": rule,
                     "src": src, "hub": hub, "special": "1007" if src == "MN" else None, "sample": True})

    # (2) INC-2026-0518: batch path missed claims scored 65-69 (2026-04-01..2026-05-12), referred manually 2026-05-13
    for _ in range(n518):
        prod = C.wchoice(r, [p for p in products if p not in hub_products], [w for p, w in zip(products, pw) if p not in hub_products])
        sd = D("2026-04-01") + dt.timedelta(days=r.randint(0, 41))
        recs.append({"claim_id": None, "product": prod, "region": C.REGION_OF[prod], "tier": C.wchoice(r, [1, 2, 3], [0.46, 0.40, 0.14]),
                     "score": r.randint(65, 69), "sd": sd, "rd": D("2026-05-13"), "rule": "BR-FRD-031@v1",
                     "src": "MN", "hub": False, "special": "0518", "sample": False})

    # (3) INC-2026-1007: Claims Hub missed Tier-3 claims scored 60-64 (2026-10-01..05), referred manually
    have = sum(1 for x in recs if x["special"] == "1007")
    for _ in range(n1007 - have):
        prod = C.wchoice(r, hub_products, [C.P["products"][p] for p in hub_products])
        sd = D("2026-10-01") + dt.timedelta(days=r.randint(0, 4))
        recs.append({"claim_id": None, "product": prod, "region": C.REGION_OF[prod], "tier": 3,
                     "score": r.randint(60, 64), "sd": sd, "rd": D("2026-10-06"), "rule": "BR-FRD-031@v2",
                     "src": "MN", "hub": True, "special": "1007", "sample": False})

    # (4) fill each period to its target with synthetic referrals
    for name, a, b, _ in PERIODS:
        have = sum(1 for x in recs if period_of(x["rd"]) == name)
        need = targets[name] - have
        assert need >= 0, (name, need)
        days = (b - a).days
        for _ in range(need):
            rd = a + dt.timedelta(days=r.randint(0, days))
            prod = C.wchoice(r, products, pw)
            hub = C.on_hub(prod, rd)
            tier = C.wchoice(r, [1, 2, 3], [0.44, 0.40, 0.16])
            rule = C.referral_rule_at(rd)
            rid, ver = rule.split("@v")
            prm = W.rules[rid]["versions"][int(ver) - 1]["parameters"]
            th = prm["threshold"]
            score = _tail_score(r, th)
            if "tier3_threshold" in prm and tier == 3 and r.random() < 0.35:
                if not (hub and rd <= D("2026-10-05")):
                    score = r.randint(prm["tier3_threshold"], th - 1)
            if hub:
                src = "ON"
            elif score >= 70:
                src = "BS" if r.random() < 0.35 else "ON"
            elif rd >= D("2026-05-14") and r.random() < 0.25:
                src = "MN"   # daily Compliance query (INC-2026-0518 workaround)
            else:
                src = "ON"
            sd = rd - dt.timedelta(days=1) if src == "BS" else (rd - dt.timedelta(days=1) if src == "MN" else rd)
            if src == "BS" and C.referral_rule_at(sd) != rule:
                src, sd = "ON", rd
            recs.append({"claim_id": None, "product": prod, "region": C.REGION_OF[prod], "tier": tier, "score": score,
                         "sd": sd, "rd": rd, "rule": rule, "src": src, "hub": hub, "special": None, "sample": False})

    # render
    for x in recs:
        if x["claim_id"] is None:
            back = r.choice([0, 0, 1, 2, 3, 5, 9])
            x["claim_id"], _ = pool.claim_id(x["region"], x["sd"] - dt.timedelta(days=back))
        if x["src"] == "ON":
            x["ts"] = dt.datetime.combine(x["rd"], dt.time(r.randint(7, 19), r.randint(0, 59), r.randint(0, 59)))
        elif x["src"] == "BS":
            x["ts"] = dt.datetime.combine(x["rd"], dt.time(0, r.randint(15, 44), r.randint(0, 59)))
        else:
            x["ts"] = dt.datetime.combine(x["rd"], dt.time(r.randint(9, 16), r.randint(0, 59), r.randint(0, 59)))
    recs.sort(key=lambda x: (x["ts"], x["claim_id"]))
    out = []
    cut = D("2026-11-01")
    for k, x in enumerate(recs, 1):
        th = 70 if x["src"] == "BS" else C.threshold_for(x["rule"], x["tier"], x["score"])
        siu = f"SIU-{260000 + k:06d}" if r.random() < 0.86 else ""
        age = (cut - x["rd"]).days
        if not siu:
            status, outcome, od = "CL", "WD", x["rd"] + dt.timedelta(days=r.randint(1, 5))
        elif age < 25 or r.random() < 0.25:
            status, outcome, od = ("OP" if age < 4 else "IN"), "", None
        else:
            status = "CL"
            outcome = C.wchoice(r, ["NF", "CF", "WD"], [0.70, 0.23, 0.07])
            od = x["rd"] + dt.timedelta(days=r.randint(18, min(140, max(19, age))))
            if od >= cut:
                status, outcome, od = "IN", "", None
        notice = iso(add_bd(x["rd"], 10)) if x["rd"] >= D("2026-04-01") else ""
        deferred = "Y" if (notice and r.random() < 0.04) else ("N" if notice else "")
        out.append([f"REF-2026-{k:06d}", x["claim_id"], x["product"], x["region"], x["tier"], x["score"], iso(x["sd"]),
                    iso(x["rd"]), x["ts"].strftime("%Y-%m-%d %H:%M:%S"), C.rule_label(x["rule"]), th, x["src"],
                    "Claims Hub" if x["hub"] else "CLARA", siu, status, notice, deferred, outcome, iso(od) if od else ""])
    ctx.write_csv(fid, REF_HEADER, out)
    pl = placement(fid, "st15_agg")
    first = True
    for rule in ("BR-FRD-012 v2", "BR-FRD-031 v1", "BR-FRD-031 v2"):
        ctx.agg(fid, {"rule_applied": rule}, "count",
                lambda v, rule=rule: f"The 2026 fraud referral extract has {v:,} referrals with rule applied {rule}.",
                world_ref=pl["world_ref"] if first else f"RULE:{rule.replace(' v', '@v')}",
                placement=pl if first else None,
                notes=None if first else "supports PL-165")
        first = False
    ctx.agg(fid, {"referral_date": {"gte": "2026-04-01", "lte": "2026-06-30"}}, "count",
            lambda v: f"The 2026 fraud referral extract has {v:,} referrals dated in Q2 2026 (matches the 2026Q2 referral count).",
            world_ref="TIMELINE:metrics#fraud_referrals_count.2026Q2", expect=targets["Q2"])
    ctx.agg(fid, {"referral_date": {"gte": "2026-07-01", "lte": "2026-09-30"}}, "count",
            lambda v: f"The 2026 fraud referral extract has {v:,} referrals dated in Q3 2026 (matches the 2026Q3 referral count).",
            world_ref="TIMELINE:metrics#fraud_referrals_count.2026Q3", expect=targets["Q3"])
    ctx.agg(fid, {"referral_source": "MN", "referral_date": "2026-05-13", "rule_applied": "BR-FRD-031 v1",
                  "sentinel_score": {"gte": 65, "lte": 69}}, "count",
            lambda v: f"{v} manual (MN) referrals dated 2026-05-13 have Sentinel scores 65-69: the claims the CLRFR040 batch path missed (INC-2026-0518).",
            world_ref="INCIDENT:INC-2026-0518#impact", expect=n518)
    ctx.agg(fid, {"referral_source": "MN", "system": "Claims Hub", "tier": "3", "sentinel_score": {"gte": 60, "lte": 64},
                  "score_date": {"gte": "2026-10-01", "lte": "2026-10-05"}}, "count",
            lambda v: f"{v} Tier-3 Claims Hub referrals scored 60-64 between 2026-10-01 and 2026-10-05 were made manually (INC-2026-1007).",
            world_ref="INCIDENT:INC-2026-1007#impact", expect=n1007)
    ctx.agg(fid, {"referral_source": "BS", "sentinel_score": {"lt": 70}}, "count",
            lambda v: f"{v} batch-sweep (BS) referrals have a Sentinel score below 70: the CLRFR040 sweep still applies a hard-coded 070.",
            rep={"referral_source": "BS"}, expect=0, world_ref="PROGRAM:CLRFR040#hardcoded_constants", notes="negation")
    ctx.agg(fid, {"referral_source": "BS", "threshold_applied": {"ne": "70"}}, "count",
            lambda v: f"{v} batch-sweep (BS) referrals record a threshold_applied other than 70.",
            rep={"referral_source": "BS"}, expect=0, world_ref="PROGRAM:CLRFR040#hardcoded_constants", notes="negation")
    ctx.agg(fid, {}, "count", lambda v: f"The 2026 fraud referral extract (to 2026-10-31) has {v:,} rows.",
            needle_col="referral_id")
    ctx.agg(fid, {"outcome": "CF"}, "count", lambda v: f"{v:,} 2026 referrals in the extract have outcome CF (confirmed fraud).")
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST016 payments September-October 2026
# =============================================================================================

PAY_HEADER = ["payment_id", "claim_id", "payment_date", "payee_type", "payee_ref", "currency", "amount", "amount_gbp",
              "payment_status", "sanctions_check", "source_system", "product_code", "region", "duplicate_of", "comment"]


def build_st016(ctx):
    fid = "ST016"
    rows = ctx.data["claims"]
    r = rng("ST016:payments")
    pays = C.payments(rows, D("2026-09-01"), D("2026-10-31"), "sepoct")
    inc = W.incidents["INC-2026-0914"]
    m = re.match(r"(\d+) claims paid twice, total £([\d,]+\.\d\d)", inc["impact"])
    n_dup, total_dup = int(m.group(1)), float(m.group(2).replace(",", ""))
    cut = D(inc["date"])
    # pick the claims paid twice on the Wave 1 cut-over day (UK motor, now on Claims Hub)
    cands = [x for x in rows if x["product_code"] == "PRD-MOT-UK" and x["notified_date"] <= cut - dt.timedelta(days=5)
             and C.life_end(x) >= cut + dt.timedelta(days=3) and x["paid_to_date"] >= 4500 and x["status"] != "CN"]
    cands.sort(key=lambda x: x["claim_id"])
    r.shuffle(cands)
    chosen = sorted(cands[:n_dup], key=lambda x: x["claim_id"])
    w = [r.uniform(0.5, 1.6) for _ in chosen]
    amts = [round(total_dup * wi / sum(w), 2) for wi in w]
    amts[-1] = round(total_dup - sum(amts[:-1]), 2)
    dup_claims = {x["claim_id"]: a for x, a in zip(chosen, amts)}
    pays = [p for p in pays if p["claim"]["claim_id"] not in dup_claims or p["date"] != cut]
    extra = []
    for x in chosen:
        a = dup_claims[x["claim_id"]]
        own = [p for p in pays if p["claim"]["claim_id"] == x["claim_id"]]
        while own and sum(p["amount"] for p in own) + a > x["paid_to_date"]:
            drop = own.pop()
            pays.remove(drop)
        extra.append({"claim": x, "date": cut, "payee_type": "claimant", "payee_ref": "CLAIMANT", "amount": a,
                      "currency": "GBP", "hub": True, "status": "CONFIRMED", "seq": 90, "dup": None})
        extra.append({"claim": x, "date": cut, "payee_type": "claimant", "payee_ref": "CLAIMANT", "amount": a,
                      "currency": "GBP", "hub": True, "status": "RECALLED", "seq": 91, "dup": True})
    allp = sorted(pays + extra, key=lambda p: (p["date"], p["claim"]["claim_id"], p["seq"]))
    out = []
    last_orig = {}
    for k, p in enumerate(allp, 1):
        pid = f"PAY-{p['date'].strftime('%y%m')}-{k:06d}"
        x = p["claim"]
        status = p["status"]
        if status == "CONFIRMED" and p.get("dup") is None and p["seq"] < 90 and r.random() < 0.008:
            status = "CANCELLED"
        dup_of, comment = "", ""
        if p.get("dup") is None and p["seq"] == 90:
            last_orig[x["claim_id"]] = pid
        if p.get("dup"):
            dup_of = last_orig[x["claim_id"]]
            comment = f"Duplicate instruction on Wave 1 cut-over ({inc['id']}) - recalled"
        elif status == "CANCELLED":
            comment = "Cancelled before release"
        sanc = "CLEAR" if r.random() < 0.985 else "CLEAR - manual review"
        rate = C.fx_latest(p["currency"])
        out.append([pid, x["claim_id"], iso(p["date"]), p["payee_type"], p["payee_ref"], p["currency"], money(p["amount"]),
                    money(round(p["amount"] * rate, 2)), status, sanc, "Claims Hub" if p["hub"] else "CLARA",
                    x["product_code"], x["region"], dup_of, comment])
    R = ctx.write_csv(fid, PAY_HEADER, out)
    ctx.data["payments"] = R
    ctx.agg(fid, {"payment_status": "RECALLED"}, "count",
            lambda v: f"{v} payments in the September-October 2026 payments extract are RECALLED duplicates from the Wave 1 cut-over (INC-2026-0914).",
            world_ref="INCIDENT:INC-2026-0914#impact", expect=n_dup)
    ctx.agg(fid, {"payment_status": "RECALLED"}, "sum",
            lambda v: f"The recalled duplicate payments of 2026-09-14 total GBP {v:,.2f}.",
            column="amount", world_ref="INCIDENT:INC-2026-0914#impact", expect=total_dup)
    ctx.agg(fid, {"payment_date": {"prefix": "2026-10"}, "payment_status": {"in": ["CONFIRMED", "SENT"]}}, "sum",
            lambda v: f"Confirmed or sent payments dated October 2026 total GBP {v:,.2f} (amount_gbp at 2026-09-30 rates).",
            column="amount_gbp", rep={"payment_date": {"prefix": "2026-10"}})
    ctx.agg(fid, {"payee_ref": "NORRVIK"}, "count",
            lambda v: f"{v} payments in the extract are made to Norrvik (NORRVIK).", rep={"region": "SE"}, expect=0,
            notes="negation; Norrvik fee amounts are deliberately absent from this family")
    ctx.agg(fid, {"payee_type": "vendor_fee", "payee_ref": "BRACKFLD"}, "top",
            lambda v: f"The most common Brackenfield fee payment amount in the extract is GBP {v[0]} ({v[1]} payments).",
            column="amount", world_ref="VENDOR:VEN-01#fees")
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST017 recoveries 2026
# =============================================================================================

REC_HEADER = ["recovery_id", "claim_id", "subro_case_id", "recovery_type", "counterparty_ref", "solicitor_vendor",
              "opened_date", "demand_date", "demand_amount", "expected_amount", "received_amount", "write_off_amount",
              "status", "currency", "last_receipt_date", "subtrak_ref", "system", "product_code", "region"]


def build_st017(ctx):
    fid = "ST017"
    rows = ctx.data["claims"]
    out = []
    receipts = []
    k = 0
    for x in rows:
        if x["recovery_flag"] != "Y" or x["status"] == "CN":
            continue
        cr = rng(f"rec:claim:{x['claim_id']}")
        opened = x["notified_date"] + dt.timedelta(days=cr.randint(10, 75))
        if opened > C.LAST_DAY:
            continue
        end = opened + dt.timedelta(days=cr.randint(40, 420))
        if end < D("2026-01-01"):
            continue
        k += 1
        line = x["_line"]
        if line == "Motor" and x["claim_type"] in ("CT-THF", "CT-COL") and cr.random() < 0.25:
            rtype, cp, sol = "SV", "SALVANTA", ""
        elif cr.random() < 0.08:
            rtype, cp, sol = "EX", "POLICYHOLDER", ""
        else:
            rtype, cp, sol = "SB", f"TPI-{cr.randint(100, 999)}", ""
        rate = C.fx_latest(x["currency"])
        base = max(x["incurred"], 300 / rate)
        if rtype == "SB":
            demand = round(base * cr.uniform(0.5, 1.0), 2)
            if opened >= D("2025-09-01") and demand * rate < 1000:
                demand = round(1000 / rate + cr.uniform(5, 400) / rate, 2)
        elif rtype == "SV":
            demand = round(max(150 / rate, base * cr.uniform(0.05, 0.2)), 2)
        else:
            ex = W.products[x["product_code"]]["excess"]
            demand = round(min(base, float(ex.get("standard", next(iter(ex.values()))))), 2)
        demand_date = add_bd(opened, cr.randint(2, 10)) if rtype == "SB" else None
        if demand_date and demand_date > C.LAST_DAY:
            demand_date = None  # letter before action not yet issued at the extract cut-off
        expected = round(demand * cr.uniform(0.6, 1.0), 2)
        st = C.wchoice(cr, ["OP", "PT", "CL", "WO"], [0.30, 0.25, 0.37, 0.08])
        if end > C.LAST_DAY and st in ("CL", "WO"):
            st = "PT" if cr.random() < 0.5 else "OP"
        received = 0.0
        if st == "PT":
            received = round(expected * cr.uniform(0.2, 0.8), 2)
        elif st == "CL":
            received = round(expected * cr.uniform(0.85, 1.0), 2)
        elif st == "WO":
            received = round(expected * cr.uniform(0.0, 0.3), 2)
        wo = round(expected - received, 2) if st == "WO" else 0.0
        if rtype == "SB" and st in ("OP", "PT") and cr.random() < 0.12:
            sol = "QUARRYHL"
        last_rcpt = None
        if received > 0:
            last_rcpt = min(C.LAST_DAY, max(opened + dt.timedelta(days=cr.randint(15, 200)), D("2026-01-02")))
            receipts.append({"claim": x, "date": last_rcpt, "amount": received, "type": rtype, "recovery_id": f"RCV-{k:06d}"})
        hub = C.on_hub(x["product_code"], max(opened, D("2026-01-01")))
        out.append([f"RCV-{k:06d}", x["claim_id"], f"SUB{k:07d}" if rtype == "SB" else "", rtype, cp, sol, iso(opened),
                    iso(demand_date) if demand_date else "", money(demand), money(expected), money(received), money(wo), st,
                    x["currency"], iso(last_rcpt) if last_rcpt else "", f"ST-{x['region']}-{k:06d}" if rtype == "SB" else "",
                    "Claims Hub" if hub else "CLARA", x["product_code"], x["region"]])
    out.sort(key=lambda rec: rec[0])
    ctx.write_csv(fid, REC_HEADER, out)
    ctx.data["receipts"] = receipts
    for t, nm in (("SB", "subrogation"), ("SV", "salvage"), ("EX", "excess recovery")):
        ctx.agg(fid, {"recovery_type": t}, "count",
                lambda v, t=t, nm=nm: f"The 2026 recoveries extract has {v:,} {nm} ({t}) rows.", world_ref="TABLE:CLR.T_RECOVERY")
    ctx.agg(fid, {"recovery_type": "SV", "counterparty_ref": {"ne": "SALVANTA"}}, "count",
            lambda v: f"{v} salvage rows use a counterparty other than SALVANTA (Salvanta Salvage handles UK and Nordic vehicle salvage).",
            rep={"recovery_type": "SV"}, expect=0, world_ref="VENDOR:VEN-09#role", notes="negation")
    ctx.agg(fid, {"currency": "GBP", "status": "CL"}, "sum",
            lambda v: f"Closed GBP recoveries in the 2026 extract received GBP {v:,.2f} in total.", column="received_amount")
    ctx.agg(fid, {"solicitor_vendor": "QUARRYHL"}, "count",
            lambda v: f"{v} recovery cases in the 2026 extract are with Quarryhill Solicitors (QUARRYHL).", world_ref="VENDOR:VEN-07#role")
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST018 Claims Assessor assignments 2026
# =============================================================================================

ASG_HEADER = ["assignment_id", "claim_id", "appointed_ts", "assessor_type", "claims_assessor_id", "vendor_code",
              "assessment_type", "sla_due_date", "product_code", "claim_type", "region", "tier", "source_system"]


def build_st018(ctx):
    fid = "ST018"
    rows = ctx.data["claims"]
    out = []
    sla01 = W.vendors["VEN-01"]["sla"]
    sla02 = W.vendors["VEN-02"]["sla"]
    k = 0
    for x in rows:
        if x["notified_date"].year != 2026 or x["assessor_type"] == "desk":
            continue
        cr = rng(f"asg:claim:{x['claim_id']}")
        k += 1
        ap = add_bd(x["notified_date"], cr.choice([0, 0, 1, 1, 2]))
        ts = dt.datetime.combine(ap, dt.time(cr.randint(8, 17), cr.randint(0, 59), 0))
        vendor = x["assessor_ref"] if x["assessor_type"] == "vendor" else ""
        if x["claim_type"] == "CT-EOW" and x["_est_gbp"] < 7500 and x["assessor_type"] == "internal" and ap >= D("2025-01-01"):
            atype = "video" if cr.random() < 0.6 else "desk"
        elif x["tier"] >= 2 or x["_line"] != "Motor":
            atype = "site"
        else:
            atype = "desk" if cr.random() < 0.6 else "site"
        sla = ""
        if vendor == "BRACKFLD":
            days = sla01["site_visit_business_days"] if atype == "site" else sla01["desk_assessment_business_days"]
            sla = iso(add_bd(ap, days))
        elif vendor == "NORRVIK" and atype == "site":
            sla = iso(add_bd(ap, sla02["site_visit_business_days"]))
        hub = C.on_hub(x["product_code"], ap)
        out.append([f"ASG-26-{k:06d}", x["claim_id"], ts.strftime("%Y-%m-%d %H:%M:%S"), x["assessor_type"],
                    x["assessor_ref"], vendor, atype, sla, x["product_code"], x["claim_type"], x["region"], x["tier"],
                    "Claims Hub" if hub else "CLARA"])
    out.sort(key=lambda rec: (rec[2], rec[0]))
    ctx.write_csv(fid, ASG_HEADER, out)
    ctx.agg(fid, {"assessor_type": "vendor"}, "top",
            lambda v: f"The vendor with the most Claims Assessor assignments in 2026 is {v[0]} (Brackenfield Loss Adjusting) with {v[1]:,} assignments.",
            column="vendor_code", rep={"vendor_code": "BRACKFLD"}, world_ref="VENDOR:VEN-01")
    ctx.agg(fid, {"vendor_code": "FELLGATE", "appointed_ts": {"gte": "2026-02-01"}}, "count",
            lambda v: f"{v} Fellgate (FELLGATE) assignments are dated on or after 2026-02-01 (removed from the panel 2026-01-31).",
            rep={"vendor_code": "FELLGATE"}, expect=0, world_ref="VENDOR:VEN-03#panel_to", notes="negation")
    ctx.agg(fid, {"vendor_code": "NORRVIK", "region": "UK"}, "count",
            lambda v: f"{v} Norrvik assignments are on UK claims (Norrvik covers the Nordic regions).",
            rep={"vendor_code": "NORRVIK"}, expect=0, world_ref="VENDOR:VEN-02#role", notes="negation")
    ctx.agg(fid, {"assessment_type": "video"}, "count",
            lambda v: f"{v} 2026 assignments are video assessments (Escape of Water below GBP 7,500, BR-ASM-003 v2).",
            world_ref="RULE:BR-ASM-003@v2")
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST019 CRUD matrix (truthful: agrees with programs.yaml)
# =============================================================================================

CREATE_WORDS = re.compile(r"\b(create|capture|register|appointment|load|import|request|build|posting|record|"
                          r"calculation|archiver|snapshot|log|extract|notice|notification|letter|referral|scor)", re.I)


def status_asof(pid: str, d) -> str:
    ds = iso(D(d))
    p = W.programs[pid]
    if pid == "CLRRS210":
        return "retired" if ds >= "2026-08-28" else "active"
    if pid == "CLRFR140":
        return "disabled" if ds >= "2026-04-01" else "active"
    return p["status"]


def crud_ops(pid: str, table: str) -> str:
    p = W.programs[pid]
    ops = set()
    if table in p["reads_tables"]:
        ops.add("R")
    if table in p["writes_tables"]:
        if table == "CLR.T_RESERVE":
            ops |= {"C"} if pid == "CLRFN030" else ({"C", "U"} if pid == "CLRRS010" else {"U"})
        elif table == "CLR.T_RESERVE_MOVEMENT":
            ops |= {"U"} if pid == "CLRRS170" else ({"C", "U"} if pid == "CLRRS150" else {"C"})
        elif table == "CLR.T_CLAIM":
            ops |= {"C"} if pid == "CLRFN030" else {"U"}
        elif re.search(r"_(HISTORY|AUDIT|LOG|EVENT|NOTE|RUN|RETURN|POSTING|NOTIFICATION)$", table):
            ops.add("C")
        elif pid == "CLRCM140":
            ops |= {"U", "D"}
        elif CREATE_WORDS.search(p["description"]):
            ops |= {"C", "U"}
        else:
            ops.add("U")
    return "".join(o for o in "CRUD" if o in ops)


CRUD_HEADER = ["program_id", "program_type", "program_area", "program_status", "table_name", "table_area", "C", "R",
               "U", "D", "crud", "evidence"]


def build_st019(ctx):
    fid = "ST019"
    d = adate(fid)
    out = []
    for pid in sorted(W.programs):
        p = W.programs[pid]
        if p["since"] > iso(d):
            continue
        tabs = sorted(set(p["reads_tables"]) | set(p["writes_tables"]))
        for t in tabs:
            ops = crud_ops(pid, t)
            ev = "EXEC SQL in program source" if p["type"] == "batch" else "EXEC SQL in program source (CICS)"
            out.append([pid, p["type"], p["area"], status_asof(pid, d), t, W.tables[t]["area"],
                        "Y" if "C" in ops else "", "Y" if "R" in ops else "", "Y" if "U" in ops else "",
                        "Y" if "D" in ops else "", ops, ev])
    R = ctx.write_csv(fid, CRUD_HEADER, out)
    pl8 = placement(fid, "st19_writers8")
    pl150 = placement(fid, "st19_rs150")
    writers = W.reserve_writers
    got = sorted({r["program_id"] for r in R if r["table_name"] == "CLR.T_RESERVE" and re.search("[CU]", r["crud"])})
    assert got == sorted(writers), got
    ctx.agg(fid, {"table_name": "CLR.T_RESERVE", "crud": {"regex": "[CU]"}}, "distinct",
            lambda v: f"CRUD matrix: exactly {v} programs have C (insert) or U (update) on CLR.T_RESERVE - CLRFN030, CLRRS010, CLRRS020, CLRRS110, CLRRS130, CLRST040, CLRRC050, CLRGL090.",
            column="program_id", rep={"table_name": "CLR.T_RESERVE", "program_id": "CLRGL090"}, needle_col="program_id",
            world_ref=pl8["world_ref"], placement=pl8, expect=8, kind=pl8["kind"])
    for i, rr in enumerate(R, 1):
        if rr["table_name"] == "CLR.T_RESERVE" and rr["program_id"] in writers:
            ctx.cfact(fid, i, "program_id", rr["program_id"],
                      f"CRUD matrix row: {rr['program_id']} has '{rr['crud']}' on CLR.T_RESERVE (a reserve-table writer).",
                      kind="contradiction_new" if rr["program_id"] == "CLRGL090" else "needle",
                      world_ref=f"PROGRAM:{rr['program_id']}#writes_tables:CLR.T_RESERVE",
                      contradictions=["C08"] if rr["program_id"] == "CLRGL090" else None,
                      notes="supports PL-166" if rr["program_id"] != "CLRGL090" else "supports PL-166; the data dictionary ST001 omits this writer")
    for i, rr in enumerate(R, 1):
        if rr["program_id"] == "CLRRS150" and rr["table_name"] == "CLR.T_RESERVE_MOVEMENT":
            ctx.cfact(fid, i, "crud", rr["crud"],
                      "CRUD matrix: CLRRS150 (reserve movement correction utility) writes CLR.T_RESERVE_MOVEMENT (C/U); its only access to CLR.T_RESERVE is a read.",
                      kind="needle", world_ref="PROGRAM:CLRRS150#writes_tables", placement=pl150,
                      notes="placement text says 'no access to CLR.T_RESERVE'; programs.yaml lists CLR.T_RESERVE in reads_tables, so the matrix shows R only")
    ctx.agg(fid, {"program_id": "CLRRS150", "table_name": "CLR.T_RESERVE", "crud": {"regex": "[CUD]"}}, "count",
            lambda v: f"CRUD matrix: CLRRS150 has {v} write operations (C/U/D) on CLR.T_RESERVE (read only).",
            rep={"program_id": "CLRRS150"}, needle_col="program_id", expect=0,
            world_ref="PROGRAM:CLRRS150#writes_tables", notes="negation; supports PL-167")
    ctx.agg(fid, {"table_name": "CLR.T_RESERVE_MOVEMENT", "crud": {"regex": "[CU]"}}, "distinct",
            lambda v: f"CRUD matrix: {v} programs write CLR.T_RESERVE_MOVEMENT.", column="program_id",
            world_ref="TABLE:CLR.T_RESERVE_MOVEMENT#writers")
    ctx.agg(fid, {}, "count", lambda v: f"The CLARA program-table CRUD matrix has {v} program-table rows.",
            needle_col="program_id")
    ctx.agg(fid, {"table_name": "CLR.T_CLAIM", "crud": {"regex": "R"}}, "distinct",
            lambda v: f"CRUD matrix: {v} programs read CLR.T_CLAIM.", column="program_id",
            world_ref="TABLE:CLR.T_CLAIM#readers")
    ctx.data["crud_rows"] = R
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST020 interface run log October 2026
# =============================================================================================

RUN_HEADER = ["run_id", "interface_id", "interface_name", "run_date", "scheduled", "start_ts", "end_ts", "runs",
              "records", "status", "comment"]


def _vol(s: str) -> int:
    m = re.search(r"([\d,]+)", s or "")
    return int(m.group(1).replace(",", "")) if m else 1000


def _nth_bd(y, m, n):
    d = dt.date(y, m, 1)
    k = 0
    while True:
        if d.weekday() < 5:
            k += 1
            if k == n:
                return d
        d += dt.timedelta(days=1)


def build_st020(ctx):
    fid = "ST020"
    r = rng("ST020:runs")
    days = [D("2026-10-01") + dt.timedelta(days=i) for i in range(31)]
    asof = "2026-10-15"
    events = []
    inc = W.incidents["INC-2026-0340"]
    for iid, x in sorted(W.interfaces.items()):
        if iid == "CLX-IF-042":
            continue  # schedule reserved for another document
        if x["since"] > "2026-10-31" or x["status"] != "live":
            continue
        sch = W.interface_schedule(iid, asof)
        vol = _vol(x["avg_daily_volume"])
        name = x["name"]
        times: list[tuple[dt.date, list[dt.time], bool]] = []
        if re.fullmatch(r"daily \d\d:\d\d", sch):
            hh, mm = map(int, sch.split()[1].split(":"))
            times = [(d, [dt.time(hh, mm)], False) for d in days]
        elif re.fullmatch(r"Mon-Fri \d\d:\d\d", sch):
            hh, mm = map(int, sch.split()[1].split(":"))
            times = [(d, [dt.time(hh, mm)], False) for d in days if d.weekday() < 5]
        elif sch.startswith("Tue,Thu"):
            hh, mm = map(int, sch.split()[1].split(":"))
            times = [(d, [dt.time(hh, mm)], False) for d in days if d.weekday() in (1, 3)]
        elif sch.startswith("every 30 minutes"):
            a, b = re.search(r"(\d\d):\d\d-(\d\d):\d\d", sch).groups()
            slots = [dt.time(h, m) for h in range(int(a), int(b) + 1) for m in (0, 30) if not (h == int(b) and m == 30)]
            times = [(d, slots, False) for d in days]
        elif re.fullmatch(r"hourly \d\d:\d\d-\d\d:\d\d", sch):
            a, b = re.search(r"(\d\d):\d\d-(\d\d):\d\d", sch).groups()
            slots = [dt.time(h, 0) for h in range(int(a), int(b) + 1)]
            times = [(d, slots, False) for d in days]
        elif sch == "hourly":
            times = [(d, [dt.time(h, 0) for h in range(24)], True) for d in days]
        elif sch.startswith("monthly"):
            n = int(re.search(r"(\d)(st|nd|rd|th)", sch).group(1))
            times = [(_nth_bd(2026, 10, n), [dt.time(6, 0)], False)]
        elif sch.startswith("quarterly,"):
            n = int(re.search(r"(\d+)(st|nd|rd|th)", sch).group(1))
            times = [(_nth_bd(2026, 10, n), [dt.time(7, 0)], False)]
        else:
            continue
        for d, slots, summary in times:
            if summary:
                recs = int(vol * r.uniform(0.85, 1.15))
                st = dt.datetime.combine(d, slots[0])
                en = dt.datetime.combine(d, dt.time(23, 59))
                events.append([iid, name, d, f"{sch}", st, en, len(slots), recs, "OK", "Daily summary of hourly runs"])
                continue
            per = max(1, vol // len(slots))
            for t in slots:
                recs = max(0, int(per * r.uniform(0.7, 1.3)))
                st = dt.datetime.combine(d, t) + dt.timedelta(seconds=r.randint(5, 150))
                en = st + dt.timedelta(seconds=30 + int(recs * r.uniform(0.05, 0.25)))
                status, comment = "OK", ""
                if iid == "CLX-IF-020" and d == D(inc["date"]):
                    status = "ER"
                    comment = f"Confirmation file not received from CPG ({inc['id']})"
                    events.append([iid, name, d, sch, st, st + dt.timedelta(seconds=40), 1, 0, status, comment])
                    rs = dt.datetime.fromisoformat(inc["start"]) + dt.timedelta(minutes=int(re.search(r"(\d+) minutes", inc["impact"]).group(1)))
                    events.append([iid, name, d, sch, rs, rs + dt.timedelta(seconds=30 + int(recs * 0.1)), 1, recs, "RR",
                                   f"Rerun after late confirmation file ({inc['id']})"])
                    continue
                events.append([iid, name, d, sch, st, en, 1, recs, status, comment])
    events.sort(key=lambda e: (e[4], e[0]))
    out = []
    for k, e in enumerate(events, 1):
        out.append([f"{2610000 + k}", e[0], e[1], iso(e[2]), e[3], e[4].strftime("%Y-%m-%d %H:%M:%S"),
                    e[5].strftime("%Y-%m-%d %H:%M:%S"), e[6], e[7], e[8], e[9]])
    ctx.write_csv(fid, RUN_HEADER, out)
    ctx.agg(fid, {"interface_id": "CLX-IF-042"}, "count",
            lambda v: f"The October 2026 interface run log has {v} rows for CLX-IF-042.",
            rep={"interface_id": "CLX-IF-043"}, expect=0, notes="negation: CLX-IF-042 is not covered by this log")
    ctx.agg(fid, {"status": "ER"}, "count",
            lambda v: f"The October 2026 interface run log has {v} failed (ER) run, on CLX-IF-020 on 2026-10-22 (INC-2026-0340).",
            world_ref="INCIDENT:INC-2026-0340", expect=1)
    ctx.agg(fid, {"interface_id": "CLX-IF-043"}, "count",
            lambda v: f"CLX-IF-043 (GL Reserve Journal Feed) ran {v} times in October 2026, scheduled daily 03:45.",
            world_ref="INTERFACE:CLX-IF-043#schedule_history")
    ctx.agg(fid, {"interface_id": "CLX-IF-033"}, "count",
            lambda v: f"CLX-IF-033 (NISA-FR1 fraud referral return) ran {v} time in October 2026, on the 5th business day after quarter end.",
            world_ref="INTERFACE:CLX-IF-033#schedule")
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST021 GL postings October 2026 (payments and recoveries)
# =============================================================================================

GL_HEADER = ["posting_id", "gl_period", "posting_date", "account_code", "account_name", "dr_cr", "amount_gbp",
             "source_type", "source_ref", "claim_id", "product_code", "region", "source_system",
             "source_program_or_service", "interface"]
ACCOUNTS = {
    "pay_ind": ("5100100", "Claims paid - indemnity"), "pay_fee": ("5100200", "Claims paid - loss adjusting fees"),
    "clear": ("1200300", "Claims payments clearing - CPG"), "rcpt": ("1200310", "Recovery receipts clearing"),
    "sub": ("5200100", "Subrogation recoveries"), "salv": ("5200200", "Salvage proceeds"),
    "exr": ("5200300", "Excess recoveries"),
}


def build_st021(ctx):
    fid = "ST021"
    pays = [p for p in ctx.data["payments"] if p["payment_date"].startswith("2026-10")
            and p["payment_status"] in ("CONFIRMED", "SENT")]
    rcpts = [x for x in ctx.data["receipts"] if x["date"] >= D("2026-10-01")]
    lines = []
    for p in pays:
        hub = p["source_system"] == "Claims Hub"
        src = ("gl-posting-svc", "CLX-IF-050") if hub else ("CLRGL010", "CLX-IF-028")
        acct = ACCOUNTS["pay_fee"] if p["payee_type"] == "vendor_fee" else ACCOUNTS["pay_ind"]
        for dc, a in (("D", acct), ("C", ACCOUNTS["clear"])):
            lines.append((p["payment_date"], a, dc, p["amount_gbp"], "PAYMENT", p["payment_id"], p["claim_id"],
                          p["product_code"], p["region"], p["source_system"], src[0], src[1]))
    for x in rcpts:
        c = x["claim"]
        hub = C.on_hub(c["product_code"], x["date"])
        src = ("gl-posting-svc", "CLX-IF-050") if hub else ("CLRGL070", "CLX-IF-029")
        amt = money(round(x["amount"] * C.fx_latest(c["currency"]), 2))
        cr_acct = {"SB": ACCOUNTS["sub"], "SV": ACCOUNTS["salv"], "EX": ACCOUNTS["exr"]}[x["type"]]
        for dc, a in (("D", ACCOUNTS["rcpt"]), ("C", cr_acct)):
            lines.append((iso(x["date"]), a, dc, amt, "RECOVERY", x["recovery_id"], c["claim_id"], c["product_code"],
                          c["region"], "Claims Hub" if hub else "CLARA", src[0], src[1]))
    lines.sort(key=lambda l: (l[0], l[5], l[2] == "C"))
    out = []
    for k, l in enumerate(lines, 1):
        out.append([f"GLP-202610-{k:07d}", "202610", l[0], l[1][0], l[1][1], l[2], l[3], l[4], l[5], l[6], l[7], l[8],
                    l[9], l[10], l[11]])
    ctx.write_csv(fid, GL_HEADER, out)
    ctx.agg(fid, {"source_type": "PAYMENT", "dr_cr": "D"}, "sum",
            lambda v: f"October 2026 GL debit postings for claim payments total GBP {v:,.2f}, equal to the October confirmed/sent payments in ST016.",
            column="amount_gbp", world_ref="TABLE:CLR.T_GL_POSTING")
    ctx.agg(fid, {"source_type": "PAYMENT", "dr_cr": "C"}, "sum",
            lambda v: f"October 2026 GL credit postings to payments clearing total GBP {v:,.2f}.",
            column="amount_gbp", world_ref="TABLE:CLR.T_GL_POSTING")
    ctx.agg(fid, {"source_program_or_service": "gl-posting-svc"}, "count",
            lambda v: f"{v:,} October 2026 GL posting lines came from Claims Hub gl-posting-svc (CLX-IF-050).",
            world_ref="INTERFACE:CLX-IF-050")
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST022 currency rates
# =============================================================================================

def build_st022(ctx):
    fid = "ST022"
    d = adate(fid)
    out = []
    fx = C.P["fx_to_gbp_quarter_end"]
    for rd in sorted(fx):
        if rd > iso(d):
            continue
        for ccy in ("NOK", "SEK", "DKK"):
            rt = "YE" if rd.endswith("12-31") else "ME"
            out.append([rd, ccy, f"{fx[rd][ccy]:.4f}", rt, "quarter-end", "Group Ledger", "CLX-IF-027", "CLRGL030"])
    header = ["rate_date", "currency", "rate_to_gbp", "rate_type", "period_basis", "source_system", "interface", "loaded_by"]
    R = ctx.write_csv(fid, header, out)
    for i, rr in enumerate(R, 1):
        if rr["rate_date"] == "2026-09-30":
            ctx.cfact(fid, i, "rate_to_gbp", rr["rate_to_gbp"],
                      f"Quarter-end rate at 2026-09-30: {rr['currency']}/GBP {rr['rate_to_gbp']}.",
                      kind="needle", world_ref="PROFILE:fx_to_gbp_quarter_end#2026-09-30", link=f"fx2026q3:{rr['currency']}")
        if rr["rate_date"] == "2024-12-31" and rr["currency"] == "NOK":
            ctx.cfact(fid, i, "rate_type", "YE", "The 2024-12-31 rates are loaded as year-end (YE) rates.",
                      world_ref="TABLE:CLR.T_CURRENCY_RATE#columns.RATE_TYPE_CD")
    for i, rr in enumerate(R, 1):
        if rr["rate_date"] == "2025-06-30" and rr["currency"] == "DKK":
            ctx.cfact(fid, i, "rate_to_gbp", rr["rate_to_gbp"], f"DKK/GBP quarter-end rate at 2025-06-30 is {rr['rate_to_gbp']}.",
                      world_ref="PROFILE:fx_to_gbp_quarter_end#2025-06-30")
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST023 incident log
# =============================================================================================

def _scrub_incident(text: str) -> str:
    # CICS region names are reserved for the CLARA architecture document
    return re.sub(r"\s*CICSPRD\d\s*", " ", text).replace("  ", " ").strip()


def _incident_status_asof(status: str, d: dt.date) -> str:
    """Drop status clauses that mention a date after the log's as-of date (e.g. a later fix release)."""
    parts = [p.strip() for p in status.split(";")]
    keep = [p for p in parts if all(m <= iso(d) for m in re.findall(r"\d{4}-\d{2}-\d{2}", p))]
    if len(keep) < len(parts) and keep == ["mitigated"]:
        keep.append("permanent fix in progress")
    return "; ".join(keep) or "open"


def build_st023(ctx):
    fid = "ST023"
    d = adate(fid)
    header = ["incident_id", "date", "start", "end", "severity", "title", "systems", "programs", "interfaces",
              "root_cause", "impact", "fix_tickets", "owner", "status"]
    out = []
    for iid, x in sorted(W.incidents.items(), key=lambda kv: (kv[1]["start"], kv[0])):
        if x["date"] > iso(d):
            continue
        for f in ("title", "root_cause", "impact", "fix_tickets", "owner"):
            require(fid, f"INCIDENT:{iid}", f)
        status = _incident_status_asof(x.get("status") or "closed", d)
        out.append([iid, x["date"], x["start"].replace("T", " "), (x.get("end") or "").replace("T", " "), x["severity"],
                    csv_text(_scrub_incident(x["title"])), " / ".join(sysname(s, d) for s in x["systems"]),
                    " ".join(x["programs"]), " ".join(x["interfaces"]), csv_text(x["root_cause"]),
                    csv_text(x["impact"]), " ".join(x["fix_tickets"]), pname(x["owner"], d), csv_text(status)])
    R = ctx.write_csv(fid, header, out)
    for i, rr in enumerate(R, 1):
        if rr["incident_id"] == "INC-2025-0412":
            ctx.cfact(fid, i, "severity", "Sev1", "INC-2025-0412 (GL reserve journals rejected after the CLX-IF-042 layout change) was a Sev1 incident.",
                      kind="needle", world_ref="INCIDENT:INC-2025-0412#severity")
            ctx.cfact(fid, i, "fix_tickets", "CHUB-142", "INC-2025-0412 was fixed under CHUB-142, CHUB-143 and CHUB-144.",
                      world_ref="INCIDENT:INC-2025-0412#fix_tickets")
        if rr["incident_id"] == "INC-2026-1007":
            ctx.cfact(fid, i, "impact", "9 Tier-3 claims scored 60", "INC-2026-1007: 9 Tier-3 claims scored 60-64 between 2026-10-01 and 2026-10-05 were not referred by Claims Hub and were referred manually.",
                      kind="needle", world_ref="INCIDENT:INC-2026-1007#impact")
        if rr["incident_id"] == "INC-2026-0914":
            ctx.cfact(fid, i, "impact", "41,236.50", "INC-2026-0914: 18 claims were paid twice on the Wave 1 cut-over, total GBP 41,236.50, all recalled by 2026-09-18.",
                      kind="needle", world_ref="INCIDENT:INC-2026-0914#impact")
        if rr["incident_id"] == "INC-2026-0518":
            ctx.cfact(fid, i, "owner", rr["owner"], f"INC-2026-0518 (batch fraud sweep used the pre-2026 threshold) is owned by {rr['owner']}.",
                      world_ref="INCIDENT:INC-2026-0518#owner")
        if rr["incident_id"] == "INC-2025-0233":
            ctx.cfact(fid, i, "fix_tickets", "CHUB-119", "INC-2025-0233 (Sentinel scoring failures after the FRAUDNET rename) was fixed under CHUB-119.",
                      world_ref="INCIDENT:INC-2025-0233#fix_tickets")
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST024 Jira ticket summary
# =============================================================================================

# recovery-svc and document-svc are left out of the filler on purpose (their 2026-11 ownership move is
# documented elsewhere); notification-svc filler goes to its owning squad lead only.
COMPONENTS = ["fnol-intake-svc", "triage-svc", "assessment-svc", "claim-core-svc", "notification-svc", "reserve-engine",
              "gl-posting-svc", "fraud-referral-svc", "settlement-svc", "payment-orchestrator", "CLARA", "Integration",
              "Data Migration", "Platform"]
COMP_ASSIGNEES = {"fnol-intake-svc": ["P040"], "triage-svc": ["P040"], "assessment-svc": ["P040"], "claim-core-svc": ["P040"],
                  "notification-svc": ["P040"], "reserve-engine": ["P041", "P053"], "gl-posting-svc": ["P041"],
                  "fraud-referral-svc": ["P042"], "settlement-svc": ["P042"], "payment-orchestrator": ["P042"],
                  "recovery-svc": ["P043", "P042"], "document-svc": ["P043"], "CLARA": ["P023", "P024", "P025"],
                  "Integration": ["P031", "P050"], "Data Migration": ["P051"], "Platform": ["P053", "P049"]}
FILLER_TPL = [
    ("Story", "{c}: add structured logging fields"), ("Story", "{c}: contract test coverage for error responses"),
    ("Bug", "{c}: validation message wording on optional field"), ("Task", "{c}: dependency patch upgrades"),
    ("Story", "{c}: improve pagination on list endpoint"), ("Bug", "{c}: flaky integration test in pipeline"),
    ("Task", "{c}: dashboard panel tidy-up"), ("Story", "{c}: accessibility review fixes"),
    ("Bug", "{c}: incorrect sort order in admin view"), ("Task", "{c}: housekeeping of feature flags"),
    ("Task", "{c}: refresh developer onboarding notes"), ("Story", "{c}: health endpoint detail for operations"),
    ("Bug", "{c}: log noise on graceful shutdown"), ("Task", "{c}: container base image refresh"),
    ("Story", "{c}: audit trail field for last editor"), ("Task", "{c}: test data clean-up script"),
]
CLARA_TPL = ["{c}: tidy JCL comments", "{c}: copybook documentation refresh", "{c}: DB2 runstats review",
             "{c}: retire unused test datasets", "{c}: compile listing archive tidy-up"]


def ticket_status_asof(t: dict, d: str) -> tuple[str, str]:
    hist = t.get("status_history")
    status = t["status"]
    resolved = t.get("resolved") or ""
    if hist:
        cur = None
        for h in hist:
            if h["from"] <= d:
                cur = h["status"]
        status = cur or hist[0]["status"]
    if resolved and resolved > d:
        resolved = ""
        if status in ("Done", "Won't Do"):
            status = "In Progress"
    return status, resolved


def build_st024(ctx):
    fid = "ST024"
    d = adate(fid)
    ds = iso(d)
    r = rng("ST024:filler")
    fixv = [(f["name"], f["release_date"]) for f in W.raw["key_tickets"]["fix_versions"]]
    header = ["key", "issue_type", "summary", "status", "assignee", "reporter", "created", "resolved", "component",
              "fix_version", "labels"]
    out = []
    for n in range(101, 2101):
        key = f"CHUB-{n}"
        t = W.tickets.get(key)
        if t:
            if t["created"] > ds:
                continue
            status, resolved = ticket_status_asof(t, ds)
            labels = " ".join(l for l in t.get("labels") or [] if l != "generated-filler")
            out.append([key, t["type"], csv_text(temporalize(t["summary"], d)), status, pname(t["assignee"], d),
                        pname(t.get("reporter"), d), t["created"], resolved, t["component"], t.get("fix_version") or "",
                        labels])
            continue
        comp = r.choice(COMPONENTS)
        typ, tpl = r.choice(FILLER_TPL)
        if comp == "CLARA":
            tpl = r.choice(CLARA_TPL)
        created = D("2025-01-20") + dt.timedelta(days=int((n - 101) / 2000 * 650) + r.randint(-12, 12))
        created = min(max(created, D("2025-01-20")), d - dt.timedelta(days=1))
        done = r.random() < (0.80 if created < D("2026-06-01") else 0.45)
        resolved = created + dt.timedelta(days=r.randint(2, 40)) if done else None
        if resolved and resolved > d:
            resolved, done = None, False
        status = "Done" if done else r.choice(["To Do", "In Progress", "In Progress", "In Review"])
        fv = ""
        ref = resolved or created
        for name, rel in fixv:
            if iso(ref) <= rel:
                fv = name
                break
        assignee = r.choice(COMP_ASSIGNEES[comp])
        if not W.employed(assignee, iso(created)):
            assignee = COMP_ASSIGNEES[comp][0]
        out.append([key, typ, tpl.format(c=comp), status, pname(assignee, d), "", iso(created),
                    iso(resolved) if resolved else "", comp, fv, ""])
    R = ctx.write_csv(fid, header, out)
    for i, rr in enumerate(R, 1):
        if rr["key"] == "CHUB-298":
            ctx.cfact(fid, i, "status", "In Review", "Jira summary (2026-11-11): CHUB-298 (CLRFR040 hard-codes 070) is In Review, assigned to Keith Barraclough.",
                      kind="temporal", world_ref="TICKET:CHUB-298#status_history")
            ctx.cfact(fid, i, "assignee", "Keith Barraclough", "CHUB-298 is assigned to Keith Barraclough.",
                      world_ref="TICKET:CHUB-298#assignee")
        if rr["key"] == "CHUB-233":
            ctx.cfact(fid, i, "resolved", "2026-02-10", "CHUB-233 (rename reserve-svc to reserve-engine) was resolved on 2026-02-10.",
                      kind="needle", world_ref="TICKET:CHUB-233")
        if rr["key"] == "CHUB-143":
            ctx.cfact(fid, i, "resolved", rr["resolved"], f"CHUB-143 was resolved on {rr['resolved']}.",
                      world_ref="TICKET:CHUB-143")
        if rr["key"] == "CHUB-441":
            ctx.cfact(fid, i, "summary", "Wave 2 cut-over plan", "CHUB-441: Wave 2 cut-over plan v1 (freeze 2027-02-12 18:00 to 2027-02-15 06:00), status To Do.",
                      world_ref="TICKET:CHUB-441")
    ctx.agg(fid, {}, "count", lambda v: f"The CHUB Jira ticket summary of 2026-11-11 lists {v:,} tickets (CHUB-101 to CHUB-2100).",
            needle_col="key")
    ctx.agg(fid, {"status": "In Review"}, "count", lambda v: f"{v} tickets in the 2026-11-11 Jira summary are In Review.")
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST025 product-peril matrix 2026
# =============================================================================================

def build_st025(ctx):
    fid = "ST025"
    d = adate(fid)
    header = ["product_id", "product_name", "product_code", "line", "region", "currency", "claim_type", "claim_type_name",
              "local_name", "peril_code", "excess_basis", "excess_amount", "excess_text", "local_excess_term",
              "other_terms"]
    sym = {"GBP": "£", "NOK": "NOK ", "SEK": "SEK ", "DKK": "DKK "}
    out = []
    for pid, p in W.products.items():
        require(fid, f"PRODUCT:{pid}", "excess")
        ex = p["excess"]
        for ct in p["claim_types"]:
            c = W.claim_types[ct]
            basis = None
            if ct == "CT-WSC" and "windscreen" in ex:
                basis = "windscreen"
            elif ct == "CT-EOW" and "escape_of_water" in ex:
                basis = "escape_of_water"
            elif ct == "CT-SUB" and "subsidence" in ex:
                basis = "subsidence"
            elif ct == "CT-TPD" and "property_damage" in ex:
                basis = "property_damage"
            elif "standard" in ex:
                basis = "standard"
            amt = ex.get(basis) if basis else None
            other = ""
            if ct == "CT-BIN" and p.get("bi_indemnity_period_months"):
                bi = p["bi_indemnity_period_months"]
                other = f"BI indemnity period {bi['standard']} months (optional {bi['optional']})"
            if ct == "CT-PLB" and p.get("limits") and may(fid, f"PRODUCT:{pid}", "limits"):
                other = f"Public liability limit £{p['limits']['public_liability']:,}"
            if ct == "CT-BIJ" and p.get("limits") and may(fid, f"PRODUCT:{pid}", "limits"):
                other = f"Employers liability limit £{p['limits']['employers_liability']:,}"
            text = f"{sym[p['currency']]}{amt:,}" if amt is not None else "No excess specified"
            out.append([pid, p["name"], p["code"], p["line"], p["region"], p["currency"], ct, c["name"],
                        (c.get("local_names") or {}).get(p["region"], ""), c["peril_code"], basis or "", amt if amt is not None else "",
                        text, p["local_excess_term"], other])
    R = ctx.write_csv(fid, header, out)
    pl = placement(fid, "st25_sek2000")
    tagged = False
    for i, rr in enumerate(R, 1):
        if rr["product_id"] == "PRD-HOM-SE" and rr["excess_basis"] == "standard" and not tagged:
            ctx.cfact(fid, i, "excess_text", "SEK 2,000", "Product-peril matrix 2026: Hem Sverige (PRD-HOM-SE) standard självrisk is SEK 2,000.",
                      kind="contradiction_new", world_ref="PRODUCT:PRD-HOM-SE#excess.standard", placement=pl)
            tagged = True
        if rr["product_id"] == "PRD-HOM-UK" and rr["claim_type"] == "CT-SUB":
            ctx.cfact(fid, i, "excess_text", "£1,000", "Home Buildings & Contents UK: subsidence excess £1,000.",
                      kind="needle", world_ref="PRODUCT:PRD-HOM-UK#excess.subsidence")
        if rr["product_id"] == "PRD-HOM-UK" and rr["claim_type"] == "CT-EOW":
            ctx.cfact(fid, i, "excess_text", "£400", "Home Buildings & Contents UK: escape of water excess £400.",
                      kind="needle", world_ref="PRODUCT:PRD-HOM-UK#excess.escape_of_water")
        if rr["product_id"] == "PRD-MOT-NO" and rr["claim_type"] == "CT-WSC":
            ctx.cfact(fid, i, "excess_text", "NOK 2,000", "Motor Privat Norge: windscreen egenandel NOK 2,000.",
                      kind="needle", world_ref="PRODUCT:PRD-MOT-NO#excess.windscreen")
        if rr["product_id"] == "PRD-COM-UK" and rr["claim_type"] == "CT-BIN":
            ctx.cfact(fid, i, "other_terms", "12 months", "Commercial Property UK: BI indemnity period 12 months standard (24 optional).",
                      world_ref="PRODUCT:PRD-COM-UK#bi_indemnity_period_months")
        if rr["product_id"] == "PRD-HOM-DK" and rr["claim_type"] == "CT-FRO":
            ctx.cfact(fid, i, "local_name", "Frostskade", "Hjem Danmark covers Frost Damage (Frostskade) with selvrisiko DKK 1,500.",
                      world_ref="PRODUCT:PRD-HOM-DK#excess.standard")
    ctx.agg(fid, {"claim_type": "CT-SUB", "region": {"ne": "UK"}}, "count",
            lambda v: f"The product-peril matrix lists {v} Nordic products covering Subsidence (CT-SUB).",
            rep={"claim_type": "CT-SUB"}, expect=0, world_ref="CLAIMTYPE:CT-SUB#uk_only", notes="negation")
    ctx.done(fid, f"{len(out)} rows")


# =============================================================================================
# ST026 copybook fields (matches copybooks.yaml)
# =============================================================================================

def pic_bytes(pic: str | None) -> int | None:
    if not pic:
        return None
    p = pic.upper()
    usage = "DISPLAY"
    if "COMP-3" in p:
        usage = "COMP-3"
    elif re.search(r"\bCOMP\b", p):
        usage = "COMP"
    core = p.split()[0]
    digits = 0
    chars = 0
    for m in re.finditer(r"([9XAS])(\((\d+)\))?|V", core):
        if m.group(0) == "V":
            continue
        ch = m.group(1)
        n = int(m.group(3)) if m.group(3) else 1
        if ch == "S":
            continue
        if ch == "9":
            digits += n
        else:
            chars += n
    if usage == "COMP-3":
        return math.ceil((digits + 1) / 2)
    if usage == "COMP":
        return 2 if digits <= 4 else 4 if digits <= 9 else 8
    return digits + chars


def pic_usage(pic: str | None) -> str:
    if not pic:
        return "GROUP"
    if "COMP-3" in pic.upper():
        return "COMP-3"
    if re.search(r"\bCOMP\b", pic.upper()):
        return "COMP"
    return "DISPLAY"


def build_st026(ctx):
    fid = "ST026"
    header = ["copybook", "kind", "table", "seq", "level", "field_name", "pic", "usage", "start_pos", "length_bytes",
              "used_by", "description"]
    out = []
    for name in sorted(W.copybooks):
        cb = W.copybooks[name]
        fields = cb["fields"]
        lens = [pic_bytes(f["pic"]) for f in fields]
        # group lengths: sum of subordinate elementary items
        glen = list(lens)
        for i, f in enumerate(fields):
            if f["pic"] is None:
                tot = 0
                for j in range(i + 1, len(fields)):
                    if fields[j]["level"] <= f["level"]:
                        break
                    if fields[j]["pic"] is not None:
                        tot += lens[j]
                glen[i] = tot
        pos = 1
        for i, f in enumerate(fields):
            start = pos
            if f["pic"] is not None:
                pos += lens[i]
            out.append([name, cb["kind"], cb.get("table") or "", i + 1, f["level"], f["name"], f["pic"] or "",
                        pic_usage(f["pic"]), start, glen[i], " ".join(cb.get("used_by") or []),
                        csv_text(cb.get("description") or "") if i == 0 else ""])
    R = ctx.write_csv(fid, header, out)
    for i, rr in enumerate(R, 1):
        if rr["copybook"] == "RSVMOVE" and rr["field_name"] == "RM-AMOUNT":
            ctx.cfact(fid, i, "pic", "S9(9)V99 COMP-3", "Copybook RSVMOVE: RM-AMOUNT is PIC S9(9)V99 COMP-3 (6 bytes).",
                      kind="needle", world_ref="COPYBOOK:RSVMOVE#fields.RM-AMOUNT")
        if rr["copybook"] == "RSVMOVE" and rr["field_name"] == "RM-REC-VERSION":
            ctx.cfact(fid, i, "pic", "9(2)", "Copybook RSVMOVE: RM-REC-VERSION is PIC 9(2), in the RM-HEADER group.",
                      kind="needle", world_ref="COPYBOOK:RSVMOVE#field_history")
        if rr["copybook"] == "RSVREC" and rr["seq"] == "1":
            ctx.cfact(fid, i, "table", "CLR.T_RESERVE", "Copybook RSVREC is the record layout of CLR.T_RESERVE.",
                      world_ref="COPYBOOK:RSVREC#table")
    ctx.agg(fid, {}, "count", lambda v: f"The copybook field list has {v} field rows.", needle_col="copybook",
            world_ref="COPYBOOK:RSVMOVE")
    ctx.agg(fid, {}, "distinct", lambda v: f"The copybook field list covers {v} copybooks.", column="copybook",
            needle_col="copybook")
    ctx.agg(fid, {"copybook": "RSVMOVE", "pic": {"ne": ""}}, "count",
            lambda v: f"Copybook RSVMOVE has {v} elementary fields.", world_ref="COPYBOOK:RSVMOVE#fields")
    ctx.done(fid, f"{len(out)} rows")


CSV_BUILDERS = [build_st013, build_st014, build_st015, build_st016, build_st017, build_st018, build_st019,
                build_st020, build_st021, build_st022, build_st023, build_st024, build_st025, build_st026]
