from typing import Any


class AdaptiveRoutingOptimizer:
    """Rank candidate models using historical task-type outcome signals."""

    def __init__(self, min_samples: int = 2) -> None:
        if min_samples < 1:
            raise ValueError("min_samples must be at least 1")
        self.min_samples = min_samples

    def rank(
        self,
        task_type: str,
        candidates: list[str],
        memory: Any,
    ) -> dict:
        signals = memory.routing_signals(task_type)
        ranked = []
        explored = False

        for index, model in enumerate(candidates):
            stats = signals.get(model, {})
            samples = stats.get("executions", 0)
            success_rate = stats.get("success_rate", 0.0)
            average_score = stats.get("average_score")
            average_attempts = stats.get("average_attempts", 0.0)

            if samples < self.min_samples:
                explored = True
                confidence = "insufficient_data"
                score = 0.0
            else:
                confidence = "historical"
                quality = average_score if average_score is not None else success_rate
                score = (0.6 * success_rate) + (0.4 * quality) - (0.05 * average_attempts)

            ranked.append(
                {
                    "model": model,
                    "score": score,
                    "samples": samples,
                    "confidence": confidence,
                    "success_rate": success_rate,
                    "average_score": average_score,
                    "average_attempts": average_attempts,
                    "original_order": index,
                }
            )

        ranked.sort(key=lambda item: (-item["score"], item["original_order"]))
        for item in ranked:
            item.pop("original_order")

        return {
            "ranked_models": ranked,
            "selected_model": ranked[0]["model"] if ranked else None,
            "exploration": explored,
            "min_samples": self.min_samples,
        }
