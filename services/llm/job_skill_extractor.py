"""
Job Skill Extractor.

Uses Groq to extract technical skills
from a job description.
"""

import json



class JobSkillExtractor:
    """
    Extracts technical skills from
    a job description.
    """

    def __init__(self):

        self.llm = get_llm()

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

        response = self.llm.invoke(
            prompt
        )

        try:

            data = json.loads(
                response.content
            )

            return data.get(
                "skills",
                [],
            )

        except Exception:

            return []