"""
Base interface for all job providers.
"""

from abc import ABC, abstractmethod

from models.job import Job


class BaseProvider(ABC):
    """
    Abstract base class for job providers.
    """

    @abstractmethod
    def search(
        self,
        role: str,
        location: str,
    ) -> list[Job]:
        """
        Search for jobs matching the role and location.
        """
        raise NotImplementedError