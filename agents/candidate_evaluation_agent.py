"""
File: agents/candidate_evaluation_agent.py

Description:
Resume-aware candidate evaluation agent.
"""

from agents.base_agent import BaseAgent
from graph.state import GraphState
from services.recommendation.recommendation_service import RecommendationService


class CandidateEvaluationAgent(BaseAgent):
    """Evaluate a resume against every discovered job."""

    def __init__(
        self,
        recommendation_service: RecommendationService | None = None,
    ):
        self.recommendation_service = recommendation_service

    def run(self, state: GraphState) -> GraphState:
        resume = state.get("resume")
        jobs = state.get("jobs", [])

        if resume is None or not jobs:
            state["match_results"] = []
            return state

        if self.recommendation_service is None:
            self.recommendation_service = RecommendationService()

        state["match_results"] = self.recommendation_service.assess_jobs(
            resume,
            jobs,
        )

        return state
