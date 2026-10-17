"""Step253 narrow original-source Python release-date policy, NOT general QA.

Two independent bindings are necessary: an exact official release-page URL
derived from the requested version, and a unique visible page heading followed
by a unique release-date field. Neither source text nor a model response is
authorized to choose a different entity, source or attribute.
"""
from __future__ import annotations

from datetime import datetime, date
import re

ENTITY_PATTERN = re.compile(r"Python ([0-9]+)\.([0-9]+)\.([0-9]+)\Z")
RELEASE_DATE = re.compile(r"Release date: (.{6,35})\Z", re.IGNORECASE)
_ALLOWED_DATE_PATTERNS = ("%b. %d, %Y", "%b %d, %Y", "%B %d, %Y",
                          "%Y-%m-%d", "%b %d %Y", "%B %d %Y")


def expected_question(question: object, entity: object, source_uri: object) -> bool:
    if (
        type(question) is not str or type(entity) is not str
        or type(source_uri) is not str
        or not 0 < len(question) <= 200
        or not 0 < len(entity) <= 100
        or question != f"When was {entity} released?"
    ):
        return False
    match = ENTITY_PATTERN.fullmatch(entity)
    if match is None:
        return False
    major, minor, micro = map(int, match.groups())
    # Decimal URL concatenation is ambiguous without this restriction.
    if not (2 <= major <= 9 and 0 <= minor <= 99 and 0 <= micro <= 9):
        return False
    exact_url = f"https://www.python.org/downloads/release/python-{major}{minor}{micro}/"
    return source_uri == exact_url


def parse_date(value: object) -> date | None:
    """Finite whitelist of complete date formats; no guessy dateutil parser."""
    if type(value) is not str or not 6 <= len(value) <= 35:
        return None
    if value != value.strip() or any(x in value for x in "\r\n\x00"):
        return None
    for fmt in _ALLOWED_DATE_PATTERNS:
        try:
            result = datetime.strptime(value, fmt).date()
            if 1990 <= result.year <= 2100:
                return result
        except ValueError:
            continue
    return None


def parse_release_date_label(text: object) -> date | None:
    if type(text) is not str or text != text.strip() or len(text) > 80:
        return None
    match = RELEASE_DATE.fullmatch(text)
    return parse_date(match.group(1)) if match else None


def select_date_unit(content: object, entity: str) -> tuple[str, date] | None:
    """Check visible source document structural proximity, not mere substring.

    The existing pinned HTTPS reader strips hidden HTML and keeps block
    boundaries. This does not parse a full DOM or authenticate publisher
    authorship. An ambiguous document must abstain, even with a helpful LLM.
    """
    if type(content) is not str or len(content) > 50000:
        return None
    lines = [unit.strip() for unit in content.split("\n") if unit.strip()]
    if not 1 <= len(lines) <= 10000:
        return None
    headings = [i for i, line in enumerate(lines) if line == entity]
    dates = [(i, line, parse_release_date_label(line)) for i, line in enumerate(lines)
             if line.casefold().startswith("release date:")]
    if len(headings) != 1 or len(dates) != 1:
        return None
    h, (position, unit, date_value) = headings[0], dates[0]
    if date_value is None or not h < position <= h + 4 or len(unit) > 80:
        return None
    # If another Python-version heading intervenes, the date's owner is not
    # clear even if the requested heading occurs earlier.
    for line in lines[h+1:position]:
        if ENTITY_PATTERN.fullmatch(line) is not None:
            return None
    return unit, date_value


__all__ = [
    "expected_question", "parse_date", "parse_release_date_label", "select_date_unit",
]
