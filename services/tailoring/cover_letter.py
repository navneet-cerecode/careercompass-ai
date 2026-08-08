"""Deterministic cover letter composition from verified resume evidence."""

from models.cover_letter import CoverLetterContent, CoverLetterEvidence
from models.job import Job
from models.resume import Resume
from models.tailoring import FactualTailoringPlan


class FactualCoverLetterComposer:
    """Create concise suggestions without adding candidate claims."""

    def compose(
        self,
        *,
        resume: Resume,
        job: Job,
        plan: FactualTailoringPlan,
    ) -> tuple[CoverLetterContent, tuple[CoverLetterEvidence, ...]]:
        evidence: list[CoverLetterEvidence] = []
        matched_skills = tuple(plan.matched_skills[:5])
        evidence.extend(
            CoverLetterEvidence(kind="skill", source_index=index, source_text=skill.name)
            for index, skill in enumerate(matched_skills)
        )

        experience = next(
            (item for item in plan.evidence if item.section == "experience"),
            None,
        )
        project = next((item for item in plan.evidence if item.section == "project"), None)
        if experience is None and resume.experience:
            experience_text = resume.experience[0]
            experience_index = 0
        else:
            experience_text = experience.source_text if experience else None
            experience_index = experience.source_index if experience else 0
        if project is None and resume.projects:
            project_text = resume.projects[0]
            project_index = 0
        else:
            project_text = project.source_text if project else None
            project_index = project.source_index if project else 0

        if experience_text:
            evidence.append(
                CoverLetterEvidence(
                    kind="experience",
                    source_index=experience_index,
                    source_text=experience_text,
                )
            )
        if project_text:
            evidence.append(
                CoverLetterEvidence(
                    kind="project",
                    source_index=project_index,
                    source_text=project_text,
                )
            )

        skill_text = self._natural_list(tuple(skill.name for skill in matched_skills))
        evidence_parts = []
        if skill_text:
            evidence_parts.append(f"My verified background includes {skill_text}.")
        if experience_text:
            evidence_parts.append(f"A relevant example from my resume is: {experience_text}")
        if not evidence_parts:
            evidence_parts.append(
                "I would welcome the opportunity to discuss the experience documented in my resume."
            )

        motivation = (
            f"A related project from my resume is: {project_text}"
            if project_text
            else "I am interested in learning more about the team's priorities for this role."
        )
        content = CoverLetterContent(
            candidate_name=resume.name,
            candidate_email=str(resume.email) if resume.email else None,
            company_name=job.company,
            job_title=job.title,
            salutation="Dear hiring team,",
            opening=f"I am applying for the {job.title} position at {job.company}.",
            evidence_paragraph=" ".join(evidence_parts),
            motivation_paragraph=motivation,
            closing_paragraph=(
                "Thank you for considering my application. I would welcome the opportunity "
                "to discuss how my verified experience relates to this position."
            ),
            sign_off="Sincerely,",
        )
        return content, tuple(evidence)

    @staticmethod
    def _natural_list(items: tuple[str, ...]) -> str:
        if len(items) < 2:
            return items[0] if items else ""
        if len(items) == 2:
            return " and ".join(items)
        return f"{', '.join(items[:-1])}, and {items[-1]}"
