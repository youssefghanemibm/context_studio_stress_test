"""LD015 – BRD Fraud Referral Changes, DRAFT v0.3 (2026-02-10)."""
from .brd import build_brd


def build():
    return build_brd("LD015", draft=True)
