"""Extract job-relevant capabilities from a job description through Groq."""

from services.llm.groq_client import GroqClient


class JobSkillExtractor:
    """
    Extracts capabilities from a job description.
    """

    def __init__(self, client: GroqClient | None = None) -> None:
        self.client = client or GroqClient()

    def extract(
        self,
        description: str,
    ) -> list[str]:
        if not description.strip():
            return []

        prompt = f"""
You are an expert recruiter across technical and non-technical occupations.

Extract concise, job-relevant capabilities and explicit qualifications from the
following job description. Include occupational knowledge, tools, methods,
certifications, licences, languages, and interpersonal capabilities only when
the employer explicitly requires them.

Ignore:
- years of experience
- locations
- benefits
- generic company marketing

Return ONLY valid JSON.

Example:

{{
    "skills": [
        "Patient assessment",
        "CPR certification",
        "Electronic health records",
        "English"
    ]
}}

Job Description:

{description}
"""

        data = self.client.chat(prompt)
        skills = data.get("skills", [])
        if not isinstance(skills, list):
            return []
        return [skill.strip() for skill in skills if isinstance(skill, str) and skill.strip()]
