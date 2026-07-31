"""
Recommendation Engine.

Runs every recommendation signal and
produces a ranked job recommendation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from models.match_assessment import MatchAssessment

from services.recommendation.fusion import ScoreFusion

if TYPE_CHECKING:
    from services.recommendation.signals.base_signal import BaseSignal


class RecommendationEngine:
    """
    Main recommendation engine.
    """

    def __init__(
        self,
        signals: list[BaseSignal] | None = None,
    ):

        if signals is None:
            from services.recommendation.signals.semantic_signal import SemanticSignal
            from services.recommendation.signals.skill_signal import SkillSignal

            signals = [
                SkillSignal(),
                SemanticSignal(),
            ]

        self.signals = signals

        self.fusion = ScoreFusion()

    def evaluate(
        self,
        resume,
        job,
    ) -> MatchAssessment:

        signal_results = []

        matched_skills = []

        missing_skills = []

        for signal in self.signals:
            result = signal.evaluate(
                resume,
                job,
            )

            signal_results.append(result)

            matched_skills.extend(result.matched_skills)

            missing_skills.extend(result.missing_skills)

        score = self.fusion.combine(signal_results)

        return MatchAssessment(
            job=job,
            score=score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            components=signal_results,
            algorithm_version="hybrid-v1",
        )
