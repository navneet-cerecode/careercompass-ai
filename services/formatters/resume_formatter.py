"""
Resume Formatter.

Converts a Resume model into text suitable
for semantic embedding.
"""


class ResumeFormatter:
    """
    Converts Resume models into plain text.
    """

    def to_text(
        self,
        resume,
    ) -> str:

        parts = []

        # -----------------------------
        # Skills
        # -----------------------------

        if getattr(resume, "skills", None):

            parts.append("Skills:")

            parts.extend(

                skill.name

                for skill in resume.skills

            )

        # -----------------------------
        # Experience
        # -----------------------------

        if getattr(resume, "experience", None):

            parts.append("Experience:")

            for exp in resume.experience:

                if getattr(exp, "title", None):

                    parts.append(exp.title)

                if getattr(exp, "company", None):

                    parts.append(exp.company)

                if getattr(exp, "description", None):

                    parts.append(exp.description)

        # -----------------------------
        # Projects
        # -----------------------------

        if getattr(resume, "projects", None):

            parts.append("Projects:")

            for project in resume.projects:

                if getattr(project, "title", None):

                    parts.append(project.title)

                if getattr(project, "description", None):

                    parts.append(project.description)

        return "\n".join(parts)