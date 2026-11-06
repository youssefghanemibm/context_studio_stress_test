# %% [markdown]
# # FNOL channel trend
#
# First notices of loss by channel and month.
# Connection settings come from the environment (`CDW_DSN`); see the README.

# %%
import os

import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine(os.environ["CDW_DSN"])

# %%
df = pd.read_sql(sa.text("SELECT channel, date_trunc('month', received_at) AS month FROM fnol_notification"), engine)
df.head()

# %%
df.groupby(['month', 'channel']).size().unstack(fill_value=0)
