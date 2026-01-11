"""Neural4D API 3D generator implementation."""

import io
from typing import Optional

import trimesh

from threedllm.generators.api_base import APIGenerator3D
from threedllm.generators.base import GenerationConfig, MeshResult


class Neural4DGenerator(APIGenerator3D):
    """Neural4D API 3D generator - High-fidelity, fast generation."""

    def _get_api_key_env_name(self) -> str:
        return "NEURAL4D_API_KEY"

    def _get_default_base_url(self) -> str:
        return "https://api.neural4d.com/v1"

    def _get_auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _create_generation_request(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> dict:
        """Create Neural4D generation request."""
        request_data = {
            "prompt": prompt,
            "mode": "text_to_3d",
        }

        # Add quality settings if config provided
        if config:
            # Map our config to Neural4D parameters
            # Neural4D uses quality levels: "fast", "standard", "high"
            if config.karras_steps <= 64:
                request_data["quality"] = "fast"
            elif config.karras_steps >= 128:
                request_data["quality"] = "high"
            else:
                request_data["quality"] = "standard"

        return request_data

    def _submit_generation(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> str:
        """Submit generation to Neural4D API."""
        request_data = self._create_generation_request(prompt, config)

        response = self._session.post(
            f"{self.base_url}/generate",
            json=request_data,
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()
        task_id = result.get("task_id") or result.get("id")
        if not task_id:
            raise RuntimeError("No task ID returned from API")

        return task_id

    def _check_status(self, task_id: str) -> dict:
        """Check Neural4D generation status."""
        response = self._session.get(
            f"{self.base_url}/tasks/{task_id}",
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        status = data.get("status", "pending").lower()

        result = {"status": status}

        if status == "completed":
            result["result_url"] = data.get("download_url") or data.get("result_url")
            result["format"] = data.get("format", "obj")

        elif status == "failed":
            result["error"] = data.get("error", "Generation failed")

        return result

    def _download_result(self, result_url: str) -> bytes:
        """Download the generated 3D model."""
        response = self._session.get(result_url, timeout=60)
        response.raise_for_status()
        return response.content

    def _parse_mesh(self, file_data: bytes, format: str = "obj") -> MeshResult:
        """Parse 3D file into MeshResult using trimesh."""
        try:
            # Use trimesh to parse various formats
            mesh = trimesh.load(io.BytesIO(file_data), file_type=format)

            # Extract vertices
            vertices = [
                (float(v[0]), float(v[1]), float(v[2])) for v in mesh.vertices
            ]

            # Extract faces
            faces = None
            if hasattr(mesh, "faces") and mesh.faces is not None:
                faces = [tuple(map(int, face)) for face in mesh.faces]

            # Extract normals if available
            normals = None
            if hasattr(mesh, "vertex_normals") and mesh.vertex_normals is not None:
                normals = [
                    (float(n[0]), float(n[1]), float(n[2])) for n in mesh.vertex_normals
                ]

            return MeshResult(
                vertices=vertices,
                faces=faces,
                normals=normals,
                prompt="",  # Will be set by pipeline
            )
        except Exception as e:
            raise RuntimeError(f"Failed to parse mesh: {e}")
