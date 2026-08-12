"""
Score Fusion Engine.

Combines multiple recommendation signals
into one final recommendation score.
"""

from models.score_component import ScoreComponent


class ScoreFusion:
    """
    Combines weighted recommendation signals.
    """

    DEFAULT_WEIGHTS = {
        "Skill Signal": 0.4,
        "Semantic Signal": 0.6,
    }

    def combine(
        self,
        signals: list[ScoreComponent],
    ) -> float:
        """
        Compute the weighted average score.
        """

        available_signals = [signal for signal in signals if signal.evidence_available]
        if not available_signals:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for signal in available_signals:
            weight = self.DEFAULT_WEIGHTS.get(
                signal.name,
                1.0,
            )

            weighted_sum += signal.score * weight

            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(
            weighted_sum / total_weight,
            2,
        )

    def evidence_coverage(self, signals: list[ScoreComponent]) -> float:
        """Return the share of configured signal weight backed by evidence."""
        expected_weight = sum(self.DEFAULT_WEIGHTS.values())
        if expected_weight == 0:
            return 0.0
        available_weight = sum(
            self.DEFAULT_WEIGHTS.get(signal.name, 1.0)
            for signal in signals
            if signal.evidence_available
        )
        return round(min(available_weight / expected_weight, 1.0), 2)
