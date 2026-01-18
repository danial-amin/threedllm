"""Hugging Face 3D generator implementation.

Supports three deployment modes:
1. Inference API (serverless, managed by HF)
2. Inference Endpoints (dedicated endpoints)
3. Local model (self-hosted)
"""

import io
import os
from typing import Optional

import trimesh

from threedllm.generators.base import GenerationConfig, Generator3D, MeshResult


class HuggingFaceGenerator(Generator3D):
    """
    Hugging Face 3D generator.
    
    Supports multiple deployment modes:
    - Inference API: Use HF's serverless inference (set HF_MODEL_ID and HF_API_TOKEN)
    - Inference Endpoint: Use dedicated endpoint (set HF_ENDPOINT_URL and HF_API_TOKEN)
    - Local model: Load model locally (set HF_MODEL_ID and HF_LOCAL_MODEL_PATH)
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        api_token: Optional[str] = None,
        local_model_path: Optional[str] = None,
        device: Optional[str] = None,
    ):
        """
        Initialize Hugging Face generator.

        Args:
            model_id: Hugging Face model ID (e.g., "username/model-name")
            endpoint_url: Custom endpoint URL (for Inference Endpoints)
            api_token: Hugging Face API token
            local_model_path: Path to local model directory (for self-hosting)
            device: Device for local models ("cuda" or "cpu")
        """
        self.model_id = model_id or os.environ.get("HF_MODEL_ID")
        self.endpoint_url = endpoint_url or os.environ.get("HF_ENDPOINT_URL")
        self.api_token = api_token or os.environ.get("HF_API_TOKEN")
        self.local_model_path = local_model_path or os.environ.get("HF_LOCAL_MODEL_PATH")
        self.device = device or os.environ.get("HF_DEVICE", "cuda" if self._has_cuda() else "cpu")
        
        # Determine deployment mode
        if self.endpoint_url:
            self.mode = "endpoint"
        elif self.local_model_path:
            self.mode = "local"
        else:
            self.mode = "inference_api"
        
        # Local model components (lazy loaded)
        self._model = None
        self._processor = None
        self._loaded = False
        
        # HTTP session for API/Endpoint calls
        self._session = None

    def _has_cuda(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _get_session(self):
        """Get or create HTTP session for API calls."""
        if self._session is None:
            import requests
            self._session = requests.Session()
            if self.api_token:
                self._session.headers.update({
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                })
        return self._session

    def _load_local_model(self):
        """Load model locally for self-hosting."""
        if self._loaded:
            return
        
        if not self.local_model_path:
            raise RuntimeError("HF_LOCAL_MODEL_PATH not set for local model deployment")
        
        print(f"[HuggingFace] Loading local model from: {self.local_model_path}", flush=True)
        
        try:
            # Try to load as a transformers model
            from transformers import AutoModel, AutoProcessor
            
            self._processor = AutoProcessor.from_pretrained(self.local_model_path)
            
            # Try to determine model type and load accordingly
            # This is a generic approach - you may need to customize based on your model
            try:
                self._model = AutoModel.from_pretrained(
                    self.local_model_path,
                    torch_dtype="auto",
                    device_map=self.device,
                )
            except Exception as e:
                print(f"[HuggingFace] AutoModel failed, trying alternative loading: {e}", flush=True)
                # Fallback: try loading with specific model class
                # You may need to customize this based on your specific model
                import torch
                from transformers import AutoConfig
                config = AutoConfig.from_pretrained(self.local_model_path)
                # Add custom loading logic here based on model type
                raise RuntimeError(f"Model loading failed. You may need to customize the loading code for your model type: {e}")
            
            self._loaded = True
            print(f"[HuggingFace] Local model loaded successfully", flush=True)
            
        except ImportError:
            raise RuntimeError(
                "transformers library required for local model deployment. "
                "Install with: pip install transformers torch"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load local model: {e}")

    def is_available(self) -> bool:
        """Check if Hugging Face generator is available."""
        if self.mode == "local":
            try:
                import torch
                from transformers import AutoModel
                return True
            except ImportError:
                return False
        elif self.mode == "endpoint":
            # Check if endpoint URL and token are set
            return bool(self.endpoint_url and self.api_token)
        else:  # inference_api
            # Check if model ID and token are set
            return bool(self.model_id and self.api_token)

    def _call_inference_api(self, prompt: str, config: Optional[GenerationConfig] = None) -> dict:
        """Call Hugging Face Inference API."""
        if not self.model_id:
            raise RuntimeError("HF_MODEL_ID must be set for Inference API mode")
        
        if not self.api_token:
            raise RuntimeError("HF_API_TOKEN must be set for Inference API mode")
        
        session = self._get_session()
        
        # Hugging Face Inference API endpoint
        url = f"https://api-inference.huggingface.co/models/{self.model_id}"
        
        # Prepare request payload
        # Adjust this based on your model's expected input format
        payload = {
            "inputs": prompt,
            "parameters": {}
        }
        
        if config:
            # Map our config to model-specific parameters
            # Adjust these based on your model's API
            if hasattr(config, 'karras_steps'):
                payload["parameters"]["num_inference_steps"] = config.karras_steps
            if hasattr(config, 'guidance_scale'):
                payload["parameters"]["guidance_scale"] = config.guidance_scale
            if config.seed is not None:
                payload["parameters"]["seed"] = config.seed
        
        print(f"[HuggingFace] Calling Inference API: {url}", flush=True)
        print(f"[HuggingFace] Payload: {payload}", flush=True)
        
        response = session.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        return response.json()

    def _call_endpoint(self, prompt: str, config: Optional[GenerationConfig] = None) -> dict:
        """Call Hugging Face Inference Endpoint."""
        if not self.endpoint_url:
            raise RuntimeError("HF_ENDPOINT_URL must be set for endpoint mode")
        
        session = self._get_session()
        
        # Prepare request payload
        payload = {
            "inputs": prompt,
            "parameters": {}
        }
        
        if config:
            if hasattr(config, 'karras_steps'):
                payload["parameters"]["num_inference_steps"] = config.karras_steps
            if hasattr(config, 'guidance_scale'):
                payload["parameters"]["guidance_scale"] = config.guidance_scale
            if config.seed is not None:
                payload["parameters"]["seed"] = config.seed
        
        print(f"[HuggingFace] Calling Endpoint: {self.endpoint_url}", flush=True)
        
        response = session.post(self.endpoint_url, json=payload, timeout=120)
        response.raise_for_status()
        
        return response.json()

    def _generate_local(self, prompt: str, config: Optional[GenerationConfig] = None) -> dict:
        """Generate using local model."""
        import torch
        
        self._load_local_model()
        
        # Process input
        inputs = self._processor(prompt, return_tensors="pt")
        if hasattr(inputs, 'to'):
            inputs = inputs.to(self.device)
        
        # Generate
        # NOTE: This is a generic implementation. You'll need to customize
        # based on your specific model's generation method.
        with torch.no_grad():
            outputs = self._model.generate(**inputs)
        
        # Process output
        # Adjust based on your model's output format
        result = self._processor.decode(outputs[0], skip_special_tokens=True)
        
        return {"generated": result}

    def _parse_response_to_mesh(self, response: dict) -> MeshResult:
        """
        Parse API/Endpoint response to MeshResult.
        
        This is model-specific. Adjust based on your model's output format.
        Common formats:
        - Direct mesh data (vertices, faces)
        - Base64 encoded 3D file
        - URL to 3D file
        - Point cloud data
        """
        # Try to extract mesh data from response
        # This is a generic implementation - customize for your model
        
        # Option 1: Response contains direct mesh data
        if "vertices" in response and "faces" in response:
            vertices = response["vertices"]
            faces = response.get("faces")
            normals = response.get("normals")
            return MeshResult(
                vertices=vertices,
                faces=faces,
                normals=normals,
                prompt="",
            )
        
        # Option 2: Response contains base64 encoded file
        if "file" in response or "mesh" in response:
            import base64
            file_data = base64.b64decode(response.get("file") or response.get("mesh"))
            return self._parse_file_to_mesh(file_data)
        
        # Option 3: Response contains URL to file
        if "url" in response or "download_url" in response:
            url = response.get("url") or response.get("download_url")
            session = self._get_session()
            file_data = session.get(url, timeout=60).content
            return self._parse_file_to_mesh(file_data)
        
        # Option 4: Response contains raw bytes or file path
        if "data" in response:
            file_data = response["data"]
            if isinstance(file_data, str):
                # Assume base64
                import base64
                file_data = base64.b64decode(file_data)
            return self._parse_file_to_mesh(file_data)
        
        # If none of the above, try to parse as generic format
        # This might work if the response is already in a parseable format
        raise RuntimeError(
            f"Could not parse response to mesh. Response format not recognized. "
            f"Response keys: {list(response.keys())}. "
            f"You may need to customize _parse_response_to_mesh() for your model."
        )

    def _parse_file_to_mesh(self, file_data: bytes, format: str = "obj") -> MeshResult:
        """Parse 3D file bytes to MeshResult using trimesh."""
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
            raise RuntimeError(f"Failed to parse mesh file: {e}")

    def generate(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> MeshResult:
        """Generate a 3D mesh from a text prompt."""
        if not self.is_available():
            raise RuntimeError(
                f"Hugging Face generator is not available. "
                f"Mode: {self.mode}. "
                f"Check your configuration (HF_MODEL_ID, HF_API_TOKEN, etc.)"
            )
        
        if config is None:
            config = GenerationConfig()
        
        print(f"[HuggingFace] Generating 3D model (mode: {self.mode})...", flush=True)
        print(f"[HuggingFace] Prompt: {prompt}", flush=True)
        
        # Call appropriate method based on mode
        if self.mode == "inference_api":
            response = self._call_inference_api(prompt, config)
        elif self.mode == "endpoint":
            response = self._call_endpoint(prompt, config)
        else:  # local
            response = self._generate_local(prompt, config)
        
        # Parse response to mesh
        mesh_result = self._parse_response_to_mesh(response)
        mesh_result.prompt = prompt
        
        return mesh_result
