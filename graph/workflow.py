"""
File: graph/workflow.py

Description:
Defines the LangGraph workflow for CareerCompass AI.
"""

from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    candidate_evaluation_node,
    job_discovery_node,
)
from graph.state import GraphState


def build_discovery_workflow():
    """Build the discovery-only workflow used by the current Streamlit search."""

    workflow = StateGraph(GraphState)
    workflow.add_node("job_discovery", job_discovery_node)
    workflow.add_edge(START, "job_discovery")
    workflow.add_edge("job_discovery", END)

    return workflow.compile()


def build_recommendation_workflow():
    """Build the resume-aware discovery and assessment workflow."""

    workflow = StateGraph(GraphState)
    workflow.add_node("job_discovery", job_discovery_node)
    workflow.add_node("candidate_evaluation", candidate_evaluation_node)
    workflow.add_edge(START, "job_discovery")
    workflow.add_edge(
        "job_discovery",
        "candidate_evaluation",
    )

    workflow.add_edge(
        "candidate_evaluation",
        END,
    )

    return workflow.compile()


def build_workflow():
    """Compatibility alias for the discovery-only application workflow."""
    return build_discovery_workflow()


graph = build_workflow()
