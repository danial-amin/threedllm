# threedllm

Generate a downloadable XYZ point cloud from a word by connecting to a multimodal
(VLM) model to expand the prompt, then using Shap-E to create a mesh and sample points.

## Install

```bash
pip install shap-e torch
```

## Usage

Basic text-only generation:

```bash
python word_to_xyz.py "red dragon"
```

Use a VLM to expand the prompt (requires `OPENAI_API_KEY`):

```bash
export OPENAI_API_KEY=YOUR_KEY
python word_to_xyz.py "red dragon" --use-vlm
```

Use an image with the VLM:

```bash
export OPENAI_API_KEY=YOUR_KEY
python word_to_xyz.py "red dragon" --image ./dragon.png
```

Optional controls:

```bash
python word_to_xyz.py "red dragon" \
  --points 3000 \
  --guidance-scale 18 \
  --karras-steps 64 \
  --seed 42 \
  --output dragon.xyz
```

The script generates a mesh from the prompt, samples points from mesh vertices,
and writes an XYZ point cloud (first line is point count, second line is a prompt comment).
