"""FastAPI application for ThreeDLLM."""

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from threedllm import __version__
from threedllm.api.models import (
    GenerationRequest,
    GenerationResponse,
    HealthResponse,
    TaskStatusResponse,
)
from threedllm.api.tasks import task_manager
from threedllm.generators.base import GenerationConfig
from threedllm.generators.shap_e import ShapEGenerator
from threedllm.pipeline import ThreeDPipeline
from threedllm.vlm.openai import OpenAIProvider

# Initialize FastAPI app
app = FastAPI(
    title="ThreeDLLM API",
    description="REST API for generating 3D objects from text prompts using VLM-enhanced generation",
    version=__version__,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components (lazy loading)
_generator: Optional[ShapEGenerator] = None
_vlm: Optional[OpenAIProvider] = None
_pipeline: Optional[ThreeDPipeline] = None


def get_pipeline() -> ThreeDPipeline:
    """Get or create the pipeline instance."""
    global _generator, _vlm, _pipeline

    if _pipeline is None:
        # Initialize generator
        if _generator is None:
            device = os.environ.get("DEVICE", "auto")
            device = None if device == "auto" else device
            _generator = ShapEGenerator(device=device)
            if not _generator.is_available():
                raise RuntimeError(
                    "Shap-E generator is not available. "
                    "Please ensure shap-e is installed: pip install git+https://github.com/openai/shap-e.git"
                )

        # Initialize VLM
        if _vlm is None:
            _vlm = OpenAIProvider()

        _pipeline = ThreeDPipeline(generator=_generator, vlm=_vlm)

    return _pipeline


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        pipeline = get_pipeline()
        generator_available = pipeline.generator.is_available()
        vlm_available = pipeline.vlm.is_available() if pipeline.vlm else False
    except RuntimeError:
        # Generator not available, but API is still running
        generator_available = False
        vlm_available = False
    
    return HealthResponse(
        status="healthy" if generator_available else "degraded",
        version=__version__,
        generator_available=generator_available,
        vlm_available=vlm_available,
    )


@app.post("/api/generate", response_model=GenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_3d(
    prompt: str = Form(..., description="Text prompt describing the 3D object"),
    use_vlm: bool = Form(True, description="Whether to use VLM for prompt enhancement"),
    guidance_scale: float = Form(15.0, ge=1.0, le=50.0),
    karras_steps: int = Form(64, ge=1, le=256),
    seed: Optional[int] = Form(None),
    format: str = Form("obj", regex="^(xyz|obj|ply|stl)$"),
    max_points: Optional[int] = Form(None, ge=1),
    image: Optional[UploadFile] = File(None, description="Optional image for image-to-3D"),
):
    """
    Generate a 3D object from a text prompt.

    This endpoint accepts form data and returns a task ID for async processing.
    """
    try:
        pipeline = get_pipeline()

        # Handle image upload
        image_path = None
        if image and image.filename and image.size > 0:
            # Save uploaded image to temp file
            suffix = Path(image.filename).suffix if image.filename else ".png"
            content = await image.read()
            if len(content) > 0:  # Ensure file has content
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(content)
                    image_path = tmp.name

        # Create generation config
        config = GenerationConfig(
            guidance_scale=guidance_scale,
            karras_steps=karras_steps,
            seed=seed,
        )

        # Create task
        task_id = await task_manager.create_task(
            prompt=prompt,
            pipeline=pipeline,
            image_path=image_path,
            use_vlm=use_vlm,
            config=config,
            format=format,
            max_points=max_points,
        )

        return GenerationResponse(
            task_id=task_id,
            status="pending",
            message="Generation task created",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/json", response_model=GenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_3d_json(request: GenerationRequest):
    """
    Generate a 3D object from a JSON request.

    This is an alternative endpoint that accepts JSON instead of form data.
    """
    try:
        pipeline = get_pipeline()

        config = GenerationConfig(
            guidance_scale=request.guidance_scale,
            karras_steps=request.karras_steps,
            seed=request.seed,
        )

        task_id = await task_manager.create_task(
            prompt=request.prompt,
            pipeline=pipeline,
            image_path=None,
            use_vlm=request.use_vlm,
            config=config,
            format=request.format,
            max_points=request.max_points,
        )

        return GenerationResponse(
            task_id=task_id,
            status="pending",
            message="Generation task created",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a generation task."""
    status_response = await task_manager.get_task_status(task_id)
    if not status_response:
        raise HTTPException(status_code=404, detail="Task not found")
    return status_response


@app.get("/api/files/{filename}")
async def download_file(filename: str):
    """Download a generated file."""
    file_path = task_manager.output_dir / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Security check: ensure file is in output directory
    try:
        file_path.resolve().relative_to(task_manager.output_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "ThreeDLLM API",
        "version": __version__,
        "endpoints": {
            "health": "/api/health",
            "generate": "/api/generate",
            "generate_json": "/api/generate/json",
            "task_status": "/api/tasks/{task_id}",
            "download": "/api/files/{filename}",
        },
        "docs": "/docs",
    }


# Mount static files LAST so API routes take precedence
# This must be after all route definitions
static_dir = Path(__file__).parent.parent.parent / "frontend"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    # Mount at root last to catch all non-API requests
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
