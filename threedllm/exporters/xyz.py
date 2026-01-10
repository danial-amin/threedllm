"""XYZ point cloud exporter."""

import random
from typing import List, Optional

from threedllm.exporters.base import Exporter3D
from threedllm.generators.base import MeshResult, Point


class XYZExporter(Exporter3D):
    """Exports point clouds in XYZ format."""

    def __init__(self, max_points: Optional[int] = None, seed: Optional[int] = None):
        """
        Initialize XYZ exporter.

        Args:
            max_points: Maximum number of points to export (samples if needed).
            seed: Random seed for sampling.
        """
        self.max_points = max_points
        self.seed = seed

    def get_file_extension(self) -> str:
        """Get the file extension."""
        return ".xyz"

    def _sample_points(self, vertices: List[Point], count: int) -> List[Point]:
        """Sample points from vertices."""
        if count <= 0 or count >= len(vertices):
            return vertices
        rng = random.Random(self.seed)
        return rng.sample(vertices, count)

    def export(self, result: MeshResult, path: str) -> None:
        """Export mesh as XYZ point cloud."""
        points = result.vertices
        if self.max_points and len(points) > self.max_points:
            points = self._sample_points(points, self.max_points)

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{len(points)}\n")
            f.write(f"prompt={result.prompt}\n")
            for x, y, z in points:
                f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")
