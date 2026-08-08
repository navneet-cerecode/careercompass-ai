"""Build a safe tailoring plan from existing resume evidence."""

import re

from models.job import Job
from models.resume import Resume
from models.skill import Skill
from models.tailoring import FactualTailoringPlan, TailoringEvidence

WORD = re.compile(r"[\w+#.-]+")
TITLE_STOP_WORDS = {"and", "for", "the", "with"}


class FactualTailoringService:
    """Prioritize existing facts without generating or rewriting claims."""

    def create_plan(self, resume: Resume, job: Job) -> FactualTailoringPlan:
        resume_skill_names = {skill.name.casefold() for skill in resume.skills}
        job_text = f"{job.title} {job.description}".casefold()
        matched_skills = tuple(
            skill
            for skill in resume.skills
            if skill.name.casefold() in job_text
            or skill.name.casefold()
            in {required.name.casefold() for required in job.required_skills}
        )
        matched_names = {skill.name.casefold() for skill in matched_skills}
        missing_skills = tuple(
            skill
            for skill in job.required_skills
            if skill.name.casefold() not in resume_skill_names
        )
        ordered_skills = tuple(
            sorted(
                resume.skills,
                key=lambda skill: skill.name.casefold() not in matched_names,
            )
        )
        target_terms = self._target_terms(job, matched_skills)
        experience, experience_evidence = self._prioritize(
            resume.experience,
            target_terms,
            "experience",
        )
        projects, project_evidence = self._prioritize(
            resume.projects,
            target_terms,
            "project",
        )

        return FactualTailoringPlan(
            source_resume_id=resume.id,
            job_id=job.id,
            skills=ordered_skills,
            experience=experience,
            projects=projects,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            evidence=experience_evidence + project_evidence,
        )

    @staticmethod
    def _target_terms(job: Job, matched_skills: tuple[Skill, ...]) -> tuple[str, ...]:
        terms = [skill.name.casefold() for skill in (*job.required_skills, *matched_skills)]
        terms.extend(
            token
            for token in WORD.findall(job.title.casefold())
            if len(token) > 2 and token not in TITLE_STOP_WORDS
        )
        return tuple(dict.fromkeys(terms))

    @staticmethod
    def _prioritize(
        items: list[str],
        target_terms: tuple[str, ...],
        section: str,
    ) -> tuple[tuple[str, ...], tuple[TailoringEvidence, ...]]:
        ranked = []
        evidence = []
        for index, item in enumerate(items):
            matched_terms = tuple(term for term in target_terms if term in item.casefold())
            ranked.append((len(matched_terms), index, item))
            if matched_terms:
                evidence.append(
                    TailoringEvidence(
                        section=section,
                        source_index=index,
                        source_text=item,
                        matched_terms=matched_terms,
                    )
                )
        ranked.sort(key=lambda value: (-value[0], value[1]))
        return tuple(value[2] for value in ranked), tuple(evidence)
