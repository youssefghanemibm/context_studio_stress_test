"""Write differences to the configured target table, or print them."""
import os

import psycopg


def print_diffs(diffs):
    for d in diffs:
        print(f"{d.claim_id:22} {d.kind:18} {d.clara_amount!s:>16} {d.hub_amount!s:>16}")
    print(f"{len(diffs)} difference(s)")


def write(target, business_date, diffs):
    table = os.environ[target["table_env"]]
    with psycopg.connect(os.environ[target["dsn_env"]]) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                f"INSERT INTO {table} (business_date, claim_id, kind, clara_amount, hub_amount)"
                " VALUES (%s, %s, %s, %s, %s)",
                [(business_date, d.claim_id, d.kind, d.clara_amount, d.hub_amount) for d in diffs])
