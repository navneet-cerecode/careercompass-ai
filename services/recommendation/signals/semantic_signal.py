"""
Semantic recommendation signal.

Uses sentence embeddings to compare
a resume with a job description.
"""

from sentence_transformers.util import cos_sim

from services.embeddings.embedding_service import (
    EmbeddingService,
)

from services.formatters.job_formatter import JobFormatter
from services.formatters.resume_formatter import ResumeFormatter

from models.score_component import ScoreComponent

from services.recommendation.signals.base_signal import (
    BaseSignal,
)


class SemanticSignal(BaseSignal):
    """
    Computes semantic similarity.
    """

    def __init__(self):

        self.embedding_service = EmbeddingService()

        self.resume_formatter = ResumeFormatter()

        self.job_formatter = JobFormatter()

    def evaluate(
        self,
        resume,
        job,
    ) -> ScoreComponent:

        resume_text = self.resume_formatter.to_text(resume)

        job_text = self.job_formatter.to_text(job)

        resume_embedding = self.embedding_service.encode(resume_text)

        job_embedding = self.embedding_service.encode(job_text)

        similarity = float(
            cos_sim(
                resume_embedding,
                job_embedding,
            )
        )

        score = max(
            0.0,
            min(
                similarity * 100,
                100.0,
            ),
        )

        return ScoreComponent(
            name="Semantic Signal",
            score=round(score, 2),
            explanation=f"Semantic similarity: {round(score, 2)}%",
        )
