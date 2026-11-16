"""Run context: output folder, facts collector, shared data and summary lines."""
from __future__ import annotations

import pathlib
from typing import Any, Callable

from . import aggregates as A
from .common import Facts, W, write_csv


class Ctx:
    def __init__(self, out_dir: pathlib.Path, only: set[str] | None):
        self.out_dir = pathlib.Path(out_dir)
        self.only = only
        self.facts = Facts(self.out_dir)
        self.summary: list[tuple[str, int, str]] = []
        self.data: dict[str, Any] = {}

    def want(self, fid: str) -> bool:
        return self.only is None or fid in self.only

    def path(self, fid: str) -> pathlib.Path:
        return self.out_dir / W.anchor(fid)["filename"]

    def done(self, fid: str, units: str) -> None:
        p = self.path(fid)
        size = p.stat().st_size if p.exists() else 0
        self.summary.append((p.name, size, units))

    # ----------------------------------------------------------------------------- facts
    def xfact(self, fid: str, sheet: str, cell: str, needle: str, statement: str, kind: str = "general",
              hidden: bool = False, **kw) -> str:
        loc = {"kind": "xlsx_cell", "sheet": sheet, "cell": cell}
        if hidden:
            loc["hidden"] = True
        return self.facts.add(fid, kind, statement, loc, needle, **kw)

    def cfact(self, fid: str, row: int, column: str | None, needle: str, statement: str, kind: str = "general",
              **kw) -> str:
        loc = {"kind": "csv_row", "row": int(row)}
        if column is not None:
            loc["column"] = column
        return self.facts.add(fid, kind, statement, loc, needle, **kw)

    def chart_fact(self, fid: str, sheet: str, idx: int, needle: str, statement: str, kind: str = "chart_only",
                   **kw) -> str:
        loc = {"kind": "xlsx_chart", "sheet": sheet, "chart_index": idx}
        return self.facts.add(fid, kind, statement, loc, needle, **kw)

    # ----------------------------------------------------------------------------- CSV + aggregates
    def write_csv(self, fid: str, header: list[str], rows: list[list[Any]]) -> list[dict]:
        p = self.path(fid)
        str_rows = [["" if v is None else str(v) for v in r] for r in rows]
        if self.want(fid):
            write_csv(p, header, str_rows)
        dicts = [dict(zip(header, r)) for r in str_rows]
        self.data[f"{fid}:rows"] = dicts
        self.data[f"{fid}:header"] = header
        return dicts

    def agg(self, fid: str, flt: dict, op: str, statement: Callable[[Any], str], column: str | None = None,
            rep: dict | None = None, needle_col: str | None = None, world_ref: str | None = None,
            placement: dict | None = None, notes: str | None = None, expect: Any = None,
            kind: str = "aggregate_source") -> Any:
        rows = self.data[f"{fid}:rows"]
        val = A.evaluate(rows, flt, op, column)
        if expect is not None and not A.values_equal(val, expect):
            raise AssertionError(f"{fid} aggregate {flt} {op} = {val}, expected {expect}")
        rep_flt = rep if rep is not None else flt
        idx = A.first_match(rows, rep_flt)
        if idx is None:
            raise AssertionError(f"{fid}: no representative row for {rep_flt}")
        rrow = rows[idx - 1]
        if needle_col is None:
            needle_col = next((c for c, v in rep_flt.items() if not isinstance(v, dict)), None)
            if needle_col is None:
                needle_col = next(iter(rep_flt), None) or self.data[f"{fid}:header"][0]
        needle = f"{needle_col}: {rrow[needle_col]}"
        spec = {"file": self.facts.rel(fid), "filter": flt, "op": op, "value": val}
        if column:
            spec["column"] = column
        return self.facts.add(fid, kind, statement(val), {"kind": "csv_row", "row": idx}, needle,
                              world_ref=world_ref or "PROFILE:rows", placement=placement, notes=notes,
                              aggregate=spec), val
