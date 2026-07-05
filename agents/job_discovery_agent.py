"""
File: agents/job_discovery_agent.py

Description:
Job Discovery Agent.

Uses the JobDiscoveryService to fetch real jobs
from supported providers.
"""

from agents.base_agent import BaseAgent
from graph.state import GraphState
from services.job_discovery.discovery_service import JobDiscoveryService


class JobDiscoveryAgent(BaseAgent):
    """
    Finds jobs matching the requested role.
    """

    def __init__(self):

        self.discovery_service = JobDiscoveryService()

    def run(
        self,
        state: GraphState,
    ) -> GraphState:

        role = state["role"]
        location = state["location"]

        jobs = self.discovery_service.discover(
            role=role,
            location=location,
        )

        state["jobs"] = jobs

        return state