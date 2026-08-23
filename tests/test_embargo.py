from datetime import datetime, timezone

from preregister.embargo import resolution_due

TS = "2026-01-01T00:00:00+00:00"


def test_resolution_waits_for_horizon_plus_buffer() -> None:
    assert not resolution_due(TS, 5, 2, datetime(2026, 1, 7, 23, tzinfo=timezone.utc))
    assert resolution_due(TS, 5, 2, datetime(2026, 1, 8, tzinfo=timezone.utc))
