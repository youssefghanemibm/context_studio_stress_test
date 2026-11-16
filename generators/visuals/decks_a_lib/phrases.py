"""rng-driven phrase banks for speaker notes and connective slide text.

None of these phrases states a world fact (no thresholds, owners, dates, system or table links);
facts are passed in by the deck modules and woven between the filler sentences.
"""
from __future__ import annotations

OPEN = [
    "This slide walks through {topic}.",
    "Use this page to explain {topic}.",
    "Here we look at {topic}.",
    "The purpose of this page is to set out {topic}.",
    "Start with the overall shape of {topic} before going into the detail.",
    "This is the reference view for {topic}.",
    "Frame {topic} briefly before taking questions.",
    "We now turn to {topic}.",
    "This page summarises {topic} for the audience.",
    "Open by reminding the room why {topic} matters.",
    "Spend a minute on {topic}; it underpins the next few slides.",
    "Talk the audience through {topic} at a high level.",
    "Introduce {topic} and point out how the page is laid out.",
    "A short one: {topic}.",
    "Set the context for {topic} first.",
]

READ = [
    "Each box is one activity and the arrows show the hand-offs.",
    "Read the page from left to right; the colours follow the legend used throughout the pack.",
    "The layout is deliberately simple so that it prints legibly on A4.",
    "The shapes are positioned to show sequence, not elapsed time.",
    "Labels on the arrows are the conditions or messages that drive each hand-off.",
    "Where something is not shown, it has not changed since the previous issue.",
    "The visual is the authoritative part of this page; the notes only add context.",
    "Point to each shape in turn rather than reading the labels aloud.",
    "The same notation is used on every process page in this pack.",
    "Rows group the work by who carries it out.",
    "The page is meant to be read together with the step catalogue at the back.",
    "Keep the explanation at the level of the picture; detail sits in the appendix.",
]

CAVEAT = [
    "Detailed procedures remain in the controlled process documentation; this deck is a summary.",
    "If anything here conflicts with an approved rule, the rule register takes precedence.",
    "Content is as at the document date and is not updated automatically.",
    "Questions on interpretation should go to the document owner.",
    "Local desk instructions may add detail but must not contradict this view.",
    "This is a controlled document; printed copies are uncontrolled.",
    "Changes go through the normal document change process.",
    "Treat the page as a snapshot; check the change log before relying on it.",
    "The appendix lists the source documents used to build this page.",
    "Nothing on this page replaces the approved policy wording.",
    "Terminology follows the programme glossary at the end of the pack.",
    "Where the systems differ during migration, the notes call it out.",
]

CLOSE = [
    "Pause here for questions before moving on.",
    "Check the room for local variations before moving on.",
    "Invite comments; anything material goes on the change log.",
    "Move on once the audience is comfortable with the flow.",
    "Note any follow-ups in the action log.",
    "Keep to time here; the detail is in the appendix.",
    "Hand over to the next speaker if the session is shared.",
    "Ask whether anything on the page looks out of date.",
    "Close the section and take any parking-lot items.",
    "Confirm everyone can see the full diagram before continuing.",
]

HISTORY_DRAFT = [
    "Initial draft for working-group review",
    "First draft circulated to contributors",
    "Outline and first content pages",
    "Working draft for walkthrough",
]
HISTORY_REVIEW = [
    "Review comments incorporated",
    "Updated after stakeholder walkthrough",
    "Comments from the review cycle addressed",
    "Revised following quality review",
    "Minor corrections and layout changes",
]
HISTORY_FINAL = {
    "approved": ["Approved for issue", "Approved and baselined", "Issued as approved version"],
    "final": ["Final version for circulation", "Final issue", "Issued as final"],
    "stale": ["Approved for issue", "Approved and published"],
}

TAKEAWAY_HEAD = ["Key points", "What to take away", "In short", "Summary", "Highlights", "At a glance"]


def pick(rng, bank):
    return bank[rng.randrange(len(bank))]


def notes(rng, topic: str, facts: list[str] | None = None, n_filler: int = 2) -> str:
    """Speaker notes: an opener, the given fact sentences, filler and a close."""
    parts = [pick(rng, OPEN).format(topic=topic)]
    if facts:
        parts.extend(facts)
    banks = [READ, CAVEAT]
    rng.shuffle(banks)
    for b in banks[:n_filler]:
        parts.append(pick(rng, b))
    parts.append(pick(rng, CLOSE))
    return "\n".join(parts)
