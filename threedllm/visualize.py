"""Visualization utilities for 3D meshes."""

from typing import Optional

from threedllm.generators.base import MeshResult


def visualize_mesh(
    result: MeshResult,
    output_path: Optional[str] = None,
    show: bool = True,
) -> None:
    """
    Visualize a 3D mesh using matplotlib.

    Args:
        result: Mesh result to visualize.
        output_path: Optional path to save the visualization.
        show: Whether to display the plot interactively.
    """
    try:
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
    except ImportError:
        raise ImportError(
            "matplotlib is required for visualization. Install with: pip install matplotlib"
        )

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    # Extract coordinates
    x = [v[0] for v in result.vertices]
    y = [v[1] for v in result.vertices]
    z = [v[2] for v in result.vertices]

    # Plot vertices
    ax.scatter(x, y, z, c=z, cmap="viridis", s=1, alpha=0.6)

    # Set labels
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title(f"3D Mesh: {result.prompt[:50]}...")

    # Equal aspect ratio
    max_range = max(
        max(x) - min(x),
        max(y) - min(y),
        max(z) - min(z),
    ) / 2.0
    mid_x = (max(x) + min(x)) * 0.5
    mid_y = (max(y) + min(y)) * 0.5
    mid_z = (max(z) + min(z)) * 0.5
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Visualization saved to: {output_path}")

    if show:
        plt.show()
    else:
        plt.close()


def print_mesh_info(result: MeshResult) -> None:
    """Print information about a mesh result."""
    print(f"\nMesh Information:")
    print(f"  Prompt: {result.prompt}")
    print(f"  Vertices: {len(result.vertices)}")
    if result.faces:
        print(f"  Faces: {len(result.faces)}")
    else:
        print(f"  Faces: None (point cloud)")

    if result.vertices:
        # Calculate bounding box
        x_coords = [v[0] for v in result.vertices]
        y_coords = [v[1] for v in result.vertices]
        z_coords = [v[2] for v in result.vertices]

        print(f"  Bounding Box:")
        print(f"    X: [{min(x_coords):.3f}, {max(x_coords):.3f}]")
        print(f"    Y: [{min(y_coords):.3f}, {max(y_coords):.3f}]")
        print(f"    Z: [{min(z_coords):.3f}, {max(z_coords):.3f}]")
