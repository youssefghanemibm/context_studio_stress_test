from decimal import Decimal

import pytest

from zz_reconcile.compare import diff, to_hub_id


def test_claim_id_mapping():
    assert to_hub_id("SE2026001234") == "CLM-SE-2026-001234"


def test_missing_and_amount_differences():
    clara = {"SE2026000001": (Decimal("100.00"), "SEK"), "SE2026000002": (Decimal("50.00"), "SEK")}
    hub = {"CLM-SE-2026-000001": (Decimal("100.00"), "SEK"), "CLM-SE-2026-000009": (Decimal("1.00"), "SEK")}
    kinds = sorted(d.kind for d in diff(clara, hub, {"per_claim": "0"}))
    assert kinds == ["MISSING_IN_CLARA", "MISSING_IN_HUB"]


def test_tolerance_must_be_configured():
    with pytest.raises(ValueError):
        diff({}, {}, {"per_claim": None})
