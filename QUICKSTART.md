# ThreeDLLM Quick Start Guide

## Installation

### Option 1: Docker (Recommended)

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start with Docker:**
   ```bash
   # CPU version
   docker-compose up -d
   
   # GPU version (requires nvidia-docker)
   docker-compose -f docker-compose.gpu.yml up -d
   ```

3. **Access the web interface:**
   Open `http://localhost:8000` in your browser

### Option 2: Manual Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install git+https://github.com/openai/shap-e.git
   ```

2. **Set up OpenAI API key (for VLM features):**
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

## Running the Web Interface

1. **Start the server:**
   ```bash
   python run_server.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:8000`

3. **Generate a 3D object:**
   - Enter a prompt (e.g., "red dragon")
   - Optionally upload an image
   - Select output format
   - Click "Generate 3D Object"
   - Wait for generation to complete
   - Download your 3D file!

## Using the API

### Start the server:
```bash
python run_server.py
```

### Example: Generate with cURL

```bash
# Start generation
curl -X POST "http://localhost:8000/api/generate" \
  -F "prompt=red dragon" \
  -F "use_vlm=true" \
  -F "format=obj"

# Response contains task_id
# {"task_id": "...", "status": "pending", ...}

# Check status (replace TASK_ID)
curl "http://localhost:8000/api/tasks/TASK_ID"

# Download result when completed
curl -O "http://localhost:8000/api/files/TASK_ID.obj"
```

### Example: Python Client

```python
import requests
import time

# Start generation
response = requests.post(
    "http://localhost:8000/api/generate",
    data={
        "prompt": "red dragon",
        "use_vlm": True,
        "format": "obj",
    }
)
task = response.json()
task_id = task["task_id"]

# Poll for completion
while True:
    status = requests.get(f"http://localhost:8000/api/tasks/{task_id}").json()
    print(f"Status: {status['status']}, Progress: {status['progress']}")
    
    if status["status"] == "completed":
        # Download
        result = requests.get(status["result_url"])
        with open("dragon.obj", "wb") as f:
            f.write(result.content)
        print("Downloaded dragon.obj")
        break
    elif status["status"] == "failed":
        print(f"Error: {status['error']}")
        break
    
    time.sleep(2)
```

## Using the CLI

```bash
# Basic generation
threedllm "red dragon"

# With VLM enhancement
threedllm "red dragon" --use-vlm

# Export as OBJ
threedllm "red dragon" --format obj --output dragon.obj

# With visualization
threedllm "red dragon" --format obj --visualize
```

## Troubleshooting

### "Shap-E is not installed"
```bash
pip install shap-e
```

### "VLM not available"
Make sure you've set the `OPENAI_API_KEY` environment variable.

### "Generator not available"
Ensure PyTorch and Shap-E are properly installed. For GPU support, install PyTorch with CUDA.

### Port already in use
Change the port in `run_server.py` or use:
```bash
uvicorn threedllm.api.main:app --port 8001
```

## Next Steps

- Read the [API Documentation](API.md) for detailed API reference
- Check [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
- Explore the codebase to extend functionality
