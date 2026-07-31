"""
Resume Formatter.

Converts a Resume model into text suitable for semantic embedding.
"""

from models.resume import Resume


class ResumeFormatter:
    """
    Converts Resume models into plain text.
    """

    def to_text(
        self,
        resume: Resume,
    ) -> str:
        parts = [resume.raw_text.strip()]

        if resume.skills:
            parts.append("Normalized skills: " + ", ".join(skill.name for skill in resume.skills))

        return "\n".join(parts)
