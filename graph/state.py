"""
File: graph/state.py

Description:
Defines the shared state used across the LangGraph workflow.

Each agent reads from this state, updates it,
and returns the modified state.
"""

from typing_extensions import TypedDict

from models.job import Job
from models.match_assessment import MatchAssessment
from models.resume import Resume


class GraphState(TypedDict):
    """
    Shared workflow state.
    """

    role: str
    location: str

    resume: Resume | None

    jobs: list[Job]

    match_results: list[MatchAssessment]
