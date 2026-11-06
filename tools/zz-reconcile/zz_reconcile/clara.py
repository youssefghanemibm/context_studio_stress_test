"""CLARA side: reserve rows per claim from CLR.T_RESERVE (unload file or read replica)."""
import csv
import pathlib
from decimal import Decimal


def load(cfg, products, business_date):
    if cfg["source"] != "db2-unload":
        raise NotImplementedError("read-replica source is configured per environment")
    path = pathlib.Path(cfg["unload_dir"]) / f"T_RESERVE_{business_date:%Y%m%d}.csv"
    out = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["PRODUCT_CD"] not in products:
                continue
            out[row["CLAIM_ID"].strip()] = (Decimal(row["RSV_OUTSTANDING_AMT"]), row["RSV_CURRENCY_CD"])
    return out
