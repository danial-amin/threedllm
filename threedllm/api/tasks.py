"""Task management for async 3D generation."""

import asyncio
import uuid
from pathlib import Path
from typing import Dict, Optional

from threedllm.api.models import TaskStatusResponse
from threedllm.exporters.base import Exporter3D
from threedllm.exporters.obj import OBJExporter
from threedllm.exporters.ply import PLYExporter
from threedllm.exporters.stl import STLExporter
from threedllm.exporters.xyz import XYZExporter
from threedllm.generators.base import GenerationConfig, Generator3D
from threedllm.pipeline import ThreeDPipeline
from threedllm.vlm.base import VLMProvider


class TaskManager:
    """Manages async 3D generation tasks."""

    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize task manager.

        Args:
            output_dir: Directory to store generated files.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.tasks: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()

    def _get_exporter(self, format_name: str, max_points: Optional[int] = None, seed: Optional[int] = None) -> Exporter3D:
        """Get exporter by format name."""
        exporters = {
            "xyz": XYZExporter(max_points=max_points, seed=seed),
            "obj": OBJExporter(),
            "ply": PLYExporter(),
            "stl": STLExporter(),
        }
        if format_name not in exporters:
            raise ValueError(f"Unknown format: {format_name}")
        return exporters[format_name]

    async def create_task(
        self,
        prompt: str,
        pipeline: ThreeDPipeline,
        image_path: Optional[str] = None,
        use_vlm: bool = True,
        config: Optional[GenerationConfig] = None,
        format: str = "obj",
        max_points: Optional[int] = None,
    ) -> str:
        """
        Create a new generation task.

        Returns:
            Task ID.
        """
        task_id = str(uuid.uuid4())
        async with self._lock:
            self.tasks[task_id] = {
                "status": "pending",
                "progress": 0.0,
                "message": "Task created",
                "result_path": None,
                "error": None,
            }

        # Start task in background
        asyncio.create_task(
            self._run_task(
                task_id=task_id,
                prompt=prompt,
                pipeline=pipeline,
                image_path=image_path,
                use_vlm=use_vlm,
                config=config,
                format=format,
                max_points=max_points,
            )
        )

        return task_id

    async def _run_task(
        self,
        task_id: str,
        prompt: str,
        pipeline: ThreeDPipeline,
        image_path: Optional[str] = None,
        use_vlm: bool = True,
        config: Optional[GenerationConfig] = None,
        format: str = "obj",
        max_points: Optional[int] = None,
    ):
        """Run a generation task."""
        import traceback
        
        try:
            async with self._lock:
                self.tasks[task_id]["status"] = "processing"
                self.tasks[task_id]["progress"] = 0.05
                self.tasks[task_id]["message"] = "Starting generation..."

            # Step 1: VLM enhancement (if enabled)
            if use_vlm and pipeline.vlm and pipeline.vlm.is_available():
                async with self._lock:
                    self.tasks[task_id]["progress"] = 0.1
                    self.tasks[task_id]["message"] = "Enhancing prompt with VLM..."
                
                # VLM is fast, do it in async
                if image_path:
                    vlm_response = pipeline.vlm.enhance_prompt(prompt, image_path=image_path)
                else:
                    vlm_response = pipeline.vlm.enhance_prompt(prompt)
                enhanced_prompt = vlm_response.text
            else:
                enhanced_prompt = prompt

            async with self._lock:
                self.tasks[task_id]["progress"] = 0.2
                self.tasks[task_id]["message"] = f"Generating 3D mesh... (this may take 2-5 minutes)"

            # Step 2: 3D generation (this is the slow part)
            # Run generation in thread pool (since it's CPU/GPU bound)
            loop = asyncio.get_event_loop()
            
            # Create a wrapper that updates progress
            def generate_with_progress():
                try:
                    # Generate mesh (this is slow - can take 2-5 minutes on CPU)
                    result = pipeline.generator.generate(enhanced_prompt, config)
                    return result
                except Exception as e:
                    # Log full traceback for debugging
                    import sys
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"Generation error: {error_trace}", file=sys.stderr)
                    raise

            result = await loop.run_in_executor(None, generate_with_progress)

            async with self._lock:
                self.tasks[task_id]["progress"] = 0.8
                self.tasks[task_id]["message"] = "Exporting mesh..."

            # Step 3: Export
            exporter = self._get_exporter(format, max_points=max_points, seed=config.seed if config else None)
            output_path = self.output_dir / f"{task_id}.{format}"
            await loop.run_in_executor(
                None,
                lambda: exporter.export(result, str(output_path)),
            )

            async with self._lock:
                self.tasks[task_id]["status"] = "completed"
                self.tasks[task_id]["progress"] = 1.0
                self.tasks[task_id]["message"] = "Generation completed"
                self.tasks[task_id]["result_path"] = str(output_path)

        except Exception as e:
            # Log full error for debugging
            error_trace = traceback.format_exc()
            print(f"Task {task_id} failed: {error_trace}", flush=True)
            
            async with self._lock:
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["error"] = str(e)
                self.tasks[task_id]["message"] = f"Generation failed: {str(e)}"

    async def get_task_status(self, task_id: str) -> Optional[TaskStatusResponse]:
        """Get status of a task."""
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None

            result_url = None
            if task["status"] == "completed" and task["result_path"]:
                filename = Path(task["result_path"]).name
                result_url = f"/api/files/{filename}"

            return TaskStatusResponse(
                task_id=task_id,
                status=task["status"],
                progress=task["progress"],
                message=task["message"],
                result_url=result_url,
                error=task.get("error"),
            )

    def get_result_path(self, task_id: str) -> Optional[Path]:
        """Get the result file path for a completed task."""
        task = self.tasks.get(task_id)
        if task and task["status"] == "completed" and task["result_path"]:
            return Path(task["result_path"])
        return None


# Global task manager instance
task_manager = TaskManager()
