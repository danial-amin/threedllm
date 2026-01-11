"""API request/response models."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    """Request model for 3D generation."""

    prompt: str = Field(..., description="Text prompt describing the 3D object")
    use_vlm: bool = Field(True, description="Whether to use VLM for prompt enhancement")
    guidance_scale: float = Field(17.5, ge=1.0, le=50.0, description="Classifier-free guidance scale (15-20 recommended)")
    karras_steps: int = Field(100, ge=1, le=256, description="Number of Karras sampling steps (100-128 for better quality)")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    format: Literal["xyz", "obj", "ply", "stl"] = Field("obj", description="Output file format")
    max_points: Optional[int] = Field(None, ge=1, description="Maximum points for XYZ format")


class GenerationResponse(BaseModel):
    """Response model for 3D generation."""

    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status: pending, processing, completed, failed")
    message: str = Field(..., description="Status message")


class TaskStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    status: str
    progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Progress (0.0 to 1.0)")
    message: str
    result_url: Optional[str] = Field(None, description="URL to download result when completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    generator_available: bool
    vlm_available: bool
