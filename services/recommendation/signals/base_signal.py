"""
Base class for recommendation signals.
"""

from abc import ABC, abstractmethod

from services.recommendation.models.signal_result import SignalResult


class BaseSignal(ABC):
    """
    Base class for all recommendation signals.
    """

    @abstractmethod
    def evaluate(
        self,
        resume,
        job,
    ) -> SignalResult:
        """
        Evaluate one recommendation signal.
        """

        pass