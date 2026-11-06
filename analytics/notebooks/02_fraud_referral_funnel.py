# %% [markdown]
# # Fraud referral funnel
#
# Scored claims, referrals and SIU outcomes by tier and threshold applied.
# Connection settings come from the environment (`CDW_DSN`); see the README.

# %%
import os

import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine(os.environ["CDW_DSN"])

# %%
df = pd.read_sql(sa.text("SELECT tier, threshold_applied, sentinel_score, referred_at FROM fraud_referral"), engine)
df.head()

# %%
df.groupby(['tier', 'threshold_applied']).size()
