from datetime import datetime, timezone
from typing import Any, Callable

from backend.app.reality.reality_entity import RealityEntity
from backend.app.reality.reality_state import RealityState
from backend.app.reality.reality_verification import RealityVerification
from backend.app.reality.reality_state_normalizer import RealityStateNormalizer


class RealityStateBuilder:
    """Assemble a deterministic snapshot from already-computed reality signals."""

    def __init__(
        self,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _build_verification(self) -> RealityVerification:
        now = self._clock()
        if not isinstance(now, datetime) or now.tzinfo is None:
            raise ValueError(
                "Reality State verification clock must return "
                "a timezone-aware datetime"
            )
        verified_at = (
            now.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
        return RealityVerification.completed(verified_at)

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
                verification=self._build_verification(),
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
