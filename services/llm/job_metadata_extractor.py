"""
Job Metadata Extractor.

Uses Groq to extract structured metadata
from an unstructured job description.
"""

from models.skill import Skill

from services.llm.groq_client import GroqClient


class JobMetadataExtractor:
    """
    Extracts structured metadata from
    a job description.
    """

    def __init__(self):

        self.llm = GroqClient()

    def extract(
        self,
        description: str,
    ) -> dict:

        if not description.strip():

            return {
                "skills": [],
                "experience": None,
                "salary": None,
                "remote": False,
            }

        prompt = f"""
You are an expert technical recruiter.

Read the following job description.

Extract:

1. Technical skills only
2. Required experience
3. Salary if mentioned
4. Whether the job is remote

Ignore:
- communication
- teamwork
- leadership
- education
- benefits

Return ONLY JSON.

Example:

{{
    "skills":[
        "Python",
        "PyTorch",
        "Docker",
        "SQL"
    ],

    "experience":"3-5 years",

    "salary":"18-25 LPA",

    "remote":false
}}

Job Description

{description}
"""

        result = self.llm.chat(
            prompt
        )

        skills = [

            Skill(
                name=name,
            )

            for name in result.get(
                "skills",
                [],
            )

        ]

        return {

            "skills": skills,

            "experience": result.get(
                "experience"
            ),

            "salary": result.get(
                "salary"
            ),

            "remote": result.get(
                "remote",
                False,
            ),

        }