"""Shap-E 3D generation backend."""

from typing import Optional

import torch
from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
from shap_e.diffusion.sample import sample_latents
from shap_e.models.download import load_config, load_model

from threedllm.generators.base import GenerationConfig, Generator3D, MeshResult


class ShapEGenerator(Generator3D):
    """Shap-E 3D generation backend."""

    def __init__(self, device: Optional[str] = None):
        """
        Initialize Shap-E generator.

        Args:
            device: Device to use ('cuda', 'cpu', or None for auto-detect).
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._text_model = None
        self._decoder_model = None
        self._diffusion = None
        self._loaded = False

    def _load_models(self):
        """Lazy load Shap-E models."""
        if self._loaded:
            return

        device = torch.device(self.device)
        self._text_model = load_model("text300M", device)
        self._decoder_model = load_model("decoder", device)
        self._diffusion = diffusion_from_config(load_config("diffusion"))
        self._loaded = True

    def is_available(self) -> bool:
        """Check if Shap-E is available."""
        try:
            import shap_e
            # Try importing key modules to ensure dependencies are available
            from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
            from shap_e.diffusion.sample import sample_latents
            from shap_e.models.download import load_config, load_model
            # Check if ipywidgets is available (needed for decode_latent_mesh)
            try:
                import ipywidgets
            except ImportError:
                # ipywidgets is optional but recommended
                pass
            return True
        except (ImportError, Exception):
            return False

    def generate(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> MeshResult:
        """Generate a 3D mesh using Shap-E."""
        if not self.is_available():
            raise RuntimeError("Shap-E is not installed")

        if config is None:
            config = GenerationConfig()

        self._load_models()

        device = torch.device(self.device)
        if config.seed is not None:
            torch.manual_seed(config.seed)

        print(f"Starting Shap-E generation on {device}...", flush=True)
        print(f"Prompt: {prompt}", flush=True)
        print(f"Steps: {config.karras_steps}, Guidance: {config.guidance_scale}", flush=True)
        
        # Required parameters for newer versions of shap-e
        # Default values based on OpenAI's Shap-E implementation
        latents = sample_latents(
            batch_size=config.batch_size,
            model=self._text_model,
            diffusion=self._diffusion,
            guidance_scale=config.guidance_scale,
            model_kwargs={"texts": [prompt]},
            progress=True,
            clip_denoised=True,
            use_fp16=device.type == "cuda",
            use_karras=True,
            karras_steps=config.karras_steps,
            sigma_min=1e-3,  # Minimum noise level (0.001)
            sigma_max=160.0,  # Maximum noise level
            s_churn=0.0,  # Stochasticity parameter (0 = deterministic)
        )
        
        print("Latents sampled, decoding mesh...", flush=True)

        # Lazy import to avoid ipywidgets dependency at module level
        from shap_e.util.notebooks import decode_latent_mesh
        mesh = decode_latent_mesh(self._decoder_model, latents[0]).tri_mesh()
        vertices = [
            (float(x), float(y), float(z)) for x, y, z in mesh.vertices
        ]

        # Extract faces if available
        faces = None
        if hasattr(mesh, "faces") and mesh.faces is not None:
            faces = [tuple(map(int, face)) for face in mesh.faces]

        return MeshResult(
            vertices=vertices,
            faces=faces,
            prompt=prompt,
        )
