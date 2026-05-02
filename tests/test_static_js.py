"""Step 3: index.html static JS tests.

Tests parseTimeToSec logic (Python simulation) and verifies
the JS source contains expected patterns (inline regex checks).
"""
import re
from pathlib import Path

INDEX_HTML = Path(__file__).resolve().parent.parent / "app" / "static" / "index.html"


def _read_js():
    return INDEX_HTML.read_text(encoding="utf-8")


def _parse_time_to_sec(s: str) -> int | None:
    """Mirror the JS parseTimeToSec logic in Python."""
    s = s.strip()
    if not s or not re.match(r'^[\d:]+$', s):
        return None
    parts = s.split(":")
    if len(parts) > 3:
        return None
    for p in parts:
        if p == "" or not p.isdigit():
            return None
    nums = [int(p) for p in parts]
    if len(nums) == 1:
        return nums[0]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    return nums[0] * 3600 + nums[1] * 60 + nums[2]


def test_parse_time_hhmmss():
    assert _parse_time_to_sec("01:08:00") == 4080


def test_parse_time_mmss():
    assert _parse_time_to_sec("45:30") == 2730


def test_parse_time_seconds_only():
    assert _parse_time_to_sec("300") == 300


def test_js_contains_state_machine_and_poll():
    js = _read_js()
    assert 'screen: "form"' in js
    assert '"processing"' in js
    assert "setInterval" in js
    assert "parseTimeToSec" in js
    assert "/api/job/new" in js
    assert "/api/job/" in js
