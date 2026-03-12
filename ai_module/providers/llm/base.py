from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    def generate_json(self, *, prompt: str) -> dict[str, Any]:
        """Generate model output and parse it as JSON."""

