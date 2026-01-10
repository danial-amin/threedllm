"""3D generation backends."""

from threedllm.generators.base import Generator3D, GenerationConfig, MeshResult
from threedllm.generators.shap_e import ShapEGenerator

__all__ = ["Generator3D", "GenerationConfig", "MeshResult", "ShapEGenerator"]
