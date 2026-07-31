"""
File: graph/nodes.py

Description:
LangGraph nodes that delegate work to agents.
"""

from functools import lru_cache

from agents.candidate_evaluation_agent import CandidateEvaluationAgent
from agents.job_discovery_agent import JobDiscoveryAgent
from graph.state import GraphState


@lru_cache(maxsize=1)
def get_job_agent() -> JobDiscoveryAgent:
    """
    Construct the job agent only when discovery is invoked.
    """
    return JobDiscoveryAgent()


@lru_cache(maxsize=1)
def get_evaluation_agent() -> CandidateEvaluationAgent:
    """
    Construct the evaluation agent only when evaluation is invoked.
    """
    return CandidateEvaluationAgent()


def job_discovery_node(state: GraphState) -> GraphState:
    """
    Execute the Job Discovery Agent.
    """
    return get_job_agent().run(state)


def candidate_evaluation_node(state: GraphState) -> GraphState:
    """
    Execute the Candidate Evaluation Agent.
    """
    return get_evaluation_agent().run(state)
