"""
File: agents/candidate_evaluation_agent.py

Description:
Dummy implementation of the Candidate Evaluation Agent.
"""

from agents.base_agent import BaseAgent
from graph.state import GraphState
from models.match import MatchResult
from models.skill import Skill


class CandidateEvaluationAgent(BaseAgent):
    """
    Evaluates the candidate against discovered jobs.
    """

    def run(self, state: GraphState) -> GraphState:

        if not state["jobs"]:
            return state

        result = MatchResult(
            job=state["jobs"][0],
            match_score=85.0,
            matched_skills=[
                Skill(name="Python"),
                Skill(name="SQL"),
            ],
            missing_skills=[
                Skill(name="Machine Learning"),
            ],
            recruiter_summary=(
                "Strong Python and SQL profile."
            ),
            recommendations=[
                "Learn Machine Learning.",
                "Build one ML project.",
            ],
        )

        state["match_results"] = [result]

        return state