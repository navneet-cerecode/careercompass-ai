"""
Recommendation Engine.

Runs every recommendation signal and
produces a ranked job recommendation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from models.match_assessment import MatchAssessment
from models.score_component import ScoreComponent
from models.skill import Skill

from services.recommendation.fusion import ScoreFusion
from services.skills.taxonomy import canonical_skill_key

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

        matched_skills = self._unique_skills(matched_skills)
        matched_keys = {canonical_skill_key(skill.name) for skill in matched_skills}
        missing_skills = [
            skill
            for skill in self._unique_skills(missing_skills)
            if canonical_skill_key(skill.name) not in matched_keys
        ]
        score = self.fusion.combine(signal_results)
        confidence = self.fusion.evidence_coverage(signal_results)

        return MatchAssessment(
            job=job,
            score=score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            components=signal_results,
            recruiter_summary=self._summary(
                matched_skills,
                missing_skills,
                confidence,
            ),
            recommendations=self._recommendations(signal_results, missing_skills),
            confidence=confidence,
            algorithm_version="hybrid-v2",
        )

    @staticmethod
    def _unique_skills(skills: list[Skill]) -> list[Skill]:
        unique = {}
        for skill in skills:
            unique.setdefault(canonical_skill_key(skill.name), skill)
        return list(unique.values())

    @staticmethod
    def _summary(
        matched_skills: list[Skill],
        missing_skills: list[Skill],
        confidence: float,
    ) -> str:
        if confidence < 1:
            return (
                "This score relies on role-description similarity because structured skill "
                "evidence was incomplete."
            )
        total_skills = len(matched_skills) + len(missing_skills)
        if total_skills == 0:
            return "The available signals found no structured skill evidence to compare."
        if not missing_skills:
            return f"The reviewed resume supports all {total_skills} listed skills."
        missing_count = len(missing_skills)
        return (
            f"The reviewed resume supports {len(matched_skills)} of {total_skills} listed skills; "
            f"{missing_count} still {'needs' if missing_count == 1 else 'need'} evidence."
        )

    @staticmethod
    def _recommendations(
        components: list[ScoreComponent],
        missing_skills: list[Skill],
    ) -> list[str]:
        if any(not component.evidence_available for component in components):
            return [
                "Review the original job description because this source did not provide "
                "structured skill requirements."
            ]
        return [
            f"Verify whether your experience demonstrates {skill.name}; only add it to "
            "application materials if factual."
            for skill in missing_skills[:3]
        ]
