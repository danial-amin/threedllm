# ThreeDLLM

A comprehensive Vision Language Model (VLM) system for generating 3D objects from text prompts and images. ThreeDLLM combines state-of-the-art VLM capabilities with 3D generation models to create high-quality 3D meshes and point clouds.

## Features

- **VLM-Enhanced Prompts**: Automatically enhance text prompts using vision-language models for better 3D generation
- **Image-to-3D**: Generate 3D objects from images using multimodal VLM understanding
- **Multiple Export Formats**: Support for XYZ, OBJ, PLY, and STL formats
- **Modular Architecture**: Extensible design supporting multiple VLM and 3D generation backends
- **Flexible Configuration**: Fine-tune generation parameters (guidance scale, steps, seed, etc.)
- **High-Quality API Generators**: Support for Neural4D, Instant3D, and Hugging Face models for production-ready 3D models

## Architecture

ThreeDLLM is built with a modular, extensible architecture:

```
threedllm/
├── vlm/          # Vision Language Model providers (OpenAI, etc.)
├── generators/   # 3D generation backends (Shap-E, etc.)
├── exporters/    # File format exporters (XYZ, OBJ, PLY, STL)
└── pipeline.py   # Main orchestration pipeline
```

### Components

- **VLM Providers**: Interface for vision-language models (currently OpenAI GPT-4 Vision)
- **3D Generators**: Backends for 3D mesh generation
  - **Shap-E**: Free, open-source (variable quality)
  - **Hugging Face**: Use any 3D generation model from Hugging Face (Inference API, Endpoints, or local)
  - **Neural4D API**: High-quality, fast (~90s) - requires API key
  - **Instant3D API**: Fast generation with PBR textures - requires API key
- **Exporters**: Convert generated meshes to various file formats
- **Pipeline**: Orchestrates the entire generation workflow

## Installation

### Docker (Recommended)

The easiest way to run ThreeDLLM is using Docker:

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Start the container:**
   ```bash
   # CPU-only
   docker-compose up -d

   # GPU support
   docker-compose -f docker-compose.gpu.yml up -d
   ```

3. **Open your browser:**
   Navigate to `http://localhost:8000`

See [DOCKER.md](DOCKER.md) for detailed Docker instructions.

### Manual Installation

**Basic Installation:**

```bash
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
```

### Requirements

- Python 3.8+
- PyTorch (with CUDA support recommended)
- Shap-E (install from GitHub: `pip install git+https://github.com/openai/shap-e.git`)
- FastAPI and Uvicorn (for API server)
- OpenAI API key (for VLM features)

## Usage

### Web Interface (Recommended)

Start the API server:

```bash
python run_server.py
```

Or:

```bash
uvicorn threedllm.api.main:app --reload
```

Then open your browser to:

```
http://localhost:8000
```

The web interface provides:
- Easy-to-use form for generating 3D objects
- Image upload support for image-to-3D
- Real-time progress tracking
- Direct download of generated files

### API Server

The REST API can be used programmatically or integrated into other applications.

**Start the server:**
```bash
python run_server.py
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

See [API.md](API.md) for complete API documentation.

**Example API Request:**
```bash
curl -X POST "http://localhost:8000/api/generate" \
  -F "prompt=red dragon" \
  -F "use_vlm=true" \
  -F "format=obj"
```

### Command Line Interface

The main entry point is the `threedllm` command (or use `python -m threedllm.cli`):

#### Basic Generation

Generate a 3D object from a text prompt:

```bash
threedllm "red dragon"
```

#### With VLM Enhancement

Use a VLM to enhance the prompt for better results:

```bash
export OPENAI_API_KEY=your_key_here
threedllm "red dragon" --use-vlm
```

#### Image-to-3D

Generate 3D objects from images:

```bash
export OPENAI_API_KEY=your_key_here
threedllm "dragon" --image ./dragon.png
```

#### Export Formats

Choose different output formats:

```bash
# OBJ format
threedllm "dragon" --format obj --output dragon.obj

# PLY format
threedllm "dragon" --format ply --output dragon.ply

# STL format (for 3D printing)
threedllm "dragon" --format stl --output dragon.stl
```

#### Advanced Options

Fine-tune generation parameters:

```bash
threedllm "red dragon" \
  --guidance-scale 20 \
  --steps 128 \
  --seed 42 \
  --format obj \
  --output dragon.obj
```

### Python API

Use ThreeDLLM programmatically:

```python
from threedllm.pipeline import ThreeDPipeline
from threedllm.generators.shap_e import ShapEGenerator
from threedllm.vlm.openai import OpenAIProvider
from threedllm.exporters.obj import OBJExporter
from threedllm.generators.base import GenerationConfig

# Initialize components
generator = ShapEGenerator()
vlm = OpenAIProvider()
exporter = OBJExporter()

# Create pipeline
pipeline = ThreeDPipeline(
    generator=generator,
    vlm=vlm,
    exporter=exporter
)

# Generate with VLM enhancement
config = GenerationConfig(
    guidance_scale=15.0,
    karras_steps=64,
    seed=42
)

result = pipeline.generate_and_export(
    prompt="red dragon",
    output_path="dragon.obj",
    use_vlm=True,
    config=config
)

print(f"Generated {len(result.vertices)} vertices")
```

## Command Line Options

```
positional arguments:
  prompt                Text prompt describing the 3D object to generate.

optional arguments:
  --image PATH          Optional image path to use with VLM.
  --use-vlm             Use VLM to enhance the prompt.
  --vlm-model MODEL     VLM model identifier (default: gpt-4o-mini).
  --guidance-scale F    Classifier-free guidance scale (default: 15.0).
  --steps N             Number of Karras sampling steps (default: 64).
  --seed N              Random seed for reproducible generation.
  --format FORMAT       Output format: xyz, obj, ply, stl (default: xyz).
  --output PATH         Output file path.
  --points N            Max points for XYZ format.
  --device DEVICE       Device: cuda, cpu, auto (default: auto).
```

## Output Formats

- **XYZ**: Simple point cloud format (vertices only)
- **OBJ**: Wavefront OBJ format (vertices and faces)
- **PLY**: Polygon File Format (vertices and faces)
- **STL**: Stereolithography format (for 3D printing)

## Using Hugging Face Models

ThreeDLLM supports deploying and using 3D generation models from Hugging Face in three ways:

1. **Inference API** (Serverless) - Use HF's managed inference service
2. **Inference Endpoints** - Use dedicated HF endpoints  
3. **Local Model** - Self-host the model on your infrastructure

### Quick Start

**Inference API Mode:**
```bash
export HF_MODEL_ID="username/model-name"
export HF_API_TOKEN="hf_xxxxxxxxxxxxx"
export GENERATOR_TYPE="huggingface"
```

**Inference Endpoint Mode:**
```bash
export HF_ENDPOINT_URL="https://xxx.endpoints.huggingface.cloud"
export HF_API_TOKEN="hf_xxxxxxxxxxxxx"
export GENERATOR_TYPE="huggingface"
```

**Local Model Mode:**
```bash
export HF_LOCAL_MODEL_PATH="./models/my-model"
export HF_DEVICE="cuda"
export GENERATOR_TYPE="huggingface"
```

See [HUGGINGFACE.md](HUGGINGFACE.md) for detailed setup instructions and customization guide.

## Using High-Quality API Generators

For better quality than Shap-E, you can use API-based generators:

### Neural4D (Recommended for Quality)

1. **Get API key**: Sign up at https://www.neural4d.com/api
2. **Set environment variable**:
   ```bash
   export NEURAL4D_API_KEY="your-api-key"
   export GENERATOR_TYPE=neural4d
   ```
3. **Install trimesh** (for parsing):
   ```bash
   pip install trimesh
   ```

### Instant3D

1. **Get API key**: Sign up at https://instant3d.co
2. **Set environment variable**:
   ```bash
   export INSTANT3D_API_KEY="your-api-key"
   export GENERATOR_TYPE=instant3d
   ```
3. **Install trimesh**:
   ```bash
   pip install trimesh
   ```

See [API_GENERATORS.md](API_GENERATORS.md) for detailed documentation.

## Extending ThreeDLLM

### Adding a New VLM Provider

```python
from threedllm.vlm.base import VLMProvider, VLMResponse

class MyVLMProvider(VLMProvider):
    def enhance_prompt(self, prompt, image_path=None, system_prompt=None):
        # Your implementation
        return VLMResponse(text=enhanced_text, model="my-model")
    
    def is_available(self):
        return True  # Check if provider is configured
```

### Adding a New 3D Generator

```python
from threedllm.generators.base import Generator3D, MeshResult

class MyGenerator(Generator3D):
    def generate(self, prompt, config=None):
        # Your implementation
        return MeshResult(vertices=[...], faces=[...])
    
    def is_available(self):
        return True
```

### Adding a New Exporter

```python
from threedllm.exporters.base import Exporter3D

class MyExporter(Exporter3D):
    def export(self, result, path):
        # Your implementation
    
    def get_file_extension(self):
        return ".myformat"
```

## Development

### Setup Development Environment

```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
