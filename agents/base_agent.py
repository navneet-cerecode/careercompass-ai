"""
File: agents/base_agent.py

Description:
Defines the abstract base class for all agents.
"""

from abc import ABC, abstractmethod

from graph.state import GraphState


class BaseAgent(ABC):
    """
    Base class for all CareerCompass agents.
    """

    @abstractmethod
    def run(self, state: GraphState) -> GraphState:
        """
        Execute the agent.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state.
        """
        pass