"""
Skill recommendation signal.

Evaluates how well the candidate's skills
match the required job skills.
"""

from services.recommendation.models.signal_result import SignalResult
from services.recommendation.signals.base_signal import BaseSignal


class SkillSignal(BaseSignal):
    """
    Computes a skill-based recommendation score.
    """

    def evaluate(
        self,
        resume,
        job,
    ) -> SignalResult:

        resume_skills = {
            skill.name.lower()
            for skill in resume.skills
        }

        job_skills = job.required_skills

        matched = []

        missing = []

        for skill in job_skills:

            if skill.name.lower() in resume_skills:

                matched.append(skill)

            else:

                missing.append(skill)

        if len(job_skills) == 0:

            score = 50.0

        else:

            score = (
                len(matched)
                / len(job_skills)
            ) * 100

        reason = (
            f"Matched {len(matched)} "
            f"out of {len(job_skills)} required skills."
        )

        return SignalResult(
            signal_name="Skill Signal",
            score=score,
            reason=reason,
            matched_skills=matched,
            missing_skills=missing,
        )