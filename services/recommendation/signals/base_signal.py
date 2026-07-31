"""
Base class for recommendation signals.
"""

from abc import ABC, abstractmethod

from models.score_component import ScoreComponent


class BaseSignal(ABC):
    """
    Base class for all recommendation signals.
    """

    @abstractmethod
    def evaluate(
        self,
        resume,
        job,
    ) -> ScoreComponent:
        """
        Evaluate one recommendation signal.
        """

        pass
