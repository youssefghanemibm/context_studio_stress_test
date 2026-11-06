# %% [markdown]
# # Settlement cycle time
#
# Days from first notice of loss to final settlement, by product and tier.
# Connection settings come from the environment (`CDW_DSN`); see the README.

# %%
import os

import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine(os.environ["CDW_DSN"])

# %%
df = pd.read_sql(sa.text("SELECT c.product_code, c.tier, c.notified_at, s.agreed_at FROM claim c JOIN settlement s USING (claim_id) WHERE s.final"), engine)
df.head()

# %%
(df['agreed_at'] - df['notified_at']).dt.days.groupby(df['product_code']).median()
