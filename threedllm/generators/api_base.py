"""Base class for API-based 3D generators."""

import os
import time
from abc import ABC, abstractmethod
from typing import Optional

import requests

from threedllm.generators.base import GenerationConfig, Generator3D, MeshResult


class APIGenerator3D(Generator3D, ABC):
    """Base class for API-based 3D generators."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize API generator.

        Args:
            api_key: API key for the service (can also be set via environment variable).
            base_url: Base URL for the API (optional, uses default if not provided).
        """
        self.api_key = api_key or os.environ.get(self._get_api_key_env_name())
        self.base_url = base_url or self._get_default_base_url()
        self._session = requests.Session()
        if self.api_key:
            self._session.headers.update(self._get_auth_headers())

    @abstractmethod
    def _get_api_key_env_name(self) -> str:
        """Return the environment variable name for the API key."""
        pass

    @abstractmethod
    def _get_default_base_url(self) -> str:
        """Return the default base URL for the API."""
        pass

    @abstractmethod
    def _get_auth_headers(self) -> dict:
        """Return authentication headers."""
        pass

    @abstractmethod
    def _create_generation_request(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> dict:
        """Create the request payload for generation."""
        pass

    @abstractmethod
    def _submit_generation(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> str:
        """
        Submit generation request and return task/job ID.

        Returns:
            Task/job ID for polling.
        """
        pass

    @abstractmethod
    def _check_status(self, task_id: str) -> dict:
        """
        Check the status of a generation task.

        Returns:
            Dict with 'status' ('pending', 'processing', 'completed', 'failed')
            and optionally 'result_url' or 'error'.
        """
        pass

    @abstractmethod
    def _download_result(self, result_url: str) -> bytes:
        """Download the generated 3D model file."""
        pass

    @abstractmethod
    def _parse_mesh(self, file_data: bytes, format: str = "obj") -> MeshResult:
        """
        Parse the downloaded 3D file into a MeshResult.

        Args:
            file_data: Raw file bytes.
            format: File format (obj, ply, stl, etc.)

        Returns:
            MeshResult with vertices and faces.
        """
        pass

    def generate(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> MeshResult:
        """
        Generate a 3D mesh from a text prompt using the API.

        Args:
            prompt: Text description of the 3D object.
            config: Optional generation configuration (may be ignored by some APIs).

        Returns:
            MeshResult containing vertices and faces.
        """
        if not self.is_available():
            raise RuntimeError(f"{self.__class__.__name__} is not available. Check API key.")

        # Submit generation request
        task_id = self._submit_generation(prompt, config)

        # Poll for completion
        max_wait = 300  # 5 minutes max
        poll_interval = 5  # Check every 5 seconds
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status_info = self._check_status(task_id)

            if status_info["status"] == "completed":
                # Download result
                result_url = status_info.get("result_url")
                if not result_url:
                    raise RuntimeError("Generation completed but no result URL provided")

                file_data = self._download_result(result_url)
                format = status_info.get("format", "obj")

                # Parse mesh
                return self._parse_mesh(file_data, format)

            elif status_info["status"] == "failed":
                error = status_info.get("error", "Unknown error")
                raise RuntimeError(f"Generation failed: {error}")

            # Still processing, wait and retry
            time.sleep(poll_interval)

        raise RuntimeError("Generation timed out")

    def is_available(self) -> bool:
        """Check if the API generator is available (has API key)."""
        return self.api_key is not None and len(self.api_key.strip()) > 0
