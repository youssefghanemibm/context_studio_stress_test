"""Fact collection for the manifest (docs/CONVENTIONS.md §5)."""
from __future__ import annotations

from typing import Any


class Facts:
    """Collects manifest entries for one file; fact ids are <FILEID>-F<nnn> in insertion order."""

    def __init__(self, fid: str, file_rel: str):
        self.fid = fid
        self.file = file_rel
        self.items: list[dict] = []

    def add(self, kind: str, statement: str, needle: str, locator: dict, world_ref: str | None = None,
            exclusive: bool = False, placement: str | None = None, placement_key: str | None = None,
            also_in: list | None = None, notes: str | None = None) -> str:
        fact_id = f"{self.fid}-F{len(self.items) + 1:03d}"
        e: dict[str, Any] = {
            "fact_id": fact_id,
            "world_ref": world_ref,
            "kind": kind,
            "statement": statement,
            "file": self.file,
            "locator": locator,
            "needle": needle,
            "exclusive": bool(exclusive),
            "also_in": list(also_in or []),
        }
        if placement:
            e["placement"] = placement
            e["placement_key"] = placement_key
        if notes:
            e["notes"] = notes
        self.items.append(e)
        return fact_id


def spec(kind: str, statement: str, needle: str, world_ref: str | None = None, **kw) -> dict:
    """A fact specification whose locator is filled in by the builder (docx figure, pdf page...)."""
    d = {"kind": kind, "statement": statement, "needle": needle, "world_ref": world_ref}
    d.update(kw)
    return d


ARROW_NOTE = "raster arrow label: the fact is carried only by a labelled arrow inside the image (no native connector)"
CHART_NOTE = "raster chart rendered by matplotlib: the value exists only in pixels (no native chart data)"


def arrow_spec(statement: str, needle: str, world_ref: str | None = None, **kw) -> dict:
    """An arrow-label fact in a raster image. The verifier reserves kind arrow_only for native
    pptx connectors, so raster arrow labels are image_text with an explanatory note."""
    kw["notes"] = f"{ARROW_NOTE}; {kw['notes']}" if kw.get("notes") else ARROW_NOTE
    return spec("image_text", statement, needle, world_ref, **kw)


def chart_spec(statement: str, needle: str, world_ref: str | None = None, **kw) -> dict:
    """A value in a raster (matplotlib) chart. Kind chart_only is reserved for native xlsx/pptx charts."""
    kw["notes"] = f"{CHART_NOTE}; {kw['notes']}" if kw.get("notes") else CHART_NOTE
    return spec("image_text", statement, needle, world_ref, **kw)


def placement_spec(pl: dict, needle: str, statement: str | None = None, kind: str | None = None,
                   also_in_ids: list | None = None, notes: str | None = None) -> dict:
    """Fact spec for a world placement: copies world_ref, exclusive and kind."""
    return spec(kind or pl["kind"], statement or pl["fact"], needle, pl["world_ref"],
                exclusive=bool(pl.get("exclusive")), placement=pl["placement_id"], placement_key=pl["key"],
                also_in=also_in_ids if also_in_ids is not None else list(pl.get("also_in", [])),
                notes=notes)
