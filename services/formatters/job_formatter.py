"""
Job Formatter.

Converts a Job model into text suitable
for semantic embedding.
"""


class JobFormatter:
    """
    Converts Job models into plain text.
    """

    def to_text(
        self,
        job,
    ) -> str:

        parts = [

            job.title,

            job.company,

            job.location,

            job.description,

        ]

        if job.required_skills:

            parts.append("Required Skills:")

            parts.extend(

                skill.name

                for skill in job.required_skills

            )

        return "\n".join(parts)