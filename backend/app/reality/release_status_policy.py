"""Step254: single official Python release-kind assertion, not current support status."""
from __future__ import annotations
import re
from backend.app.reality.release_date_policy import expected_question

_RELEASE_CLAIM = re.compile(r"This is the ([A-Za-z][A-Za-z -]{0,40}) release of (Python [0-9]+\.[0-9]+\.[0-9]+)\Z", re.I)


def status_question_valid(question: object, entity: object, url: object) -> bool:
    return (
        type(question) is str and type(entity) is str and type(url) is str
        and question == f"What type of release was {entity}?"
        and expected_question(f"When was {entity} released?", entity, url)
    )


def select_release_type_unit(content: object, entity: str) -> str | None:
    """Only one positive standalone stable declaration near unique page heading.

    Other type assertions, repetitions, quotation boundaries and ambiguity
    refuse support. A stable *release type* is not current support status.
    """
    if type(content) is not str or not 0 < len(content) <= 50_000:
        return None
    lines=[part.strip() for part in content.split("\n") if part.strip()]
    headings=[n for n,s in enumerate(lines) if s==entity]
    if len(headings)!=1:
        return None
    matches=[(n,s,_RELEASE_CLAIM.fullmatch(s)) for n,s in enumerate(lines)
             if s.casefold().startswith("this is the ") and " release of " in s.casefold()]
    # Claim once on the page, not an assertion buried in unrelated paragraphs.
    if len(matches)!=1:
        return None
    position,text,match=matches[0]
    if match is None or match.group(1).casefold()!="stable" or match.group(2)!=entity:
        return None
    if not (headings[0]<position<=headings[0]+5) or len(text)>80:
        return None
    for other in lines[headings[0]+1:position]:
        if other.startswith("Python ") and re.fullmatch(r"Python \d+\.\d+\.\d+",other):
            return None
    return text


def normalize_model_release_type(value: object) -> str | None:
    if type(value) is not str or value!=value.strip() or len(value)>32:
        return None
    return "stable" if value.casefold() in ("stable","stable release") else None


__all__=["status_question_valid","select_release_type_unit","normalize_model_release_type"]
