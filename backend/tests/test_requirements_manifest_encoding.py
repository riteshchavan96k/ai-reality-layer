"""Ensure GitHub and dependency tooling can parse production requirements as UTF-8.

The manifest previously used UTF-16, causing GitHub's managed pip dependency
graph parser to fail. This test protects the encoding without freezing the
dependency choices or versions for future reviewed updates.
"""
from pathlib import Path
import re


MANIFEST = Path(__file__).resolve().parents[1] / "requirements.txt"


def test_production_requirements_are_plain_strict_utf8():
    raw = MANIFEST.read_bytes()
    assert raw, "Production dependency manifest must not be empty"
    assert not raw.startswith((b"\xff\xfe", b"\xfe\xff", b"\xef\xbb\xbf"))
    assert b"\x00" not in raw, "Manifest must be plain-text UTF-8"
    assert b"\r" not in raw, "Manifest must use normalized LF newlines"
    assert raw.endswith(b"\n")
    text = raw.decode("utf-8", errors="strict")
    assert not text.startswith("\ufeff")


def test_production_requirements_have_unambiguous_pinned_versions():
    text = MANIFEST.read_bytes().decode("utf-8", errors="strict")
    entries = text.splitlines()
    assert entries, "Production manifest must list dependencies"
    assert all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*==[A-Za-z0-9][A-Za-z0-9._+!-]*", line) for line in entries)
    names = [line.split("==", 1)[0].lower().replace("_", "-") for line in entries]
    assert len(names) == len(set(names)), "Avoid duplicate package pins"
