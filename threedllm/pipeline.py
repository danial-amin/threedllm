"""Main pipeline for VLM-enhanced 3D generation."""

from typing import Optional

from threedllm.exporters.base import Exporter3D
from threedllm.exporters.xyz import XYZExporter
from threedllm.generators.base import GenerationConfig, Generator3D, MeshResult
from threedllm.vlm.base import VLMProvider


class ThreeDPipeline:
    """Main pipeline for generating 3D objects from prompts using VLM enhancement."""

    def __init__(
        self,
        generator: Generator3D,
        vlm: Optional[VLMProvider] = None,
        exporter: Optional[Exporter3D] = None,
    ):
        """
        Initialize the pipeline.

        Args:
            generator: 3D generation backend.
            vlm: Optional VLM provider for prompt enhancement.
            exporter: Optional exporter (defaults to XYZExporter).
        """
        self.generator = generator
        self.vlm = vlm
        self.exporter = exporter or XYZExporter()

    def generate(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        use_vlm: bool = True,
        config: Optional[GenerationConfig] = None,
    ) -> MeshResult:
        """
        Generate a 3D mesh from a prompt.

        Args:
            prompt: Input text prompt.
            image_path: Optional image path for VLM enhancement.
            use_vlm: Whether to use VLM for prompt enhancement.
            config: Optional generation configuration.

        Returns:
            MeshResult containing the generated mesh.
        """
        # Enhance prompt with VLM if available
        if use_vlm and self.vlm and self.vlm.is_available():
            if image_path:
                vlm_response = self.vlm.enhance_prompt(prompt, image_path=image_path)
            else:
                vlm_response = self.vlm.enhance_prompt(prompt)
            enhanced_prompt = vlm_response.text
            print(f"VLM enhanced prompt: {enhanced_prompt}")
        else:
            enhanced_prompt = prompt

        # Generate 3D mesh
        result = self.generator.generate(enhanced_prompt, config)
        result.prompt = enhanced_prompt  # Store the actual prompt used

        return result

    def generate_and_export(
        self,
        prompt: str,
        output_path: str,
        image_path: Optional[str] = None,
        use_vlm: bool = True,
        config: Optional[GenerationConfig] = None,
    ) -> MeshResult:
        """
        Generate a 3D mesh and export it to a file.

        Args:
            prompt: Input text prompt.
            output_path: Output file path.
            image_path: Optional image path for VLM enhancement.
            use_vlm: Whether to use VLM for prompt enhancement.
            config: Optional generation configuration.

        Returns:
            MeshResult containing the generated mesh.
        """
        result = self.generate(prompt, image_path, use_vlm, config)
        self.exporter.export(result, output_path)
        return result
