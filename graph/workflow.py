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


def build_workflow():
    """
    Build and compile the CareerCompass workflow.
    """

    workflow = StateGraph(GraphState)

    # Nodes
    workflow.add_node("job_discovery", job_discovery_node)
    workflow.add_node(
        "candidate_evaluation",
        candidate_evaluation_node,
    )

    # Edges
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


graph = build_workflow()