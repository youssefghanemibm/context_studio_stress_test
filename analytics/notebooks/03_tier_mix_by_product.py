# %% [markdown]
# # Tier mix by product
#
# Share of Tier-1, Tier-2 and Tier-3 claims per product.
# Connection settings come from the environment (`CDW_DSN`); see the README.

# %%
import os

import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine(os.environ["CDW_DSN"])

# %%
df = pd.read_sql(sa.text("SELECT product_code, tier FROM claim"), engine)
df.head()

# %%
pd.crosstab(df['product_code'], df['tier'], normalize='index')
