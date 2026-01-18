"""3D generation backends."""

from threedllm.generators.base import Generator3D, GenerationConfig, MeshResult
from threedllm.generators.shap_e import ShapEGenerator

__all__ = [
    "Generator3D",
    "GenerationConfig",
    "MeshResult",
    "ShapEGenerator",
]

# API-based generators (optional, require API keys)
try:
    from threedllm.generators.api_base import APIGenerator3D
    from threedllm.generators.neural4d import Neural4DGenerator
    from threedllm.generators.instant3d import Instant3DGenerator
    __all__.extend(["APIGenerator3D", "Neural4DGenerator", "Instant3DGenerator"])
except ImportError:
    pass

# Hugging Face generator (optional, requires transformers)
try:
    from threedllm.generators.huggingface import HuggingFaceGenerator
    __all__.append("HuggingFaceGenerator")
except ImportError:
    pass
