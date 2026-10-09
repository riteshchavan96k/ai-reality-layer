"""Conservative text alignment of linked claims to an explicitly named entity.

This is NOT semantic task relevance or source authenticity. An entity mention
is necessary to establish this narrow form of alignment, but not sufficient
to establish factual support, entailment, or publisher trust.
"""

import re
from typing import Any

from backend.app.reality.reality_entity import RealityEntity


def explicit_entity_link_alignment(
    entity: RealityEntity | str | dict[str, Any],
    linking: dict[str, Any],
) -> bool:
    """Require all linked claim texts to mention the exact explicit entity.

    Fail closed for missing/malformed links. Full identifiers are compared
    with Unicode-aware case folding and whitespace normalization. Identifier
    boundaries exclude version prefixes and hyphenated/decimal suffixes:
    'Python 3.13' must not match 'Python 3.13.0'.
    """
    target = RealityEntity.validate(entity)
    if target.status != "specified" or not target.name:
        raise ValueError("entity alignment requires an explicitly specified entity")
    if not isinstance(linking, dict):
        raise ValueError("linking must be a dictionary")
    if linking.get("status") != "usable":
        return False

    raw_links = linking.get("links")
    if not isinstance(raw_links, list) or not raw_links:
        return False

    normalized_name = " ".join(target.name.split()).casefold()
    phrase = re.compile(r"(?<![\w.\-])" + re.escape(normalized_name) + r"(?![\w.\-])")
    for link in raw_links:
        if not isinstance(link, dict):
            return False
        text = link.get("claim_text")
        if not isinstance(text, str) or not text.strip():
            return False
        normalized_claim = " ".join(text.split()).casefold()
        if phrase.search(normalized_claim) is None:
            return False
    return True


__all__ = ["explicit_entity_link_alignment"]
