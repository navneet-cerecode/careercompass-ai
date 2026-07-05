"""
File: graph/nodes.py

Description:
LangGraph nodes that delegate work to agents.
"""

from agents.candidate_evaluation_agent import CandidateEvaluationAgent
from agents.job_discovery_agent import JobDiscoveryAgent
from graph.state import GraphState

job_agent = JobDiscoveryAgent()
evaluation_agent = CandidateEvaluationAgent()


def job_discovery_node(state: GraphState) -> GraphState:
    """
    Execute the Job Discovery Agent.
    """
    return job_agent.run(state)


def candidate_evaluation_node(state: GraphState) -> GraphState:
    """
    Execute the Candidate Evaluation Agent.
    """
    return evaluation_agent.run(state)