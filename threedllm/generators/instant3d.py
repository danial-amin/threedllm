"""Instant3D.co API 3D generator implementation."""

import io
from typing import Optional

import trimesh

from threedllm.generators.api_base import APIGenerator3D
from threedllm.generators.base import GenerationConfig, MeshResult


class Instant3DGenerator(APIGenerator3D):
    """Instant3D.co API 3D generator - Fast generation with PBR textures."""

    def _get_api_key_env_name(self) -> str:
        return "INSTANT3D_API_KEY"

    def _get_default_base_url(self) -> str:
        # Note: This is a template implementation.
        # You need to check Instant3D's actual API documentation for the correct endpoint.
        # The base URL can be overridden via INSTANT3D_API_BASE_URL environment variable.
        import os
        return os.environ.get("INSTANT3D_API_BASE_URL", "https://api.instant3d.co/v1")

    def _get_auth_headers(self) -> dict:
        return {"X-API-Key": self.api_key}

    def _create_generation_request(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> dict:
        """Create Instant3D generation request."""
        request_data = {
            "prompt": prompt,
            "type": "text_to_3d",
        }

        # Add quality settings
        if config:
            # Instant3D uses resolution/quality parameters
            if config.karras_steps >= 128:
                request_data["quality"] = "high"
            elif config.karras_steps <= 64:
                request_data["quality"] = "fast"
            else:
                request_data["quality"] = "standard"

        return request_data

    def _submit_generation(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> str:
        """Submit generation to Instant3D API."""
        request_data = self._create_generation_request(prompt, config)

        response = self._session.post(
            f"{self.base_url}/generate",
            json=request_data,
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()
        task_id = result.get("job_id") or result.get("id") or result.get("task_id")
        if not task_id:
            raise RuntimeError("No task ID returned from API")

        return task_id

    def _check_status(self, task_id: str) -> dict:
        """Check Instant3D generation status."""
        response = self._session.get(
            f"{self.base_url}/jobs/{task_id}",
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        status = data.get("status", "pending").lower()

        result = {"status": status}

        if status in ["completed", "done", "success"]:
            result["status"] = "completed"
            result["result_url"] = data.get("download_url") or data.get("model_url")
            result["format"] = data.get("format", "obj")

        elif status in ["failed", "error"]:
            result["status"] = "failed"
            result["error"] = data.get("error", "Generation failed")

        elif status in ["processing", "generating", "in_progress"]:
            result["status"] = "processing"

        return result

    def _download_result(self, result_url: str) -> bytes:
        """Download the generated 3D model."""
        response = self._session.get(result_url, timeout=60)
        response.raise_for_status()
        return response.content

    def _parse_mesh(self, file_data: bytes, format: str = "obj") -> MeshResult:
        """Parse 3D file into MeshResult using trimesh."""
        try:
            mesh = trimesh.load(io.BytesIO(file_data), file_type=format)

            vertices = [
                (float(v[0]), float(v[1]), float(v[2])) for v in mesh.vertices
            ]

            faces = None
            if hasattr(mesh, "faces") and mesh.faces is not None:
                faces = [tuple(map(int, face)) for face in mesh.faces]

            normals = None
            if hasattr(mesh, "vertex_normals") and mesh.vertex_normals is not None:
                normals = [
                    (float(n[0]), float(n[1]), float(n[2])) for n in mesh.vertex_normals
                ]

            return MeshResult(
                vertices=vertices,
                faces=faces,
                normals=normals,
                prompt="",
            )
        except Exception as e:
            raise RuntimeError(f"Failed to parse mesh: {e}")
