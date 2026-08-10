"""Aggregate skill evidence from one user's resume and observed role history."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from database.repositories.applications import ApplicationRepository, SavedJobRepository
from database.repositories.job_discovery_tasks import JobDiscoveryTaskRepository
from database.repositories.jobs import JobRepository
from database.repositories.resumes import ResumeRepository
from database.session import Database
from models.job import Job
from models.skill_intelligence import (
    RoleCluster,
    RoleClusterBasis,
    RoleHistoryWindow,
    SkillIntelligenceItem,
    SkillIntelligenceSnapshot,
    SkillRoleReference,
)
from services.skills import canonical_skill_key


class SkillIntelligenceService:
    MAX_ROLES = 100
    MAX_GAPS = 30

    def __init__(self, database: Database) -> None:
        self.database = database

    def get(self, *, user_id: UUID) -> SkillIntelligenceSnapshot:
        with self.database.session() as session:
            resume = ResumeRepository(session).get_active(user_id=user_id)
            search_observations = JobDiscoveryTaskRepository(
                session
            ).list_user_job_observations(
                user_id=user_id,
                limit=self.MAX_ROLES,
            )
            saved_jobs = SavedJobRepository(session).list(user_id=user_id)
            applications = ApplicationRepository(session).list(user_id=user_id)
            searched_ids = tuple(item.job_id for item in search_observations)
            saved_ids = tuple(saved.job_id for saved in saved_jobs)
            application_ids = tuple(application.job_id for application in applications)
            job_ids = self._unique_ids(application_ids + saved_ids + searched_ids)[
                : self.MAX_ROLES
            ]
            jobs = JobRepository(session).get_many(job_ids) if job_ids else ()
            if jobs is None:
                raise RuntimeError("Career history references a missing catalog entry.")
            observation_windows: dict[UUID, tuple[datetime, datetime]] = {
                item.job_id: (item.first_observed_at, item.last_observed_at)
                for item in search_observations
            }
            cluster_hints: dict[UUID, tuple[str, RoleClusterBasis]] = {
                item.job_id: (item.role, "search_intent") for item in search_observations
            }
            for item in (*saved_jobs, *applications):
                first, last = observation_windows.get(
                    item.job_id,
                    (item.created_at, item.created_at),
                )
                observation_windows[item.job_id] = (
                    min(self._utc(first), self._utc(item.created_at)),
                    max(self._utc(last), self._utc(item.created_at)),
                )
            return self._snapshot(
                resume=resume.resume if resume else None,
                jobs=jobs,
                searched_ids=searched_ids,
                saved_ids=saved_ids,
                application_ids=application_ids,
                observation_windows=observation_windows,
                cluster_hints=cluster_hints,
                now=datetime.now(UTC),
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
        observation_windows: dict[UUID, tuple[datetime, datetime]],
        cluster_hints: dict[UUID, tuple[str, RoleClusterBasis]],
        now: datetime,
    ) -> SkillIntelligenceSnapshot:
        resume_skills: dict[str, tuple[str, str | None, str]] = {}
        if resume:
            for skill in resume.skills:
                resume_skills.setdefault(
                    canonical_skill_key(skill.name),
                    (skill.name, skill.category, cls._literal_key(skill.name)),
                )
        observed: dict[str, dict[str, object]] = {}
        roles_with_skills = 0
        for job in jobs:
            unique_job_skills: set[str] = set()
            for skill in job.required_skills:
                key = canonical_skill_key(skill.name)
                entry = observed.setdefault(
                    key,
                    {
                        "name": skill.name,
                        "category": skill.category,
                        "roles": [],
                        "terms": [],
                    },
                )
                terms = entry["terms"]
                if cls._literal_key(skill.name) not in {
                    cls._literal_key(term) for term in terms
                }:
                    terms.append(skill.name)
                if key in unique_job_skills:
                    continue
                unique_job_skills.add(key)
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
            terms = tuple(entry["terms"])
            resume_entry = resume_skills.get(key)
            match_confidence = None
            matched_terms: tuple[str, ...] = ()
            if resume_entry:
                match_confidence = (
                    "exact"
                    if resume_entry[2] in {cls._literal_key(term) for term in terms}
                    else "curated_high"
                )
                matched_terms = tuple(dict.fromkeys((resume_entry[0], *terms)))
            item = SkillIntelligenceItem(
                name=resume_entry[0] if resume_entry else str(entry["name"]),
                category=resume_entry[1] if resume_entry else entry["category"],
                status="supported" if resume_entry else "develop",
                resume_evidenced=resume_entry is not None,
                match_confidence=match_confidence,
                matched_terms=matched_terms,
                observed_role_count=len(roles),
                observed_roles=roles[:3],
            )
            (supported if resume_entry else gaps).append(item)
        for key, (name, category, _) in resume_skills.items():
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
            history_window=cls._history_window(
                jobs=jobs,
                observation_windows=observation_windows,
                now=now,
            ),
            role_clusters=cls._role_clusters(jobs=jobs, cluster_hints=cluster_hints),
            skills=tuple(skills),
        )

    @classmethod
    def _history_window(
        cls,
        *,
        jobs: tuple[Job, ...],
        observation_windows: dict[UUID, tuple[datetime, datetime]],
        now: datetime,
    ) -> RoleHistoryWindow:
        windows = [observation_windows[job.id] for job in jobs]
        if not windows:
            return RoleHistoryWindow()
        normalized = [(cls._utc(first), cls._utc(last)) for first, last in windows]
        recent_cutoff = now - timedelta(days=7)
        aging_cutoff = now - timedelta(days=30)
        latest = [last for _, last in normalized]
        return RoleHistoryWindow(
            first_observed_at=min(first for first, _ in normalized),
            last_observed_at=max(latest),
            observed_last_7_days=sum(item >= recent_cutoff for item in latest),
            observed_8_to_30_days=sum(aging_cutoff <= item < recent_cutoff for item in latest),
            observed_over_30_days=sum(item < aging_cutoff for item in latest),
        )

    @classmethod
    def _role_clusters(
        cls,
        *,
        jobs: tuple[Job, ...],
        cluster_hints: dict[UUID, tuple[str, RoleClusterBasis]],
    ) -> tuple[RoleCluster, ...]:
        clusters: dict[tuple[RoleClusterBasis, str], dict[str, object]] = {}
        for job in jobs:
            label, basis = cluster_hints.get(job.id, (job.title, "role_title"))
            key = (basis, cls._literal_key(label))
            cluster = clusters.setdefault(key, {"label": label, "roles": []})
            cluster["roles"].append(
                SkillRoleReference(job_id=job.id, title=job.title, company=job.company)
            )
        values = (
            RoleCluster(
                label=str(cluster["label"]),
                basis=basis,
                role_count=len(cluster["roles"]),
                roles=tuple(cluster["roles"][:3]),
            )
            for (basis, _), cluster in clusters.items()
        )
        return tuple(sorted(values, key=lambda item: (-item.role_count, item.label.casefold())))

    @staticmethod
    def _unique_ids(values: tuple[UUID, ...]) -> tuple[UUID, ...]:
        return tuple(dict.fromkeys(values))

    @staticmethod
    def _literal_key(value: str) -> str:
        return " ".join(value.strip().casefold().split())

    @staticmethod
    def _utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
