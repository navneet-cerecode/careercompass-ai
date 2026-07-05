"""
Fast skill matching engine.

Performs deterministic matching between
resume skills and job skills.
"""

from models.skill import Skill


class SkillMatcher:

    def match(
        self,
        resume_skills: list[Skill],
        job_skills: list[Skill],
    ):
        """
        Compare two skill lists.
        """

        resume_set = {
            skill.name.lower()
            for skill in resume_skills
        }

        matched = []

        missing = []

        for skill in job_skills:

            if skill.name.lower() in resume_set:

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

        return {
            "score": score,
            "matched": matched,
            "missing": missing,
        }