"""OpenAI VLM provider implementation."""

import base64
import json
import os
import urllib.request
from typing import Optional

from threedllm.vlm.base import VLMProvider, VLMResponse


class OpenAIProvider(VLMProvider):
    """OpenAI GPT-4 Vision provider."""

    DEFAULT_SYSTEM_PROMPT = (
        "Create a detailed, high-quality 3D-friendly prompt describing a single object. "
        "Be specific about:\n"
        "- Shape and geometry (dimensions, proportions, curves, angles)\n"
        "- Surface details (texture, patterns, smoothness, roughness)\n"
        "- Material properties (metallic, matte, glossy, transparent, etc.)\n"
        "- Fine details (decorations, engravings, structural elements)\n"
        "- Overall form and structure\n\n"
        "Avoid scenes, backgrounds, or multiple objects. Focus on creating a detailed, "
        "high-quality 3D model with clear geometric features and surface characteristics. "
        "Use technical and descriptive language that will help generate a precise 3D mesh."
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        endpoint: str = "https://api.openai.com/v1/chat/completions",
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var).
            model: Model identifier (default: gpt-4o-mini).
            endpoint: API endpoint URL.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.endpoint = endpoint

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return self.api_key is not None

    def enhance_prompt(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> VLMResponse:
        """Enhance prompt using OpenAI's vision model."""
        if not self.is_available():
            raise RuntimeError("OpenAI API key not configured")

        content = [{"type": "text", "text": prompt}]

        if image_path and os.path.exists(image_path):
            # Validate file exists and has content
            file_size = os.path.getsize(image_path)
            if file_size > 0:
                try:
                    with open(image_path, "rb") as f:
                        image_data = f.read()
                        if len(image_data) > 0:
                            encoded = base64.b64encode(image_data).decode("utf-8")
                            # Detect image format
                            ext = os.path.splitext(image_path)[1].lower()
                            if ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                                mime_type = "image/png" if ext == ".png" else "image/jpeg"
                                content.append(
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
                                    }
                                )
                except (IOError, OSError) as e:
                    # If image file can't be read, just use text prompt
                    pass

        messages = [
            {
                "role": "system",
                "content": system_prompt or self.DEFAULT_SYSTEM_PROMPT,
            },
            {"role": "user", "content": content},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 200,
        }

        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read().decode("utf-8"))

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            text = message.get("content", "").strip()

            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens")

            return VLMResponse(text=text, model=self.model, tokens_used=tokens_used)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"OpenAI API error: {error_body}") from e
