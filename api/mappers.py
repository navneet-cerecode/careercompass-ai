"""Explicit mappings from internal domain models to public API contracts."""

from api.schemas.common import SkillResponse
from api.schemas.jobs import JobResponse
from api.schemas.recommendations import (
    JobRecommendationResponse,
    MatchAssessmentResponse,
    ResumeRecommendationInput,
    ScoreComponentResponse,
)
from api.schemas.resumes import ParsedResumeResponse, ResumeResponse
from models.job import Job
from models.job_recommendation import JobRecommendation
from models.match_assessment import MatchAssessment
from models.resume import Resume
from models.score_component import ScoreComponent
from models.skill import Skill


def map_skill(skill: Skill) -> SkillResponse:
    return SkillResponse(name=skill.name, category=skill.category)


def map_job(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        required_skills=tuple(map_skill(skill) for skill in job.required_skills),
        experience_level=job.experience_level,
        employment_type=job.employment_type,
        source=job.source,
        source_name=job.source_name,
        external_id=job.external_id,
        source_url=job.source_url,
        url=job.url,
    )


def map_resume(resume: Resume) -> ResumeResponse:
    return ResumeResponse(
        id=resume.id,
        name=resume.name,
        email=resume.email,
        phone=resume.phone,
        linkedin=resume.linkedin,
        github=resume.github,
        education=tuple(resume.education),
        experience=tuple(resume.experience),
        projects=tuple(resume.projects),
        skills=tuple(map_skill(skill) for skill in resume.skills),
        certifications=tuple(resume.certifications),
        achievements=tuple(resume.achievements),
    )


def map_resume_input(value: ResumeRecommendationInput) -> Resume:
    return Resume(
        id=value.id,
        name=value.name,
        email=value.email,
        phone=value.phone,
        linkedin=value.linkedin,
        github=value.github,
        education=list(value.education),
        experience=list(value.experience),
        projects=list(value.projects),
        skills=[Skill(name=skill.name, category=skill.category) for skill in value.skills],
        certifications=list(value.certifications),
        achievements=list(value.achievements),
        raw_text=value.raw_text,
    )


def map_parsed_resume(resume: Resume) -> ParsedResumeResponse:
    return ParsedResumeResponse(
        resume=map_resume(resume),
        raw_text=resume.raw_text,
    )


def map_score_component(component: ScoreComponent) -> ScoreComponentResponse:
    return ScoreComponentResponse(
        name=component.name,
        score=component.score,
        explanation=component.explanation,
        matched_skills=tuple(map_skill(skill) for skill in component.matched_skills),
        missing_skills=tuple(map_skill(skill) for skill in component.missing_skills),
    )


def map_assessment(assessment: MatchAssessment) -> MatchAssessmentResponse:
    return MatchAssessmentResponse(
        id=assessment.id,
        job=map_job(assessment.job),
        score=assessment.score,
        components=tuple(map_score_component(item) for item in assessment.components),
        matched_skills=tuple(map_skill(skill) for skill in assessment.matched_skills),
        missing_skills=tuple(map_skill(skill) for skill in assessment.missing_skills),
        recruiter_summary=assessment.recruiter_summary,
        recommendations=tuple(assessment.recommendations),
        confidence=assessment.confidence,
        algorithm_version=assessment.algorithm_version,
    )


def map_recommendation(
    recommendation: JobRecommendation,
) -> JobRecommendationResponse:
    return JobRecommendationResponse(
        id=recommendation.id,
        assessment=map_assessment(recommendation.assessment),
        rank=recommendation.rank,
    )
