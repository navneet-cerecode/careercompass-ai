"""
Recommendation Engine.

Runs every recommendation signal and
produces a ranked job recommendation.
"""

from models.job_recommendation import JobRecommendation

from services.recommendation.fusion import ScoreFusion

from services.recommendation.signals.skill_signal import (
    SkillSignal,
)

from services.recommendation.signals.semantic_signal import (
    SemanticSignal,
)


class RecommendationEngine:
    """
    Main recommendation engine.
    """

    def __init__(self):

        self.signals = [

            SkillSignal(),

            SemanticSignal(),

        ]

        self.fusion = ScoreFusion()

    def evaluate(
        self,
        resume,
        job,
    ) -> JobRecommendation:

        signal_results = []

        matched_skills = []

        missing_skills = []

        for signal in self.signals:

            result = signal.evaluate(
                resume,
                job,
            )

            signal_results.append(result)

            matched_skills.extend(
                result.matched_skills
            )

            missing_skills.extend(
                result.missing_skills
            )

        score = self.fusion.combine(
            signal_results
        )

        return JobRecommendation(

            job=job,

            score=score,

            matched_skills=matched_skills,

            missing_skills=missing_skills,

            signal_results=signal_results,

        )