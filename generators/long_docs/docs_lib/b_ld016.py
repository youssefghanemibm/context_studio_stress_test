"""LD016 – BRD Fraud Referral Changes, APPROVED v1.0 (2026-03-12)."""
from .brd import build_brd


def build():
    return build_brd("LD016", draft=False)
