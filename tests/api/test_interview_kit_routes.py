from api.dependencies import get_required_principal
from models.skill import Skill
from tests.api.test_application_routes import (
    make_authenticated_client,
    make_principal,
    review_application_packet,
)


def _submitted_application(client, job_id: str) -> str:
    application_id = client.post(
        "/api/v1/applications",
        json={"job_id": job_id},
    ).json()["id"]
    review_application_packet(client, application_id)
    assert client.post(f"/api/v1/applications/{application_id}/packet/ready").status_code == 200
    assert client.post(
        f"/api/v1/applications/{application_id}/packet/submitted",
        json={"confirm_external_submission": True},
    ).status_code == 200
    return application_id


def test_interview_kit_is_grounded_owner_scoped_and_does_not_change_status():
    application, client, database, owner, other, job, _, _ = make_authenticated_client()
    with database.session() as session:
        from database.models.jobs import JobRecord

        record = session.get(JobRecord, job.id)
        record.required_skills = [
            Skill(name="Python").model_dump(mode="json"),
            Skill(name="Stakeholder communication").model_dump(mode="json"),
        ]
    application_id = _submitted_application(client, str(job.id))

    created = client.post(f"/api/v1/applications/{application_id}/interview-kit")

    assert created.status_code == 201
    payload = created.json()
    assert payload["application_status"] == "Applied"
    assert payload["job"]["id"] == str(job.id)
    assert payload["resume_id"]
    assert {question["category"] for question in payload["questions"]} >= {
        "career_story",
        "skill_gap",
        "motivation",
        "behavioral",
    }
    assert all(question["evidence_prompts"] for question in payload["questions"])
    detail = client.get(f"/api/v1/applications/{application_id}").json()
    assert detail["status"] == "Applied"
    assert len(detail["events"]) == 3

    duplicate = client.post(f"/api/v1/applications/{application_id}/interview-kit")
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == payload["id"]

    application.dependency_overrides[get_required_principal] = lambda: make_principal(other)
    assert client.get(f"/api/v1/applications/{application_id}/interview-kit").status_code == 404
    application.dependency_overrides[get_required_principal] = lambda: make_principal(owner)


def test_interview_notes_require_known_questions_and_explicit_review():
    _, client, _, _, _, job, _, _ = make_authenticated_client()
    application_id = _submitted_application(client, str(job.id))
    kit = client.post(f"/api/v1/applications/{application_id}/interview-kit").json()
    question_id = kit["questions"][0]["id"]

    draft = client.patch(
        f"/api/v1/applications/{application_id}/interview-kit",
        json={"responses": {question_id: "A factual example from my experience."}},
    )
    assert draft.status_code == 200
    assert draft.json()["reviewed_at"] is None

    reviewed = client.patch(
        f"/api/v1/applications/{application_id}/interview-kit",
        json={
            "responses": {question_id: "A factual example from my experience."},
            "confirm_reviewed": True,
        },
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["reviewed_at"] is not None

    edited = client.patch(
        f"/api/v1/applications/{application_id}/interview-kit",
        json={"responses": {question_id: "A corrected factual example."}},
    )
    assert edited.status_code == 200
    assert edited.json()["reviewed_at"] is None

    invalid = client.patch(
        f"/api/v1/applications/{application_id}/interview-kit",
        json={"responses": {"invented-question": "No."}},
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "invalid_interview_response"


def test_interview_preparation_is_unavailable_before_submission():
    _, client, _, _, _, job, _, _ = make_authenticated_client()
    application_id = client.post(
        "/api/v1/applications",
        json={"job_id": str(job.id)},
    ).json()["id"]

    response = client.post(f"/api/v1/applications/{application_id}/interview-kit")

    assert response.status_code == 409
    assert response.json()["code"] == "interview_kit_unavailable"
