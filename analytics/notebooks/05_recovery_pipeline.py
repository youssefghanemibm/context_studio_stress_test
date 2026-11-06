# %% [markdown]
# # Recovery pipeline
#
# Open recovery cases by type and expected amount, and receipts over time.
# Connection settings come from the environment (`CDW_DSN`); see the README.

# %%
import os

import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine(os.environ["CDW_DSN"])

# %%
df = pd.read_sql(sa.text("SELECT type, status, expected_amount FROM recovery_case"), engine)
df.head()

# %%
df.pivot_table(index='type', columns='status', values='expected_amount', aggfunc='sum')
