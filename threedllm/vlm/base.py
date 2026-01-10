"""Base interfaces for Vision Language Model providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class VLMResponse:
    """Response from a VLM provider."""

    text: str
    """The generated text response."""
    model: str
    """The model identifier used."""
    tokens_used: Optional[int] = None
    """Number of tokens used (if available)."""


class VLMProvider(ABC):
    """Abstract base class for Vision Language Model providers."""

    @abstractmethod
    def enhance_prompt(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> VLMResponse:
        """
        Enhance a prompt using the VLM, optionally with an image.

        Args:
            prompt: The input text prompt.
            image_path: Optional path to an image file.
            system_prompt: Optional system prompt to guide the VLM.

        Returns:
            VLMResponse containing the enhanced prompt.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available (e.g., API key configured)."""
        pass
