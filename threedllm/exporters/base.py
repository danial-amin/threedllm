"""Base interfaces for 3D file exporters."""

from abc import ABC, abstractmethod

from threedllm.generators.base import MeshResult


class Exporter3D(ABC):
    """Abstract base class for 3D file format exporters."""

    @abstractmethod
    def export(self, result: MeshResult, path: str) -> None:
        """
        Export a mesh result to a file.

        Args:
            result: The mesh result to export.
            path: Output file path.
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this exporter (e.g., '.obj')."""
        pass
