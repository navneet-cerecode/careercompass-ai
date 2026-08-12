"""
Skill recommendation signal.

Evaluates how well the candidate's skills
match the required job skills.
"""

from models.score_component import ScoreComponent
from services.recommendation.signals.base_signal import BaseSignal
from services.skills.taxonomy import canonical_skill_key


class SkillSignal(BaseSignal):
    """
    Computes a skill-based recommendation score.
    """

    def evaluate(
        self,
        resume,
        job,
    ) -> ScoreComponent:

        resume_skills = {canonical_skill_key(skill.name) for skill in resume.skills}

        job_skills = job.required_skills

        matched = []

        missing = []

        for skill in job_skills:
            if canonical_skill_key(skill.name) in resume_skills:
                matched.append(skill)

            else:
                missing.append(skill)

        if len(job_skills) == 0:
            score = 50.0
            reason = (
                "This source did not provide structured skill requirements, "
                "so skill evidence was not scored."
            )

        else:
            score = (len(matched) / len(job_skills)) * 100
            reason = f"Matched {len(matched)} out of {len(job_skills)} required skills."

        return ScoreComponent(
            name="Skill Signal",
            score=score,
            explanation=reason,
            evidence_available=bool(job_skills),
            matched_skills=matched,
            missing_skills=missing,
        )
