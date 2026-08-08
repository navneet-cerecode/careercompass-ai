"""Aggregate skill evidence from one user's resume and observed role history."""

from uuid import UUID

from database.repositories.applications import ApplicationRepository, SavedJobRepository
from database.repositories.job_discovery_tasks import JobDiscoveryTaskRepository
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.session import Database
from models.job import Job
from models.skill_intelligence import (
    SkillIntelligenceItem,
    SkillIntelligenceSnapshot,
    SkillRoleReference,
)


class SkillIntelligenceService:
    MAX_ROLES = 100
    MAX_GAPS = 30

    def __init__(self, database: Database) -> None:
        self.database = database

    def get(self, *, user_id: UUID) -> SkillIntelligenceSnapshot:
        with self.database.session() as session:
            resume = ResumeRepository(session).get_active(user_id=user_id)
            searched_ids = JobDiscoveryTaskRepository(session).list_user_job_ids(
                user_id=user_id,
                limit=self.MAX_ROLES,
            )
            saved_ids = tuple(
                saved.job_id for saved in SavedJobRepository(session).list(user_id=user_id)
            )
            application_ids = tuple(
                application.job_id
                for application in ApplicationRepository(session).list(user_id=user_id)
            )
            job_ids = self._unique_ids(application_ids + saved_ids + searched_ids)[
                : self.MAX_ROLES
            ]
            jobs = JobRepository(session).get_many(job_ids) if job_ids else ()
            if jobs is None:
                raise RuntimeError("Career history references a missing catalog entry.")
            return self._snapshot(
                resume=resume.resume if resume else None,
                jobs=jobs,
                searched_ids=searched_ids,
                saved_ids=saved_ids,
                application_ids=application_ids,
            )

    @classmethod
    def _snapshot(
        cls,
        *,
        resume,
        jobs: tuple[Job, ...],
        searched_ids: tuple[UUID, ...],
        saved_ids: tuple[UUID, ...],
        application_ids: tuple[UUID, ...],
    ) -> SkillIntelligenceSnapshot:
        resume_skills = {
            skill.name.casefold(): (skill.name, skill.category) for skill in resume.skills
        } if resume else {}
        observed: dict[str, dict[str, object]] = {}
        roles_with_skills = 0
        for job in jobs:
            unique_job_skills: set[str] = set()
            for skill in job.required_skills:
                key = skill.name.casefold()
                if key in unique_job_skills:
                    continue
                unique_job_skills.add(key)
                entry = observed.setdefault(
                    key,
                    {"name": skill.name, "category": skill.category, "roles": []},
                )
                entry["roles"].append(
                    SkillRoleReference(job_id=job.id, title=job.title, company=job.company)
                )
            if unique_job_skills:
                roles_with_skills += 1

        supported: list[SkillIntelligenceItem] = []
        gaps: list[SkillIntelligenceItem] = []
        resume_only: list[SkillIntelligenceItem] = []
        for key, entry in observed.items():
            roles = tuple(entry["roles"])
            resume_entry = resume_skills.get(key)
            item = SkillIntelligenceItem(
                name=resume_entry[0] if resume_entry else str(entry["name"]),
                category=resume_entry[1] if resume_entry else entry["category"],
                status="supported" if resume_entry else "develop",
                resume_evidenced=resume_entry is not None,
                observed_role_count=len(roles),
                observed_roles=roles[:3],
            )
            (supported if resume_entry else gaps).append(item)
        for key, (name, category) in resume_skills.items():
            if key not in observed:
                resume_only.append(
                    SkillIntelligenceItem(
                        name=name,
                        category=category,
                        status="resume_only",
                        resume_evidenced=True,
                        observed_role_count=0,
                    )
                )

        def by_demand(item: SkillIntelligenceItem) -> tuple[int, str]:
            return (-item.observed_role_count, item.name.casefold())
        skills = (
            sorted(supported, key=by_demand)
            + sorted(gaps, key=by_demand)[: cls.MAX_GAPS]
            + sorted(resume_only, key=lambda item: item.name.casefold())
        )
        analyzed_ids = {job.id for job in jobs}
        return SkillIntelligenceSnapshot(
            resume_id=resume.id if resume else None,
            roles_analyzed=len(jobs),
            roles_with_skill_data=roles_with_skills,
            roles_without_skill_data=len(jobs) - roles_with_skills,
            search_history_roles=len(analyzed_ids.intersection(searched_ids)),
            saved_roles=len(analyzed_ids.intersection(saved_ids)),
            application_roles=len(analyzed_ids.intersection(application_ids)),
            skills=tuple(skills),
        )

    @staticmethod
    def _unique_ids(values: tuple[UUID, ...]) -> tuple[UUID, ...]:
        return tuple(dict.fromkeys(values))
