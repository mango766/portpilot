"""Tests for the prober module (title extraction is pure)."""

from __future__ import annotations

from portpilot.prober import _extract_title


def test_extract_title_basic() -> None:
    body = b"<html><head><title>Hello World</title></head></html>"
    assert _extract_title(body) == "Hello World"


def test_extract_title_with_attributes_and_whitespace() -> None:
    body = b"<title  data-x='1'>\n  My  App  \n</title>"
    assert _extract_title(body) == "My App"


def test_extract_title_missing() -> None:
    assert _extract_title(b"<html><body>nope</body></html>") == ""
