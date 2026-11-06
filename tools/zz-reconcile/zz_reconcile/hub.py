"""Claims Hub side: outstanding reserve per claim from reserve.reserve."""
import os

import psycopg

SQL = """
    SELECT r.claim_id, r.outstanding_amount, r.currency
      FROM reserve.reserve r
     WHERE r.status = 'OPEN'
"""


def load(cfg, products, business_date):
    out = {}
    with psycopg.connect(os.environ[cfg["dsn_env"]]) as conn:
        for claim_id, amount, currency in conn.execute(SQL):
            out[claim_id] = (amount, currency)
    return out
