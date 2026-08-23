"""Outcomes are scored only after the full horizon they were given has
passed. Scoring a counterfactual early is how a bad decision looks good."""
from __future__ import annotations

from datetime import datetime, timedelta


def resolution_due(decision_ts: str, horizon_days: int, buffer_days: int,
                   now: datetime) -> bool:
    """True once `horizon_days + buffer_days` have elapsed since the decision."""
    decided = datetime.fromisoformat(decision_ts)
    return now >= decided + timedelta(days=horizon_days + buffer_days)
