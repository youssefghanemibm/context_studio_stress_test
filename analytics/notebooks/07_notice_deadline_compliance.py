# %% [markdown]
# # Customer notice deadline compliance
#
# Fraud-referral customer notices sent before their due date, and deferrals.
# Connection settings come from the environment (`CDW_DSN`); see the README.

# %%
import os

import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine(os.environ["CDW_DSN"])

# %%
df = pd.read_sql(sa.text("SELECT due_date, deferred_until, sent_at FROM fraud_customer_notice"), engine)
df.head()

# %%
(df['sent_at'].dt.date <= df['due_date']).mean()
