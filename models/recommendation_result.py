"""
Recommendation Result Model.
"""

from pydantic import BaseModel

from models.job import Job
from services.recommendation.models.signal_result import SignalResult


class RecommendationResult(BaseModel):
    """
    Final recommendation produced by the
    recommendation engine.
    """

    job: Job

    score: float

    signal_results: list[SignalResult]