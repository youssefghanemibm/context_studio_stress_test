"""Neutral phrase banks for the short prose around figures.

The prose here never states world facts (no thresholds, owners, dates, schedules, system or
table links). It only frames the figures, so image-only facts stay image-only.
"""
from __future__ import annotations

import random

PURPOSE = [
    "This document collects the {topic} figures in one place so that teams can refer to a single, controlled source.",
    "The purpose of this pack is to give {audience} a visual reference for {topic}.",
    "This pack brings together the {topic} diagrams that are otherwise spread across workshop outputs and design notes.",
    "It is intended as a quick visual reference for {audience}; the figures carry the detail and the text only frames them.",
    "The pack supports onboarding and day-to-day reference for {audience} working on {topic}.",
    "Use this document alongside the controlled procedures; it illustrates {topic} rather than replacing them.",
]

READING = [
    "Each figure is self-contained. Read the labels on boxes and arrows; the captions only identify the view.",
    "Figures are drawn at a consistent scale and colour scheme. The legend on each figure explains the shapes used.",
    "Where a figure shows a flow, arrows run from the sending party to the receiving party and the arrow label carries the detail.",
    "Colours distinguish legacy components, target components and external parties. The legend on each figure applies.",
    "The figures are exported from the team's drawing workspace at print resolution; zoom in for the smaller labels.",
    "Labels in the figures use the names in force on the document date. Earlier names are not shown.",
    "Boxes represent systems or roles, depending on the view; each figure's title states which.",
]

AUDIENCE = {
    "arch": ["architects and integration leads", "the Design Authority and delivery squads",
             "solution architects and service owners"],
    "ops": ["claim handlers and team leaders", "claims operations staff", "handlers, team leaders and trainers"],
    "data": ["data engineers, DBAs and analysts", "the data migration team and report developers"],
    "fin": ["the Reserving team and Finance stakeholders", "reserving analysts and actuarial colleagues"],
    "fraud": ["the Counter-Fraud & SIU team and Claims Hub squads", "fraud analysts and SIU investigators"],
    "vendor": ["supplier managers and claims assessment leads", "vendor management and claims operations"],
    "org": ["all Claims staff", "managers and HR business partners", "colleagues across the Claims function"],
}

FIGURE_INTRO = [
    "{fig} shows {what}.",
    "The view in {fig} covers {what}.",
    "{fig} illustrates {what}.",
    "{fig} below sets out {what}.",
    "See {fig} for {what}.",
    "{fig} gives the picture of {what}.",
]

FIGURE_TAIL = [
    "The labels in the figure are authoritative for this pack.",
    "Detail is carried in the figure labels rather than repeated here.",
    "Refer to the figure for the specific values.",
    "The figure is reproduced as exported; no values have been re-keyed into this text.",
    "Readers should rely on the figure itself for specifics.",
    "",
    "",
]

MAINTENANCE = [
    "Changes to this pack follow the normal document-control process. Raise suggestions with the document owner.",
    "The owner reviews the figures when the underlying design or process changes and re-issues the pack.",
    "Superseded versions are retained in the document library for audit purposes.",
    "Comments on the figures should be raised through the document owner rather than by editing the images.",
    "If a figure disagrees with a controlled procedure, the procedure takes precedence until the pack is corrected.",
]

SCOPE_IN = [
    "In scope: the views listed in the contents.",
    "The pack covers the views listed in the contents and nothing else.",
    "Only the views listed in the contents are covered.",
]

SCOPE_OUT = [
    "Out of scope: detailed procedures, test evidence and operational runbooks.",
    "Detailed procedures and runbooks are maintained separately and are not reproduced here.",
    "The pack does not replace procedures, specifications or runbooks.",
]

GLOSSARY_LEAD = [
    "The abbreviations below are used in the figure labels.",
    "Abbreviations used in the figures:",
    "The following terms appear in the figures.",
]


def pick(r: random.Random, bank: list[str], **kw) -> str:
    return r.choice(bank).format(**kw)


def fig_sentence(r: random.Random, fig: str, what: str) -> str:
    s = pick(r, FIGURE_INTRO, fig=fig, what=what)
    tail = r.choice(FIGURE_TAIL)
    return (s + " " + tail).strip()
