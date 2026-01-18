"""Neural4D API 3D generator implementation."""

import io
import os
from typing import Optional

import trimesh

from threedllm.generators.api_base import APIGenerator3D
from threedllm.generators.base import GenerationConfig, MeshResult


class Neural4DGenerator(APIGenerator3D):
    """
    Neural4D API 3D generator - High-fidelity, fast generation.
    
    ⚠️ IMPORTANT: Neural4D does not provide public API documentation.
    To use this generator, you must:
    1. Sign up at https://www.neural4d.com/api
    2. Get your API key from the dashboard
    3. Obtain API documentation (endpoints, request/response formats) from:
       - Their developer dashboard (after login)
       - Contact support@dreamtech.ai
       - Inspect network traffic from their web UI
    4. Configure the endpoints via environment variables:
       - NEURAL4D_API_BASE_URL (default: https://www.neural4d.com/api)
       - NEURAL4D_GENERATE_ENDPOINT (e.g., /v1/generate/text)
       - NEURAL4D_STATUS_ENDPOINT (e.g., /v1/tasks/{task_id})
    """

    def _get_api_key_env_name(self) -> str:
        return "NEURAL4D_API_KEY"

    def _get_default_base_url(self) -> str:
        # Note: This is a template implementation based on common API patterns.
        # The actual endpoint paths may differ - check Neural4D's API docs after signing up.
        # The base URL can be overridden via NEURAL4D_API_BASE_URL environment variable.
        import os
        # Try common patterns - user should override with correct URL from their API docs
        return os.environ.get("NEURAL4D_API_BASE_URL", "https://www.neural4d.com/api")

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

        # Try common endpoint patterns - adjust based on actual API docs
        # Common patterns: /v1/generate, /v1/text-to-3d, /generate/text, etc.
        endpoint = os.environ.get("NEURAL4D_GENERATE_ENDPOINT", "/v1/generate/text")
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        print(f"[Neural4D] Submitting to: {url}", flush=True)
        print(f"[Neural4D] ⚠️  Note: If this fails, you need to configure the correct endpoint from Neural4D's API docs.", flush=True)
        
        try:
            response = self._session.post(
                url,
                json=request_data,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            task_id = result.get("task_id") or result.get("id") or result.get("job_id")
            if not task_id:
                raise RuntimeError(f"No task ID returned from API. Response: {result}")

            return task_id
        except Exception as e:
            error_msg = (
                f"Neural4D API call failed. This is likely because:\n"
                f"1. The endpoint path is incorrect (check NEURAL4D_GENERATE_ENDPOINT)\n"
                f"2. The request format doesn't match Neural4D's API spec\n"
                f"3. You need to get the API documentation from Neural4D\n\n"
                f"Original error: {e}\n"
                f"URL attempted: {url}\n"
                f"Request data: {request_data}"
            )
            raise RuntimeError(error_msg) from e

    def _check_status(self, task_id: str) -> dict:
        """Check Neural4D generation status."""
        # Try common endpoint patterns
        endpoint = os.environ.get("NEURAL4D_STATUS_ENDPOINT", f"/v1/tasks/{task_id}")
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        # Replace {task_id} placeholder if present
        endpoint = endpoint.replace("{task_id}", task_id)
        
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        
        response = self._session.get(
            url,
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        status = data.get("status", "pending").lower()

        result = {"status": status}

        if status == "completed":
            result["result_url"] = data.get("download_url") or data.get("result_url") or data.get("file_url")
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
