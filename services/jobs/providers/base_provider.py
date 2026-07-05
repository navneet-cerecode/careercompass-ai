"""
Base Job Provider.

Every job provider must implement this interface.
"""

from abc import ABC, abstractmethod

from models.job import Job


class BaseProvider(ABC):
    """
    Abstract job provider.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Provider name.
        """
        pass

    @abstractmethod
    def search(
        self,
        role: str,
        location: str,
    ) -> list[Job]:
        """
        Search for jobs.
        """
        pass