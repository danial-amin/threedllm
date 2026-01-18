# API-Based 3D Generators

This document describes how to use high-quality API-based 3D generators as alternatives to Shap-E.

## Available Generators

### 1. Neural4D API
- **Quality**: High-fidelity, production-ready models
- **Speed**: ~90 seconds per generation
- **Features**: Text-to-3D, Image-to-3D, 3D-printing-ready
- **Website**: https://www.neural4d.com/api
- **Pricing**: Check their website for current pricing

### 2. Instant3D.co API
- **Quality**: Fast generation with PBR textures
- **Speed**: Minutes per generation
- **Features**: Text-to-3D, Image-to-3D, watertight meshes
- **Website**: https://instant3d.co
- **Pricing**: Check their website for current pricing

## Setup

### 1. Install Dependencies

```bash
pip install trimesh
```

### 2. Get API Keys

#### Neural4D ⚠️ **Requires API Documentation**

**IMPORTANT**: Neural4D does not provide public API documentation. You must obtain the API specification from them.

1. Sign up at https://www.neural4d.com/api
2. Get your API key from the dashboard
3. **Obtain API documentation** by:
   - Checking your developer dashboard (after login) for API docs
   - Contacting support@dreamtech.ai to request API documentation
   - Inspecting network traffic from their web UI (DevTools → Network tab)
4. Once you have the documentation, configure environment variables:
   ```bash
   export NEURAL4D_API_KEY="your-api-key-here"
   # Base URL (default: https://www.neural4d.com/api)
   export NEURAL4D_API_BASE_URL="https://www.neural4d.com/api"
   # Endpoint paths from their API docs (examples below - replace with actual paths)
   export NEURAL4D_GENERATE_ENDPOINT="/v1/generate/text"
   export NEURAL4D_STATUS_ENDPOINT="/v1/tasks/{task_id}"
   ```

**Note**: The endpoint paths above are guesses. You must replace them with the actual paths from Neural4D's API documentation.

#### Instant3D
1. Sign up at https://instant3d.co
2. Get your API key from the dashboard
3. Set environment variable:
   ```bash
   export INSTANT3D_API_KEY="your-api-key-here"
   ```

### 3. Update Configuration

Edit `.env` file:
```bash
# Choose generator: "shap_e", "neural4d", or "instant3d"
GENERATOR_TYPE=neural4d

# API keys
NEURAL4D_API_KEY=your-key-here
# or
INSTANT3D_API_KEY=your-key-here
```

## Usage

### Command Line

```bash
# Use Neural4D
GENERATOR_TYPE=neural4d NEURAL4D_API_KEY=your-key threedllm generate "a red dragon"

# Use Instant3D
GENERATOR_TYPE=instant3d INSTANT3D_API_KEY=your-key threedllm generate "a futuristic car"
```

### Python API

```python
from threedllm.generators import Neural4DGenerator, GenerationConfig

# Initialize generator
generator = Neural4DGenerator(api_key="your-api-key")

# Generate
config = GenerationConfig.quality_preset("high")
result = generator.generate("a detailed medieval sword", config=config)

# Access vertices and faces
print(f"Generated {len(result.vertices)} vertices")
print(f"Generated {len(result.faces)} faces")
```

### REST API

The API automatically uses the generator specified in `GENERATOR_TYPE` environment variable.

```bash
curl -X POST http://localhost:8000/api/generate \
  -F "prompt=a red dragon" \
  -F "quality_preset=high"
```

## Comparison

| Feature | Shap-E | Neural4D | Instant3D |
|---------|--------|----------|-----------|
| Quality | Variable | High | Good |
| Speed | Slow (CPU) | Fast (~90s) | Fast (minutes) |
| Cost | Free | Paid | Paid |
| Setup | Complex | Easy | Easy |
| Text-to-3D | ✅ | ✅ | ✅ |
| Image-to-3D | ✅ | ✅ | ✅ |
| PBR Textures | ❌ | ✅ | ✅ |
| 3D Printing Ready | ❌ | ✅ | ✅ |

## Notes

- API generators require internet connection
- API keys are required (check each service's pricing)
- Some APIs may have rate limits
- Quality is generally much better than Shap-E
- Generated models are production-ready with clean topology

## Troubleshooting

### "Generator not available"
- Check that your API key is set correctly
- Verify the API key is valid and has credits
- Check internet connection

### "Failed to resolve hostname" or DNS errors
- The API endpoint URLs in the code are **template implementations**
- You need to check the actual API documentation from Neural4D/Instant3D for the correct endpoints
- You can override the base URL using environment variables:
  ```bash
  export NEURAL4D_API_BASE_URL="https://actual-api-endpoint.com/v1"
  export INSTANT3D_API_BASE_URL="https://actual-api-endpoint.com/v1"
  ```

### "Generation timed out"
- Some APIs may take longer than expected
- Check the API status page
- Try with a simpler prompt

### "Failed to parse mesh"
- Ensure `trimesh` is installed: `pip install trimesh`
- Check that the API returned a valid 3D file format

## Important Note About API Endpoints

⚠️ **The API endpoint URLs in this code are template implementations based on common API patterns.**

The actual endpoints, request/response formats, and authentication methods may differ. You should:

1. **Check the official API documentation** from Neural4D or Instant3D
2. **Verify the correct base URL** and endpoint paths
3. **Override the base URL** using environment variables if needed:
   - `NEURAL4D_API_BASE_URL` for Neural4D
   - `INSTANT3D_API_BASE_URL` for Instant3D
4. **Update the request/response handling** in the generator classes if the API format differs

The code structure is designed to be easily modifiable once you have the actual API documentation.
