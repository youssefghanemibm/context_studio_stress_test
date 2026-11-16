"""Aggregate evaluation shared by the generator and generators/structured/check_aggregates.py.

An aggregate spec (stored in the manifest entry under `aggregate`) looks like
    {file, filter: {col: cond, ...}, op, column, value}

Conditions (all ANDed):
    "UK"                      equality on the raw CSV string
    {"in": [..]}              value in list
    {"prefix": "2025"}        string prefix (years and months of ISO dates)
    {"regex": "[CU]"}         re.search on the value
    {"gte": x} {"lte": x} {"gt": x} {"lt": x}   numeric when x is a number, else string compare
    {"ne": x}                 not equal

Ops:
    count        number of matching rows
    sum          sum of float(column), rounded to 2 dp
    max / min    max/min of float(column)
    distinct     number of distinct values of column
    top          most frequent value of column (ties: alphabetical); value is [top_value, count]
    top_month    most frequent column[:7] (YYYY-MM); value is [month, count]
"""
from __future__ import annotations

import collections
import csv
import re
from typing import Any, Iterable


def _cond_ok(v: str, cond: Any) -> bool:
    if not isinstance(cond, dict):
        return v == str(cond)
    for k, x in cond.items():
        if k == "in":
            if v not in [str(i) for i in x]:
                return False
        elif k == "prefix":
            if not v.startswith(str(x)):
                return False
        elif k == "regex":
            if not re.search(x, v):
                return False
        elif k == "ne":
            if v == str(x):
                return False
        elif k in ("gte", "lte", "gt", "lt"):
            if isinstance(x, (int, float)):
                try:
                    a = float(v)
                except ValueError:
                    return False
                b = float(x)
            else:
                a, b = v, str(x)
            if k == "gte" and not a >= b:
                return False
            if k == "lte" and not a <= b:
                return False
            if k == "gt" and not a > b:
                return False
            if k == "lt" and not a < b:
                return False
        else:
            raise ValueError(f"unknown condition {k}")
    return True


def match(row: dict, flt: dict) -> bool:
    return all(_cond_ok(row.get(c, ""), cond) for c, cond in (flt or {}).items())


def evaluate(rows: Iterable[dict], flt: dict, op: str, column: str | None = None) -> Any:
    sel = [r for r in rows if match(r, flt)]
    if op == "count":
        return len(sel)
    if op == "sum":
        return round(sum(float(r[column]) for r in sel), 2)
    if op == "max":
        return max(float(r[column]) for r in sel) if sel else None
    if op == "min":
        return min(float(r[column]) for r in sel) if sel else None
    if op == "distinct":
        return len({r[column] for r in sel})
    if op in ("top", "top_month"):
        vals = [r[column][:7] if op == "top_month" else r[column] for r in sel]
        c = collections.Counter(vals)
        if not c:
            return None
        best = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        return [best[0], best[1]]
    raise ValueError(f"unknown op {op}")


def first_match(rows: list[dict], flt: dict) -> int | None:
    """1-based index of the first matching row (header excluded)."""
    for i, r in enumerate(rows, 1):
        if match(r, flt):
            return i
    return None


def read_csv_dicts(path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def values_equal(a: Any, b: Any) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 0.005
    return str(a) == str(b)
