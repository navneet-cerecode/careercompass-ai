"""Extract technical skills from a job description through Groq."""

from services.llm.groq_client import GroqClient


class JobSkillExtractor:
    """
    Extracts technical skills from
    a job description.
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
You are an expert technical recruiter.

Extract ONLY technical skills from the following job description.

Ignore:
- years of experience
- soft skills
- communication
- leadership
- education
- locations

Return ONLY valid JSON.

Example:

{{
    "skills": [
        "Python",
        "PyTorch",
        "Docker",
        "SQL"
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
