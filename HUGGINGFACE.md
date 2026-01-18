# Hugging Face Model Deployment Guide

This guide explains how to use Hugging Face models for 3D generation in ThreeDLLM.

## Overview

The `HuggingFaceGenerator` supports three deployment modes:

1. **Inference API** (Serverless) - Use HF's managed inference service
2. **Inference Endpoints** - Use dedicated HF endpoints
3. **Local Model** - Self-host the model on your own infrastructure

## Prerequisites

### For Inference API / Endpoints:
```bash
pip install requests
```

### For Local Deployment:
```bash
pip install transformers torch trimesh
```

## Configuration

### Mode 1: Inference API (Easiest)

Use Hugging Face's serverless inference API. Good for testing and low-volume usage.

**Environment Variables:**
```bash
export HF_MODEL_ID="username/model-name"
export HF_API_TOKEN="hf_xxxxxxxxxxxxx"
export GENERATOR_TYPE="huggingface"
```

**Get your API token:**
1. Go to https://huggingface.co/settings/tokens
2. Create a new token with "read" permissions
3. Copy the token

**Example:**
```bash
export HF_MODEL_ID="stabilityai/stable-diffusion-2"
export HF_API_TOKEN="hf_your_token_here"
export GENERATOR_TYPE="huggingface"
```

### Mode 2: Inference Endpoints (Production)

Use dedicated Hugging Face Inference Endpoints for better performance and reliability.

**Step 1: Deploy an Endpoint**

Via Hugging Face UI:
1. Go to your model page on Hugging Face
2. Click "Deploy" → "Inference Endpoints"
3. Configure instance type, region, etc.
4. Copy the endpoint URL

Via Python SDK:
```python
from huggingface_hub import create_inference_endpoint

endpoint = create_inference_endpoint(
    name="my-3d-model-endpoint",
    repository="username/model-name",
    framework="pytorch",
    task="text-to-3d",  # Adjust based on your model
    accelerator="gpu",
    vendor="aws",
    region="us-east-1",
    instance_size="x1",
    instance_type="nvidia-a10g",
)
```

**Step 2: Configure Environment Variables:**
```bash
export HF_ENDPOINT_URL="https://xxxx.us-east-1.aws.endpoints.huggingface.cloud"
export HF_API_TOKEN="hf_xxxxxxxxxxxxx"
export GENERATOR_TYPE="huggingface"
```

### Mode 3: Local Model (Self-Hosted)

Download and run the model locally for full control and privacy.

**Step 1: Download the Model**

```python
from huggingface_hub import snapshot_download

model_path = snapshot_download(
    repo_id="username/model-name",
    local_dir="./models/my-model",
    token="hf_xxxxxxxxxxxxx"  # If private model
)
```

Or use `git`:
```bash
git lfs install
git clone https://huggingface.co/username/model-name ./models/my-model
```

**Step 2: Configure Environment Variables:**
```bash
export HF_LOCAL_MODEL_PATH="./models/my-model"
export HF_DEVICE="cuda"  # or "cpu"
export GENERATOR_TYPE="huggingface"
```

## Usage

### Command Line

```bash
# Using Inference API
HF_MODEL_ID="username/model-name" \
HF_API_TOKEN="hf_xxx" \
GENERATOR_TYPE="huggingface" \
threedllm generate "a red dragon"

# Using Inference Endpoint
HF_ENDPOINT_URL="https://xxx.endpoints.huggingface.cloud" \
HF_API_TOKEN="hf_xxx" \
GENERATOR_TYPE="huggingface" \
threedllm generate "a futuristic car"

# Using Local Model
HF_LOCAL_MODEL_PATH="./models/my-model" \
HF_DEVICE="cuda" \
GENERATOR_TYPE="huggingface" \
threedllm generate "a medieval sword"
```

### Python API

```python
from threedllm.generators import HuggingFaceGenerator, GenerationConfig

# Inference API mode
generator = HuggingFaceGenerator(
    model_id="username/model-name",
    api_token="hf_xxx"
)

# Inference Endpoint mode
generator = HuggingFaceGenerator(
    endpoint_url="https://xxx.endpoints.huggingface.cloud",
    api_token="hf_xxx"
)

# Local model mode
generator = HuggingFaceGenerator(
    local_model_path="./models/my-model",
    device="cuda"
)

# Generate
config = GenerationConfig.quality_preset("balanced")
result = generator.generate("a red dragon", config=config)
```

### Web API

Set the generator parameter to `"huggingface"` or `"hf"`:

```bash
curl -X POST http://localhost:8000/api/generate \
  -F "prompt=a red dragon" \
  -F "generator=huggingface" \
  -F "format=obj"
```

## Customizing for Your Model

The `HuggingFaceGenerator` is designed to work with various 3D generation models, but you may need to customize it based on your model's specific API.

### Customizing Request Format

If your model expects a different request format, modify `_call_inference_api()` or `_call_endpoint()`:

```python
# In threedllm/generators/huggingface.py

def _call_inference_api(self, prompt: str, config: Optional[GenerationConfig] = None) -> dict:
    # Customize payload based on your model
    payload = {
        "inputs": {
            "text": prompt,  # Your model might expect "text" instead of "inputs"
            "num_steps": config.karras_steps if config else 100,
            # Add other model-specific parameters
        }
    }
    # ... rest of the method
```

### Customizing Response Parsing

If your model returns data in a different format, modify `_parse_response_to_mesh()`:

```python
# In threedllm/generators/huggingface.py

def _parse_response_to_mesh(self, response: dict) -> MeshResult:
    # Your model might return data in a different structure
    if "mesh_data" in response:
        vertices = response["mesh_data"]["vertices"]
        faces = response["mesh_data"]["faces"]
        # ... parse accordingly
```

### Customizing Local Model Generation

If you're using a local model, you'll likely need to customize `_generate_local()`:

```python
# In threedllm/generators/huggingface.py

def _generate_local(self, prompt: str, config: Optional[GenerationConfig] = None) -> dict:
    self._load_local_model()
    
    # Customize based on your model's API
    inputs = self._processor(prompt, return_tensors="pt").to(self.device)
    
    # Your model might have a different generation method
    with torch.no_grad():
        outputs = self._model.generate_3d(  # Custom method name
            inputs,
            num_steps=config.karras_steps if config else 100,
            guidance_scale=config.guidance_scale if config else 17.5,
        )
    
    # Process outputs to return mesh data
    return {"vertices": outputs.vertices, "faces": outputs.faces}
```

## Model Response Formats

The generator supports multiple response formats:

1. **Direct mesh data:**
   ```json
   {
     "vertices": [[x, y, z], ...],
     "faces": [[i, j, k], ...],
     "normals": [[nx, ny, nz], ...]
   }
   ```

2. **Base64 encoded file:**
   ```json
   {
     "file": "base64_encoded_3d_file_data"
   }
   ```

3. **URL to file:**
   ```json
   {
     "url": "https://example.com/model.obj"
   }
   ```

4. **Raw bytes:**
   ```json
   {
     "data": "binary_data_here"
   }
   ```

## Troubleshooting

### "Model not available" error

- Check that `HF_MODEL_ID` or `HF_ENDPOINT_URL` or `HF_LOCAL_MODEL_PATH` is set
- For API/Endpoint modes, ensure `HF_API_TOKEN` is set
- Verify the model ID/endpoint URL is correct

### "Failed to parse response" error

- Your model might return data in a different format
- Customize `_parse_response_to_mesh()` for your model's response format
- Check the model's documentation for the expected response structure

### Local model loading fails

- Ensure `transformers` and `torch` are installed
- Check that the model path is correct
- Verify the model files are complete (config.json, model weights, etc.)
- Some models require specific model classes - customize `_load_local_model()`

### CUDA out of memory

- Use a smaller model or reduce batch size
- Set `HF_DEVICE="cpu"` to use CPU (slower but no GPU memory needed)
- Use Inference API/Endpoints instead of local deployment

## Finding 3D Generation Models on Hugging Face

Search for models with tags like:
- `text-to-3d`
- `3d-generation`
- `mesh-generation`
- `point-cloud`

Example search: https://huggingface.co/models?search=text-to-3d

## Next Steps

1. Find a 3D generation model on Hugging Face
2. Choose your deployment mode (API/Endpoint/Local)
3. Configure environment variables
4. Test with a simple prompt
5. Customize the generator code if needed for your specific model

For more information, see the [Hugging Face documentation](https://huggingface.co/docs).
