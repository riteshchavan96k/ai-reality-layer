import re
from typing import Any


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "with",
}


def _terms(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOP_WORDS and len(token) > 1
    }


def evaluate_relevance(task: str, response_text: str) -> dict[str, Any]:
    """Estimate task-response lexical relevance without claiming factual correctness."""
    task_terms = _terms(task)
    response_terms = _terms(response_text)
    matched_terms = sorted(task_terms & response_terms)

    if not task_terms:
        score = 1.0 if response_terms else 0.0
    else:
        score = len(matched_terms) / len(task_terms)

    return {
        "score": score,
        "status": "pass" if score >= 0.5 else "review",
        "task_terms": sorted(task_terms),
        "matched_terms": matched_terms,
        "coverage": score,
        "limitation": "Reference-free lexical relevance only; this does not establish factual or semantic correctness.",
    }
