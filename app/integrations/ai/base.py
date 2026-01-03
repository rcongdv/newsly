"""Abstract base class for AI services."""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class AIService(Protocol):
    """Protocol for AI summarization services."""

    def summarize(self, content: str) -> str:
        """Generate a summary from the given content."""
        ...
