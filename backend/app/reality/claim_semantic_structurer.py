"""Optional semantic-structuring boundary for candidate evidence claims.

The default deliberately does not infer semantic parts. A future trusted
implementation may be injected without coupling the extractor to any provider.
"""

from collections.abc import Mapping
from typing import Any, Protocol

from backend.app.reality.claim_semantic_structure import ClaimSemanticStructure


class ClaimSemanticStructurer(Protocol):
    """A trusted adapter that proposes semantics for an attributed claim."""

    def structure(
        self, claim_text: str, source_refs: tuple[str, ...]
    ) -> ClaimSemanticStructure | Mapping[str, Any] | None:
        """Return semantics, an explicit unstructured state, or no result."""
        ...


class NotAttemptedClaimSemanticStructurer:
    """Honest default: no semantic inference or model execution."""

    def structure(
        self, claim_text: str, source_refs: tuple[str, ...]
    ) -> ClaimSemanticStructure:
        return ClaimSemanticStructure.unstructured()


class ClaimSemanticStructuringStage:
    """Validate adapter output and never turn adapter failure into a fact."""

    def __init__(self, structurer: ClaimSemanticStructurer | None = None) -> None:
        self._structurer = (
            structurer if structurer is not None
            else NotAttemptedClaimSemanticStructurer()
        )
        if not callable(getattr(self._structurer, "structure", None)):
            raise ValueError("semantic structurer must expose a callable structure method")

    def structure_claim(
        self, claim_text: str, source_refs: tuple[str, ...]
    ) -> ClaimSemanticStructure:
        if not isinstance(claim_text, str) or not claim_text.strip():
            raise ValueError("semantic structuring requires non-empty claim text")
        if not isinstance(source_refs, tuple) or not source_refs or any(
            not isinstance(ref, str) or not ref.strip() for ref in source_refs
        ):
            raise ValueError("semantic structuring requires valid source references")

        try:
            proposed = self._structurer.structure(claim_text, source_refs)
            if proposed is None:
                return ClaimSemanticStructure.unstructured(
                    "semantic_structuring_no_result"
                )
            return ClaimSemanticStructure.validate(proposed)
        except Exception:
            # A failing or malformed optional adapter must not fabricate semantic
            # certainty or remove the original claim/source attribution.
            return ClaimSemanticStructure.unstructured(
                "semantic_structuring_failed"
            )


__all__ = [
    "ClaimSemanticStructurer",
    "NotAttemptedClaimSemanticStructurer",
    "ClaimSemanticStructuringStage",
]
