"""Base interfaces for 3D generation backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple

Point = Tuple[float, float, float]


@dataclass
class GenerationConfig:
    """Configuration for 3D generation."""

    guidance_scale: float = 17.5
    """Classifier-free guidance scale. Higher values (15-20) improve prompt adherence."""
    karras_steps: int = 100
    """Number of Karras sampling steps. More steps (100-128) = better quality but slower."""
    seed: Optional[int] = None
    """Random seed for reproducibility."""
    batch_size: int = 1
    """Batch size for generation."""
    
    @classmethod
    def quality_preset(cls, preset: str = "balanced") -> "GenerationConfig":
        """
        Create a config with quality presets.
        
        Args:
            preset: "fast" (64 steps, 15.0 guidance), 
                   "balanced" (100 steps, 17.5 guidance),
                   "high" (128 steps, 20.0 guidance)
        """
        presets = {
            "fast": {"karras_steps": 64, "guidance_scale": 15.0},
            "balanced": {"karras_steps": 100, "guidance_scale": 17.5},
            "high": {"karras_steps": 128, "guidance_scale": 20.0},
        }
        if preset not in presets:
            preset = "balanced"
        return cls(**presets[preset])


@dataclass
class MeshResult:
    """Result from 3D generation."""

    vertices: List[Point]
    """List of vertex coordinates (x, y, z)."""
    faces: Optional[List[Tuple[int, int, int]]] = None
    """List of face indices (triangles)."""
    normals: Optional[List[Point]] = None
    """Vertex normals (if available)."""
    prompt: str = ""
    """The prompt used for generation."""


class Generator3D(ABC):
    """Abstract base class for 3D generation backends."""

    @abstractmethod
    def generate(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> MeshResult:
        """
        Generate a 3D mesh from a text prompt.

        Args:
            prompt: Text description of the 3D object.
            config: Optional generation configuration.

        Returns:
            MeshResult containing vertices and faces.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the generator is available (e.g., models loaded)."""
        pass
