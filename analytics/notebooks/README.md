# Analytics notebooks

Exploratory notebooks for the Data & Analytics team, kept as plain Python files with
`# %%` cell markers so they diff cleanly.

## Data access

Analytics notebooks read from the CDW read replica cdw-ro-02.
Set `CDW_DSN` in your environment before running a notebook; credentials come from
the team vault and are never committed.

## Notebooks
- `01_reserve_movement_profile.py`: Distribution of reserve movements by movement type and product, including RV revaluation movements.
- `02_fraud_referral_funnel.py`: Scored claims, referrals and SIU outcomes by tier and threshold applied.
- `03_tier_mix_by_product.py`: Share of Tier-1, Tier-2 and Tier-3 claims per product.
- `04_settlement_cycle_time.py`: Days from first notice of loss to final settlement, by product and tier.
- `05_recovery_pipeline.py`: Open recovery cases by type and expected amount, and receipts over time.
- `06_fnol_channel_trend.py`: First notices of loss by channel and month.
- `07_notice_deadline_compliance.py`: Fraud-referral customer notices sent before their due date, and deferrals.
- `08_reserve_review_backlog.py`: Tier-3 claims whose next reserve review date has passed.

