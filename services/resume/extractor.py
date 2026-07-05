"""
Resume Information Extractor.

Extracts structured information
from parsed resume text.
"""

import re

from models.resume import Resume
from models.skill import Skill


class ResumeExtractor:

    EMAIL_REGEX = (
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    )

    PHONE_REGEX = (
        r"(\+?\d[\d\s\-]{8,15})"
    )

    LINKEDIN_REGEX = (
        r"(linkedin\.com/in/[^\s]+)"
    )

    GITHUB_REGEX = (
        r"(github\.com/[^\s]+)"
    )

    COMMON_SKILLS = [

        "Python",
        "SQL",
        "C++",
        "JavaScript",

        "PyTorch",
        "TensorFlow",
        "Keras",

        "NumPy",
        "Pandas",

        "Scikit-learn",

        "OpenCV",

        "React.js",
        "Node.js",

        "MongoDB",
        "MySQL",

        "Machine Learning",
        "Deep Learning",

        "Computer Vision",

        "Natural Language Processing",

        "LangChain",

        "Git",
        "GitHub",

        "Docker",
        "Spark",

        "Airflow",

    ]

    def extract(
        self,
        text: str,
    ) -> Resume:

        email = self._extract_email(text)

        phone = self._extract_phone(text)

        linkedin = self._extract_linkedin(text)

        github = self._extract_github(text)

        name = self._extract_name(text)

        skills = self._extract_skills(text)

        return Resume(

            name=name,

            email=email,

            phone=phone,

            linkedin=linkedin,

            github=github,

            skills=skills,

            raw_text=text,
        )

    def _extract_name(self, text):

        return text.split("\n")[0].strip()

    def _extract_email(self, text):

        match = re.search(
            self.EMAIL_REGEX,
            text,
        )

        return match.group() if match else None

    def _extract_phone(self, text):

        match = re.search(
            self.PHONE_REGEX,
            text,
        )

        return match.group() if match else None

    def _extract_linkedin(self, text):

        match = re.search(
            self.LINKEDIN_REGEX,
            text,
        )

        return (
            "https://" + match.group()
            if match
            else None
        )

    def _extract_github(self, text):

        match = re.search(
            self.GITHUB_REGEX,
            text,
        )

        return (
            "https://" + match.group()
            if match
            else None
        )

    def _extract_skills(self, text):

        found = []

        lower = text.lower()

        for skill in self.COMMON_SKILLS:

            if skill.lower() in lower:

                found.append(
                    Skill(name=skill)
                )

        return found