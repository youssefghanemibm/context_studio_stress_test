"""Match claims between CLARA and Claims Hub and classify differences."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Difference:
    claim_id: str
    kind: str            # MISSING_IN_HUB, MISSING_IN_CLARA, AMOUNT, CURRENCY
    clara_amount: Decimal | None
    hub_amount: Decimal | None


def to_hub_id(clara_id: str) -> str:
    """UK2025118204 -> CLM-UK-2025-118204."""
    return f"CLM-{clara_id[:2]}-{clara_id[2:6]}-{clara_id[6:]}"


def diff(clara, hub, tolerance):
    per_claim = tolerance.get("per_claim")
    if per_claim is None:
        raise ValueError("tolerance.per_claim must be set in the run configuration")
    per_claim = Decimal(str(per_claim))
    out = []
    hub_seen = set()
    for cid, (amount, ccy) in clara.items():
        hid = to_hub_id(cid)
        if hid not in hub:
            out.append(Difference(hid, "MISSING_IN_HUB", amount, None))
            continue
        hub_seen.add(hid)
        h_amount, h_ccy = hub[hid]
        if h_ccy != ccy:
            out.append(Difference(hid, "CURRENCY", amount, h_amount))
        elif abs(h_amount - amount) > per_claim:
            out.append(Difference(hid, "AMOUNT", amount, h_amount))
    for hid, (h_amount, _) in hub.items():
        if hid not in hub_seen:
            out.append(Difference(hid, "MISSING_IN_CLARA", None, h_amount))
    return out
