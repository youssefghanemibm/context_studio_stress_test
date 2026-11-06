# %% [markdown]
# # Tier-3 reserve review backlog
#
# Tier-3 claims whose next reserve review date has passed.
# Connection settings come from the environment (`CDW_DSN`); see the README.

# %%
import os

import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine(os.environ["CDW_DSN"])

# %%
df = pd.read_sql(sa.text("SELECT claim_id, next_review_date, cadence_days FROM review_schedule"), engine)
df.head()

# %%
df[df['next_review_date'] < pd.Timestamp.today().normalize()]
