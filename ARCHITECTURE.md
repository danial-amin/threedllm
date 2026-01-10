# ThreeDLLM Architecture

## Overview

ThreeDLLM is designed as a modular, extensible system for generating 3D objects from text prompts using Vision Language Models (VLMs) and 3D generation models.

## Core Components

### 1. VLM Module (`threedllm/vlm/`)

The VLM module provides interfaces and implementations for Vision Language Model providers.

**Base Interface:**
- `VLMProvider`: Abstract base class defining the interface
- `VLMResponse`: Data class for VLM responses

**Implementations:**
- `OpenAIProvider`: OpenAI GPT-4 Vision integration

**Key Features:**
- Prompt enhancement for better 3D generation
- Image-to-text understanding
- Extensible architecture for adding new providers (Anthropic, local models, etc.)

### 2. Generators Module (`threedllm/generators/`)

The generators module contains 3D mesh generation backends.

**Base Interface:**
- `Generator3D`: Abstract base class for 3D generators
- `GenerationConfig`: Configuration dataclass
- `MeshResult`: Result container with vertices, faces, and metadata

**Implementations:**
- `ShapEGenerator`: Shap-E diffusion model integration

**Key Features:**
- Lazy model loading
- Configurable generation parameters
- Support for multiple devices (CUDA/CPU)

### 3. Exporters Module (`threedllm/exporters/`)

The exporters module handles conversion to various 3D file formats.

**Base Interface:**
- `Exporter3D`: Abstract base class for exporters

**Implementations:**
- `XYZExporter`: Point cloud format
- `OBJExporter`: Wavefront OBJ format
- `PLYExporter`: Polygon File Format
- `STLExporter`: Stereolithography format (for 3D printing)

**Key Features:**
- Format-specific optimizations
- Point sampling for large meshes
- Metadata preservation

### 4. Pipeline (`threedllm/pipeline.py`)

The pipeline orchestrates the entire generation workflow:

1. **Prompt Enhancement**: Uses VLM to enhance user prompts
2. **3D Generation**: Generates mesh using selected backend
3. **Export**: Converts mesh to desired format

**Key Features:**
- Optional VLM enhancement
- Flexible configuration
- Error handling and validation

### 5. CLI (`threedllm/cli.py`)

Command-line interface providing:
- Easy-to-use commands
- Comprehensive options
- Format selection
- Visualization support

### 6. Visualization (`threedllm/visualize.py`)

Utilities for visualizing generated meshes:
- 3D scatter plots
- Mesh information display
- Export to images

## Data Flow

```
User Input (text/image)
    ↓
VLM Provider (optional)
    ↓ Enhanced Prompt
3D Generator
    ↓ MeshResult
Exporter
    ↓ 3D File
Output
```

## Extension Points

### Adding a New VLM Provider

1. Inherit from `VLMProvider`
2. Implement `enhance_prompt()` and `is_available()`
3. Register in `threedllm/vlm/__init__.py`

### Adding a New 3D Generator

1. Inherit from `Generator3D`
2. Implement `generate()` and `is_available()`
3. Return `MeshResult` with vertices and faces
4. Register in `threedllm/generators/__init__.py`

### Adding a New Exporter

1. Inherit from `Exporter3D`
2. Implement `export()` and `get_file_extension()`
3. Register in `threedllm/exporters/__init__.py`

## Design Principles

1. **Modularity**: Each component is independent and replaceable
2. **Extensibility**: Easy to add new providers, generators, and exporters
3. **Type Safety**: Uses type hints throughout
4. **Error Handling**: Graceful degradation when components unavailable
5. **Configuration**: Flexible configuration at multiple levels

## Future Enhancements

- **Additional VLM Providers**: Anthropic Claude, local models (LLaVA, etc.)
- **Additional Generators**: Point-E, other diffusion models
- **Additional Formats**: GLB, USD, FBX
- **Batch Processing**: Generate multiple objects at once
- **API Server**: REST API for programmatic access
- **Web Interface**: Browser-based UI
- **Model Caching**: Persistent model storage
- **Progress Tracking**: Better progress indicators
- **Quality Metrics**: Automatic quality assessment
