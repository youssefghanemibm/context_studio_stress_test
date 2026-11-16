"""VS013 Claims KPI Dashboard – Q3 2026 (2026-10-14, Maja Holm, final).

The fraud referral rate (slide 4) and the 2026 H1 average settlement days (slide 5) appear only in
native charts (both exclusive to this file)."""
from __future__ import annotations

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck


def build(W, out_dir):
    D = Deck(W, "VS013", version="1.0", doc_ref="MI-KPI-2026Q3", out_dir=out_dir)
    d = D.date
    rng = D.rng
    met = W.timeline["metrics"]
    fy = W.company["financials"]["fy2025"]

    # 1 title
    D.title_slide(D.title, "Quarterly claims performance pack",
                  [f"Data & Analytics  |  {D.date_long()}", f"Prepared by: {D.author}, {D.author_title}",
                   "Status: Final"])

    # 2 contents
    CM.agenda(D, ["FY2025 baseline", "Fraud referral rate", "Average settlement days", "Claims notified",
                  "SIU referrals", "Claim mix", "Definitions", "Data sources", "Dashboard view"], title="Contents",
              kicker="KPI dashboard")

    # 3 FY2025 baseline tiles
    s = D.content("FY2025 baseline", "Baseline")
    for k in ("claims_notified", "fraud_referrals", "confirmed_fraud_cases", "fraud_savings_gbp_m"):
        D.need("ORG:company", f"financials.fy2025.{k}")
    tiles = [("Claims notified", f"{fy['claims_notified']:,}"), ("SIU referrals", f"{fy['fraud_referrals']:,}"),
             ("Confirmed fraud cases", f"{fy['confirmed_fraud_cases']:,}"), ("Fraud savings", f"£{fy['fraud_savings_gbp_m']}m")]
    for i, (lab, val) in enumerate(tiles):
        x = 0.5 + i * 3.1
        s.box(x, 1.6, 2.9, 1.9, [{"text": val, "bold": True, "size": 28, "color": "navy"},
                                 {"text": lab, "size": 12, "color": "slate"}], style="tile", margins=0.1)
    s.text(0.5, 3.9, 12.3, 1.2, [{"text": "Full-year 2025 figures from the annual claims and reserving filing, used as the comparison base for 2026.", "size": 12}],
           size=12, color="slate")
    s.notes(P.notes(rng, "the 2025 baseline", n_filler=1))
    D.fact(s, "text", f"{fy['fraud_referrals']:,}", "FY2025: 4,812 SIU referrals and 1,109 confirmed fraud cases.",
           world_ref="ORG:company#financials.fy2025.fraud_referrals")
    D.fact(s, "text", f"£{fy['fraud_savings_gbp_m']}m", "FY2025 fraud savings were £38.7m.",
           world_ref="ORG:company#financials.fy2025.fraud_savings_gbp_m")

    # 4 fraud referral rate (chart only)
    s = D.content("Fraud referral rate", "Fraud")
    rr = met["fraud_referral_rate_pct_of_scored"]
    cats = [f"{k[:4]} {k[4:]}" for k in rr]
    s.chart(0.5, 1.4, 8.4, 5.45, "line", cats, [("Referral rate (% of scored claims)", list(rr.values()))],
            title="Fraud referral rate (% of scored claims) – threshold 65 from 1 Apr 2026", number_format="0.0",
            label_format="0.0", colors=["red"], legend=False, axis_min=0, axis_max=3.5)
    s.box(9.2, 1.6, 3.6, 3.2, [{"text": "Commentary", "bold": True, "size": 13},
                               {"text": "The rate stepped up when the referral threshold changed in April 2026 and held in Q3.", "size": 12},
                               {"text": "Tier-3 referrals at the lower threshold start in Q4 2026.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "the fraud referral rate",
                    ["The denominator is every claim scored by Sentinel in the quarter."]))
    D.place("vs13_referral_rate", s, "chart", "Referral rate (% of scored claims): 2026 Q3=2.8",
            notes="Q1 2026 = 2.3 and Q2 2026 = 2.8 are the preceding points; the threshold note is in the chart title.")
    D.place("vs13_referral_rate", s, "chart", "Referral rate (% of scored claims): 2026 Q1=2.3",
            statement="Fraud referral rate Q1 2026: 2.3% of scored claims (chart only).")
    D.fact(s, "chart", "title: Fraud referral rate (% of scored claims) – threshold 65 from 1 Apr 2026",
           "Chart title notes the referral threshold of 65 from 2026-04-01.", kind="chart_only",
           world_ref="RULE:BR-FRD-031@v1#parameters.threshold")

    # 5 settlement days (chart only)
    s = D.content("Average settlement days", "Settlement")
    sd = met["avg_settlement_days_2026H1"]
    s.chart(0.5, 1.4, 8.4, 5.45, "column", ["Motor", "Home"],
            [("FY2025", [fy["avg_settlement_days_motor"], fy["avg_settlement_days_home"]]),
             ("2026 H1", [sd["motor"], sd["home"]])],
            title="Average settlement days by line", colors=["grey", "teal"])
    s.box(9.2, 1.6, 3.6, 3.0, [{"text": "Commentary", "bold": True, "size": 13},
                               {"text": "Both lines settled faster in the first half of 2026 than in 2025.", "size": 12},
                               {"text": "Second-half figures follow with the full-year pack.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "settlement speed", n_filler=1))
    D.place("vs13_settle_days", s, "chart", "2026 H1: Motor=31",
            notes="Second series of the clustered column chart; Home = 47.")
    D.place("vs13_settle_days", s, "chart", "2026 H1: Home=47", statement="Average settlement days 2026 H1: home 47 (chart only).")
    D.fact(s, "chart", "FY2025: Motor=34", "FY2025 average settlement days: motor 34, home 51.", kind="chart_only",
           world_ref="ORG:company#financials.fy2025.avg_settlement_days_motor")

    # 6 claims notified (chart)
    s = D.content("Claims notified", "Volumes")
    cn = met["claims_notified"]
    s.chart(0.5, 1.4, 7.4, 5.45, "column", ["Q2 2026", "Q3 2026"], [("Claims notified", [cn["2026Q2"], cn["2026Q3"]])],
            title="Claims notified per quarter", legend=False, colors=["navy"], label_format="#,##0")
    s.bullets(8.3, 1.6, 4.5, 4.5, ["Includes all channels and all regions.",
                                   "Q3 includes the first weeks of UK motor on Claims Hub.",
                                   "Seasonal weather events are not adjusted out."], size=12)
    s.notes(P.notes(rng, "claim volumes", n_filler=1))
    D.fact(s, "chart", f"Claims notified: Q3 2026={cn['2026Q3']}", "Claims notified: 53,140 in Q2 2026 and 55,180 in Q3 2026.",
           kind="chart_only", world_ref="TIMELINE:metrics#claims_notified")

    # 7 SIU referrals (chart) + FR1
    s = D.content("SIU referrals", "Fraud")
    fc = met["fraud_referrals_count"]
    q2 = W.reports["NISA-FR1"]["submissions"]["2026Q2"]
    s.chart(0.5, 1.4, 7.4, 5.45, "column", ["Q2 2026", "Q3 2026"], [("SIU referrals", [fc["2026Q2"], fc["2026Q3"]])],
            title="SIU referrals per quarter", legend=False, colors=["red"], label_format="#,##0")
    s.box(8.3, 1.6, 4.5, 2.6, [{"text": "NISA-FR1", "bold": True, "size": 13},
                               {"text": f"Q2 2026 return submitted {D.date_long(q2['submitted'])} (due {D.date_long(q2['due'])}).", "size": 12},
                               {"text": "Q3 2026 return due 30 October 2026.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "referral volumes and the regulatory return", n_filler=1))
    D.fact(s, "chart", f"SIU referrals: Q2 2026={fc['2026Q2']}", "SIU referrals: 1,488 in Q2 2026 and 1,530 in Q3 2026.",
           kind="chart_only", world_ref="TIMELINE:metrics#fraud_referrals_count")

    # 8 claim mix
    s = D.content("Claim mix", "Mix")
    D.need("TIMELINE:metrics", "tier3_share_pct")
    s.box(0.5, 1.6, 3.6, 2.0, [{"text": f"{met['tier3_share_pct']['2025']}%", "bold": True, "size": 32, "color": "navy"},
                               {"text": "Tier-3 share of claims, 2025", "size": 12, "color": "slate"}], style="tile")
    s.bullets(4.6, 1.6, 8.2, 4.8, [
        "Tier-3 (BR-TRI-003 v3): estimated incurred of £50,000 or more, any bodily injury, litigation at notification, or a property total loss.",
        "Tier-3 claims route to Major & Complex Loss within 4 hours (BR-TRI-004).",
        "Tier-3 reserves are reviewed at least every 14 days from 1 July 2026.",
    ], size=13)
    s.notes(P.notes(rng, "the claim mix", n_filler=1))
    D.fact(s, "text", f"{met['tier3_share_pct']['2025']}%", "Tier-3 claims were 4.1% of claims in 2025.",
           world_ref="TIMELINE:metrics#tier3_share_pct")

    # 9 section
    D.section("02", "Definitions and data", "How the measures are built")

    # 10 definitions
    s = D.content("KPI definitions", "Definitions")
    s.table(0.5, 1.45, 12.3, ["Measure", "Definition", "Source"], [
        ("Fraud referral rate", "SIU referrals as a percentage of claims scored by Sentinel in the period", "Claims Data Warehouse"),
        ("Average settlement days", "Average calendar days to settlement, by line of business", "Claims Data Warehouse"),
        ("Claims notified", "New claims notified in the period, all channels", "Claims Data Warehouse"),
        ("SIU referrals", "Referrals created in the period", "SIU Case Manager via the warehouse"),
        ("Tier-3 share", "Claims classified Tier-3 as a share of all claims", "Claims Data Warehouse")],
        col_w=[2.4, 7.0, 2.9], row_h=0.6, size=11, first_col_bold=True)
    s.notes(P.notes(rng, "how each KPI is defined", n_filler=1))

    # 11 data sources
    s = D.content("Data sources", "Data")
    rows = []
    for iid in ["CLX-IF-030", "CLX-IF-044", "CLX-IF-056", "CLX-IF-058"]:
        i = W.interfaces[iid]
        D.need(f"INTERFACE:{iid}", "schedule")
        rows.append((iid, i["name"], f"{W.system_name(i['source_system'], d)} → {W.system_name(i['target_system'], d)}",
                     W.interface_schedule(iid, d)))
    s.table(0.5, 1.45, 12.3, ["Feed", "Name", "Source → target", "Schedule"], rows, col_w=[1.3, 3.6, 4.6, 2.8],
            row_h=0.55, size=11, first_col_bold=True)
    s.text(0.5, 4.5, 12.3, 1.0, [{"text": f"The Claims Data Warehouse is owned by {W.name_of('P036', d)} ({W.title_of('P036', d)}).", "size": 12}],
           size=12, color="slate")
    s.notes(P.notes(rng, "where the numbers come from", n_filler=1))
    D.fact(s, "table", "Daily claims MI to CDW", "CLX-IF-030 Daily claims MI to CDW (CLARA → Claims Data Warehouse) runs daily 04:30.",
           world_ref="INTERFACE:CLX-IF-030#schedule")

    # 12 dashboard view
    s = D.content("Dashboard view", "Dashboard")
    png = R.ui_screen(
        "Claims MI", f"{D.author} · Data & Analytics",
        ["Overview", "Volumes", "Fraud", "Settlement", "Reserving", "Exports"], "Volumes",
        "Dashboards  /  Claims volumes  /  Q3 2026", "Claims volumes – Q3 2026",
        [("Claims notified, Q3 2026", f"{met['claims_notified']['2026Q3']:,}"), ("Claims notified, Q2 2026", f"{met['claims_notified']['2026Q2']:,}"),
         ("SIU referrals, Q3 2026", f"{fc['2026Q3']:,}"), ("SIU referrals, Q2 2026", f"{fc['2026Q2']:,}"),
         ("Source", "Claims Data Warehouse"), ("Refreshed", "Daily after the 04:30 load")],
        chips=[("Q3 2026", "teal"), ("FINAL", "green")], env="MI")
    s.picture_fit(png, 0.9, 1.35, 11.5, 5.55,
                  alt="Claims MI dashboard view for Q3 2026 showing claims notified and SIU referrals for Q2 and Q3 2026.")
    s.notes(P.notes(rng, "the live dashboard behind this pack", n_filler=1))
    D.fact(s, "image", "55,180", "Dashboard screenshot shows 55,180 claims notified in Q3 2026.", kind="screenshot",
           world_ref="TIMELINE:metrics#claims_notified.2026Q3")

    # 13 caveats
    s = D.content("Notes and caveats", "Notes")
    s.bullets(0.6, 1.5, 12.0, 4.8, ["UK motor claims migrated in Wave 1 are reported from Claims Hub from 14 September 2026.",
                                    "Danish claims have been reported from Claims Hub since Wave 0 on 1 June 2026.",
                                    "Quarter figures are final at the pack date; month figures may be restated.",
                                    "Fraud measures follow the referral rules in force in each quarter."], size=13)
    s.notes(P.notes(rng, "the caveats", n_filler=1))

    # 14 document control
    hist = CM.history_rows(D, [("0.1", ""), ("1.0", "")], spacing=(5, 9), kind="final")
    CM.doc_control(D, hist, [("P005", "Reviewed"), ("P008", "Reviewed")], status="Final",
                   reviewers=[W.name_of(x, d) for x in ("P011", "P009")],
                   distribution="Claims leadership team, Counter-Fraud & SIU, Finance",
                   purpose="Quarterly claims KPIs for Q3 2026.", approval_label="Review")

    # Facts appended after the original set so existing fact ids stay stable.
    D.place("vs13_referral_rate", 4, "chart", "Referral rate (% of scored claims): 2026 Q2=2.8",
            statement="Fraud referral rate Q2 2026: 2.8% of scored claims, the first quarter at the 65 threshold (chart only).")
    return D
