"""3D generation backends."""

from threedllm.generators.base import Generator3D, GenerationConfig, MeshResult
from threedllm.generators.shap_e import ShapEGenerator

# API-based generators (optional, require API keys)
try:
    from threedllm.generators.neural4d import Neural4DGenerator
    from threedllm.generators.instant3d import Instant3DGenerator
    __all__ = [
        "Generator3D",
        "GenerationConfig",
        "MeshResult",
        "ShapEGenerator",
        "Neural4DGenerator",
        "Instant3DGenerator",
    ]
except ImportError:
    # trimesh might not be installed
    __all__ = [
        "Generator3D",
        "GenerationConfig",
        "MeshResult",
        "ShapEGenerator",
    ]
