"""Command-line interface for ThreeDLLM."""

import argparse
import os
import sys
from pathlib import Path

from threedllm.exporters.obj import OBJExporter
from threedllm.exporters.ply import PLYExporter
from threedllm.exporters.stl import STLExporter
from threedllm.exporters.xyz import XYZExporter
from threedllm.generators.base import GenerationConfig
from threedllm.generators.shap_e import ShapEGenerator
from threedllm.pipeline import ThreeDPipeline
from threedllm.vlm.openai import OpenAIProvider
from threedllm.visualize import print_mesh_info, visualize_mesh


def get_exporter(format_name: str, max_points: int = None, seed: int = None):
    """Get exporter by format name."""
    exporters = {
        "xyz": XYZExporter(max_points=max_points, seed=seed),
        "obj": OBJExporter(),
        "ply": PLYExporter(),
        "stl": STLExporter(),
    }
    if format_name not in exporters:
        raise ValueError(f"Unknown format: {format_name}. Choose from: {list(exporters.keys())}")
    return exporters[format_name]


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate 3D objects from text prompts using VLM-enhanced generation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic generation
  %(prog)s "red dragon"

  # With VLM enhancement
  %(prog)s "red dragon" --use-vlm

  # With image input
  %(prog)s "dragon" --image dragon.png

  # Export as OBJ
  %(prog)s "dragon" --format obj --output dragon.obj

  # Custom generation parameters
  %(prog)s "dragon" --guidance-scale 20 --steps 128 --seed 42
        """,
    )

    # Input
    parser.add_argument(
        "prompt",
        help="Text prompt describing the 3D object to generate.",
    )
    parser.add_argument(
        "--image",
        type=str,
        help="Optional image path to use with VLM for enhanced prompt generation.",
    )

    # VLM options
    parser.add_argument(
        "--use-vlm",
        action="store_true",
        help="Use VLM to enhance the prompt before 3D generation.",
    )
    parser.add_argument(
        "--vlm-model",
        default="gpt-4o-mini",
        help="VLM model identifier (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "--vlm-endpoint",
        default="https://api.openai.com/v1/chat/completions",
        help="VLM API endpoint URL.",
    )

    # Generation options
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=15.0,
        help="Classifier-free guidance scale (default: 15.0).",
    )
    parser.add_argument(
        "--steps",
        "--karras-steps",
        type=int,
        dest="karras_steps",
        default=64,
        help="Number of Karras sampling steps (default: 64).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducible generation.",
    )

    # Output options
    parser.add_argument(
        "--format",
        choices=["xyz", "obj", "ply", "stl"],
        default="xyz",
        help="Output file format (default: xyz).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (default: <prompt>.<format>).",
    )
    parser.add_argument(
        "--points",
        type=int,
        help="Maximum number of points for XYZ format (samples if mesh has more).",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Display a 3D visualization of the generated mesh (requires matplotlib).",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Print detailed information about the generated mesh.",
    )

    # Device options
    parser.add_argument(
        "--device",
        choices=["cuda", "cpu", "auto"],
        default="auto",
        help="Device to use for generation (default: auto).",
    )

    args = parser.parse_args()

    # Determine device
    device = None if args.device == "auto" else args.device

    # Initialize components
    try:
        generator = ShapEGenerator(device=device)
        if not generator.is_available():
            print("Error: Shap-E is not installed. Install it with: pip install shap-e", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error initializing generator: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize VLM if requested
    vlm = None
    use_vlm = args.use_vlm or bool(args.image)
    if use_vlm:
        vlm = OpenAIProvider(
            model=args.vlm_model,
            endpoint=args.vlm_endpoint,
        )
        if not vlm.is_available():
            print("Warning: VLM not available (OPENAI_API_KEY not set). Proceeding without VLM enhancement.", file=sys.stderr)
            use_vlm = False

    # Get exporter
    try:
        exporter = get_exporter(args.format, max_points=args.points, seed=args.seed)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create pipeline
    pipeline = ThreeDPipeline(generator=generator, vlm=vlm, exporter=exporter)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        safe_prompt = args.prompt.strip().lower().replace(" ", "_")
        output_path = f"{safe_prompt}{exporter.get_file_extension()}"

    # Generation config
    config = GenerationConfig(
        guidance_scale=args.guidance_scale,
        karras_steps=args.karras_steps,
        seed=args.seed,
    )

    # Generate and export
    try:
        print(f"Generating 3D object from prompt: '{args.prompt}'")
        result = pipeline.generate_and_export(
            prompt=args.prompt,
            output_path=output_path,
            image_path=args.image,
            use_vlm=use_vlm,
            config=config,
        )
        print(f"\n✓ Generated {len(result.vertices)} vertices")
        if result.faces:
            print(f"✓ Generated {len(result.faces)} faces")
        print(f"✓ Saved to: {output_path}")

        # Print info if requested
        if args.info:
            print_mesh_info(result)

        # Visualize if requested
        if args.visualize:
            try:
                visualize_mesh(result, show=True)
            except ImportError:
                print(
                    "Warning: matplotlib not installed. Install with: pip install matplotlib",
                    file=sys.stderr,
                )
    except Exception as e:
        print(f"Error during generation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
