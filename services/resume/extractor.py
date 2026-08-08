"""
Resume Information Extractor.

Extracts structured information
from parsed resume text.
"""

import re

from models.resume import Resume
from models.skill import Skill


class ResumeExtractor:
    SKILL_SECTION_PATTERN = re.compile(
        r"^(?:skills|technical skills(?: and interests)?|core skills|key skills|"
        r"core competencies|competencies|areas of expertise|professional skills)"
        r"\s*:?\s*(.*)$",
        re.IGNORECASE,
    )
    SECTION_PATTERN = re.compile(
        r"^(?:summary|profile|objective|experience|employment|work history|education|"
        r"projects|technical skills(?: and interests)?|skills|certifications?|"
        r"licen[cs]es?|languages?|achievements?|references)\s*:?$",
        re.IGNORECASE,
    )
    CONTENT_SECTIONS = {
        "education": "education",
        "experience": "experience",
        "employment": "experience",
        "work history": "experience",
        "projects": "projects",
        "certification": "certifications",
        "certifications": "certifications",
        "license": "certifications",
        "licenses": "certifications",
        "licence": "certifications",
        "licences": "certifications",
        "achievement": "achievements",
        "achievements": "achievements",
    }
    BULLET_PREFIXES = ("•", "◦", "▪", "‣", "-")

    EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

    PHONE_REGEX = r"(\+?\d[\d\s\-]{8,15})"

    LINKEDIN_REGEX = r"(linkedin\.com/in/[^\s]+)"

    GITHUB_REGEX = r"(github\.com/[^\s]+)"

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

        sections = self._extract_content_sections(text)

        return Resume(
            name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github,
            skills=skills,
            education=sections["education"],
            experience=sections["experience"],
            projects=sections["projects"],
            certifications=sections["certifications"],
            achievements=sections["achievements"],
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

        return "https://" + match.group() if match else None

    def _extract_github(self, text):

        match = re.search(
            self.GITHUB_REGEX,
            text,
        )

        return "https://" + match.group() if match else None

    def _extract_skills(self, text):

        found = []

        lower = text.lower()

        for skill in self.COMMON_SKILLS:
            if skill.lower() in lower:
                found.append(Skill(name=skill))

        in_skill_section = False
        declared_lines: list[str] = []
        wrapped_bullet = False
        for line in text.splitlines():
            stripped = line.strip().strip("•◦▪‣-–—")
            heading = self.SKILL_SECTION_PATTERN.match(stripped)
            if heading:
                in_skill_section = True
                stripped = heading.group(1).strip()
            elif in_skill_section and self.SECTION_PATTERN.match(stripped):
                in_skill_section = False
                wrapped_bullet = False
                continue

            if not in_skill_section or not stripped:
                continue

            starts_bullet = line.lstrip().startswith(
                (*self.BULLET_PREFIXES, "•", "◦", "▪", "‣", "–", "—")
            )
            if ":" in stripped:
                _, stripped = stripped.split(":", 1)
            if wrapped_bullet and not starts_bullet:
                declared_lines[-1] = f"{declared_lines[-1]} {stripped}"
            else:
                declared_lines.append(stripped)
            wrapped_bullet = (starts_bullet or wrapped_bullet) and not stripped.endswith(
                (",", ";", "|")
            )

        for declared_line in declared_lines:
            for name in re.split(r"[,;|•]", declared_line):
                name = name.strip().strip(".•◦▪‣-–—")
                if name and len(name.split()) <= 8:
                    found.append(Skill(name=name, category="Declared capability"))

        return list({skill.name.casefold(): skill for skill in found}.values())

    def _extract_content_sections(self, text: str) -> dict[str, list[str]]:
        captured = {name: [] for name in set(self.CONTENT_SECTIONS.values())}
        current_section = None
        section_lines: list[str] = []

        def flush() -> None:
            if current_section is None:
                return
            captured[current_section].extend(
                self._group_section_lines(section_lines, section=current_section)
            )

        for raw_line in text.splitlines():
            line = raw_line.strip()
            normalized = line.rstrip(":").strip().casefold()
            section = self.CONTENT_SECTIONS.get(normalized)
            if section is not None:
                flush()
                current_section = section
                section_lines = []
                continue
            if self.SECTION_PATTERN.match(line):
                flush()
                current_section = None
                section_lines = []
                continue
            if current_section is not None and line:
                section_lines.append(line)
        flush()
        return captured

    def _group_section_lines(self, lines: list[str], *, section: str) -> list[str]:
        if section == "education":
            return [self._clean_resume_line(line) for line in lines if line.strip()]

        grouped: list[str] = []
        current = ""
        for line in lines:
            clean = self._clean_resume_line(line)
            if not clean:
                continue
            starts_item = line.lstrip().startswith(self.BULLET_PREFIXES)
            if starts_item and current:
                grouped.append(current)
                current = clean
            elif current:
                current = f"{current} {clean}"
            else:
                current = clean
        if current:
            grouped.append(current)
        return grouped

    @staticmethod
    def _clean_resume_line(line: str) -> str:
        clean = line.strip().lstrip("•◦▪‣-").strip()
        clean = re.sub(r"\[?\(cid:\d+\)\]?", "", clean)
        clean = clean.replace("[§]", "")
        return re.sub(r"\s+", " ", clean).strip()
