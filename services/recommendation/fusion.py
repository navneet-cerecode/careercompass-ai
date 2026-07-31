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

        if not signals:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for signal in signals:
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
