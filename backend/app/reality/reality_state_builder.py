from typing import Any

from backend.app.reality.reality_entity import RealityEntity
from backend.app.reality.reality_state import RealityState
from backend.app.reality.reality_state_normalizer import RealityStateNormalizer


class RealityStateBuilder:
    """Assemble a deterministic snapshot from already-computed reality signals."""

    def build_result(
        self,
        task: str,
        evidence: dict[str, Any],
        claims: dict[str, Any],
        linking: dict[str, Any],
        provenance: dict[str, Any],
        observation: dict[str, Any],
        freshness: dict[str, Any],
        conflicts: dict[str, Any],
        confidence: dict[str, Any],
        *,
        entity: object = None,
    ) -> RealityState:
        if not isinstance(confidence, dict):
            raise ValueError("confidence must be a dictionary")
        status = confidence.get("status")
        if status not in {"supported", "uncertain", "insufficient", "unavailable"}:
            raise ValueError("confidence status is invalid")
        reason = confidence.get("reason")
        return RealityStateNormalizer.normalize(
            RealityState(
                status,
                task,
                evidence,
                claims,
                linking,
                provenance,
                observation,
                freshness,
                conflicts,
                confidence,
                entity=RealityEntity.validate(entity),
                reason=reason,
            )
        )

    def build(
        self,
        task,
        evidence,
        claims,
        linking,
        provenance,
        observation,
        freshness,
        conflicts,
        confidence,
        entity=None,
    ):
        return self.build_result(
            task,
            evidence,
            claims,
            linking,
            provenance,
            observation,
            freshness,
            conflicts,
            confidence,
            entity=entity,
        ).to_dict()


__all__ = ["RealityStateBuilder"]
