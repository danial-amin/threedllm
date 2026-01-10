# ThreeDLLM API Documentation

## Overview

The ThreeDLLM API provides a RESTful interface for generating 3D objects from text prompts using VLM-enhanced generation.

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

**GET** `/api/health`

Check the health status of the API and available components.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "generator_available": true,
  "vlm_available": true
}
```

### Generate 3D Object (Form Data)

**POST** `/api/generate`

Generate a 3D object from a text prompt. Accepts form data including optional image upload.

**Request (multipart/form-data):**
- `prompt` (string, required): Text prompt describing the 3D object
- `use_vlm` (boolean, default: true): Whether to use VLM for prompt enhancement
- `guidance_scale` (float, default: 15.0, range: 1.0-50.0): Classifier-free guidance scale
- `karras_steps` (int, default: 64, range: 1-256): Number of Karras sampling steps
- `seed` (int, optional): Random seed for reproducibility
- `format` (string, default: "obj"): Output format - "xyz", "obj", "ply", or "stl"
- `max_points` (int, optional): Maximum points for XYZ format
- `image` (file, optional): Image file for image-to-3D generation

**Response (202 Accepted):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Generation task created"
}
```

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/generate" \
  -F "prompt=red dragon" \
  -F "use_vlm=true" \
  -F "format=obj" \
  -F "guidance_scale=15.0" \
  -F "steps=64"
```

**Example with Image:**
```bash
curl -X POST "http://localhost:8000/api/generate" \
  -F "prompt=dragon" \
  -F "image=@dragon.png" \
  -F "format=obj"
```

### Generate 3D Object (JSON)

**POST** `/api/generate/json`

Alternative endpoint that accepts JSON instead of form data. Does not support image uploads.

**Request Body:**
```json
{
  "prompt": "red dragon",
  "use_vlm": true,
  "guidance_scale": 15.0,
  "karras_steps": 64,
  "seed": 42,
  "format": "obj",
  "max_points": null
}
```

**Response:** Same as `/api/generate`

### Get Task Status

**GET** `/api/tasks/{task_id}`

Get the current status of a generation task.

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 0.5,
  "message": "Generating mesh...",
  "result_url": null,
  "error": null
}
```

**Status Values:**
- `pending`: Task created but not started
- `processing`: Generation in progress
- `completed`: Generation finished successfully
- `failed`: Generation failed

**Example:**
```bash
curl "http://localhost:8000/api/tasks/550e8400-e29b-41d4-a716-446655440000"
```

### Download Result

**GET** `/api/files/{filename}`

Download a generated 3D file. The filename is provided in the `result_url` field of completed tasks.

**Response:** Binary file download

**Example:**
```bash
curl -O "http://localhost:8000/api/files/550e8400-e29b-41d4-a716-446655440000.obj"
```

### API Information

**GET** `/api`

Get information about available API endpoints.

**Response:**
```json
{
  "name": "ThreeDLLM API",
  "version": "0.1.0",
  "endpoints": {
    "health": "/api/health",
    "generate": "/api/generate",
    "generate_json": "/api/generate/json",
    "task_status": "/api/tasks/{task_id}",
    "download": "/api/files/{filename}"
  },
  "docs": "/docs"
}
```

## Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Examples

### Python

```python
import requests

# Start generation
response = requests.post(
    "http://localhost:8000/api/generate",
    data={
        "prompt": "red dragon",
        "use_vlm": True,
        "format": "obj",
        "guidance_scale": 15.0,
    }
)
task = response.json()
task_id = task["task_id"]

# Poll for status
import time
while True:
    status = requests.get(f"http://localhost:8000/api/tasks/{task_id}").json()
    print(f"Status: {status['status']}, Progress: {status['progress']}")
    
    if status["status"] == "completed":
        # Download result
        result = requests.get(status["result_url"])
        with open("dragon.obj", "wb") as f:
            f.write(result.content)
        break
    elif status["status"] == "failed":
        print(f"Error: {status['error']}")
        break
    
    time.sleep(2)
```

### JavaScript

```javascript
// Start generation
const formData = new FormData();
formData.append('prompt', 'red dragon');
formData.append('use_vlm', 'true');
formData.append('format', 'obj');

const response = await fetch('http://localhost:8000/api/generate', {
    method: 'POST',
    body: formData
});

const task = await response.json();
const taskId = task.task_id;

// Poll for status
const pollStatus = async () => {
    const statusResponse = await fetch(`http://localhost:8000/api/tasks/${taskId}`);
    const status = await statusResponse.json();
    
    if (status.status === 'completed') {
        // Download result
        window.location.href = status.result_url;
    } else if (status.status === 'failed') {
        console.error('Generation failed:', status.error);
    } else {
        setTimeout(pollStatus, 2000);
    }
};

pollStatus();
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful request
- `202 Accepted`: Task created (for generation endpoints)
- `404 Not Found`: Task or file not found
- `500 Internal Server Error`: Server error

Error responses include a `detail` field with the error message:

```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

Currently, there is no rate limiting implemented. For production deployments, consider adding rate limiting middleware.

## CORS

The API includes CORS middleware allowing requests from any origin. For production, configure specific allowed origins.

## File Storage

Generated files are stored in the `outputs/` directory by default. Files are named using the task ID and format extension.

## Environment Variables

- `OPENAI_API_KEY`: Required for VLM features
- `DEVICE`: Device for generation ("cuda", "cpu", or "auto")
