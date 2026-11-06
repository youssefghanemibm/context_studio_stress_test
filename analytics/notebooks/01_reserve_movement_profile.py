# %% [markdown]
# # Reserve movement profile
#
# Distribution of reserve movements by movement type and product, including RV revaluation movements.
# Connection settings come from the environment (`CDW_DSN`); see the README.

# %%
import os

import pandas as pd
import sqlalchemy as sa

engine = sa.create_engine(os.environ["CDW_DSN"])

# %%
df = pd.read_sql(sa.text("SELECT movement_type, source, currency, amount_minor, created_at FROM reserve_movement"), engine)
df.head()

# %%
df.groupby(['movement_type', 'currency'])['amount_minor'].describe()
