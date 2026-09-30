from collections.abc import Mapping

from backend.app.evaluation.quality_recovery_contract import (
    QualityRecoveryResult,
)


class QualityRecoveryResultNormalizer:
    """Normalize quality-recovery outcomes through the canonical contract."""

    @staticmethod
    def normalize(raw_result: object) -> QualityRecoveryResult:
        if isinstance(raw_result, QualityRecoveryResult):
            return raw_result
        if isinstance(raw_result, Mapping):
            return QualityRecoveryResult.validate(dict(raw_result))
        raise ValueError(
            "quality recovery result must be a contract or mapping"
        )


__all__ = ["QualityRecoveryResultNormalizer"]
