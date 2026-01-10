"""PLY mesh exporter."""

from threedllm.exporters.base import Exporter3D
from threedllm.generators.base import MeshResult


class PLYExporter(Exporter3D):
    """Exports meshes in PLY format."""

    def get_file_extension(self) -> str:
        """Get the file extension."""
        return ".ply"

    def export(self, result: MeshResult, path: str) -> None:
        """Export mesh as PLY file."""
        num_vertices = len(result.vertices)
        num_faces = len(result.faces) if result.faces else 0

        with open(path, "w", encoding="utf-8") as f:
            # Write PLY header
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            if result.prompt:
                f.write(f"comment Prompt: {result.prompt}\n")
            f.write(f"element vertex {num_vertices}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            if num_faces > 0:
                f.write(f"element face {num_faces}\n")
                f.write("property list uchar int vertex_indices\n")
            f.write("end_header\n")

            # Write vertices
            for x, y, z in result.vertices:
                f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")

            # Write faces
            if result.faces:
                for face in result.faces:
                    f.write(f"3 {face[0]} {face[1]} {face[2]}\n")
