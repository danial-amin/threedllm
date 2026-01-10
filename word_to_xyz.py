#!/usr/bin/env python3
"""Generate a 3D point cloud from a word using a VLM-enhanced Shap-E pipeline.

This script optionally calls a multimodal model to expand the prompt (and optionally
uses an image) before generating a mesh with Shap-E and exporting sampled XYZ points.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import urllib.request
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import torch
from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
from shap_e.diffusion.sample import sample_latents
from shap_e.models.download import load_config, load_model
from shap_e.util.notebooks import decode_latent_mesh

Point = Tuple[float, float, float]


@dataclass(frozen=True)
class GenerationResult:
    prompt: str
    points: List[Point]


def build_output_path(word: str, output: str | None) -> str:
    if output:
        return output
    filename = f"{word.strip().lower().replace(' ', '_')}.xyz"
    return os.path.join(os.getcwd(), filename)


def write_xyz(path: str, prompt: str, points: Sequence[Point]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"{len(points)}\n")
        handle.write(f"prompt={prompt}\n")
        for x, y, z in points:
            handle.write(f"{x:.6f} {y:.6f} {z:.6f}\n")


def sample_points(vertices: Iterable[Point], count: int, seed: int | None) -> List[Point]:
    verts = list(vertices)
    if not verts:
        raise ValueError("No vertices available to sample from the mesh.")
    rng = random.Random(seed)
    if count <= 0:
        raise ValueError("--points must be a positive integer")
    if count >= len(verts):
        return verts
    return rng.sample(verts, count)


def build_vlm_request(prompt: str, image_path: str | None) -> dict:
    content = [{"type": "input_text", "text": prompt}]
    if image_path:
        with open(image_path, "rb") as image_handle:
            encoded = base64.b64encode(image_handle.read()).decode("utf-8")
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:image/png;base64,{encoded}",
            }
        )
    return {
        "model": "gpt-4o-mini",
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Create a concise 3D-friendly prompt describing a single object. "
                            "Emphasize shape and material, avoid scenes."
                        ),
                    },
                    *content,
                ],
            }
        ],
        "max_output_tokens": 200,
    }


def call_vlm(
    prompt: str,
    image_path: str | None,
    api_key: str,
    endpoint: str,
    model: str,
) -> str:
    payload = build_vlm_request(prompt, image_path)
    payload["model"] = model
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode("utf-8"))
    output_text = data.get("output_text")
    if output_text:
        return output_text.strip()
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return content.get("text", "").strip()
    raise RuntimeError("No output_text found in VLM response.")


def generate_mesh_vertices(
    prompt: str,
    guidance_scale: float,
    karras_steps: int,
    seed: int | None,
) -> List[Point]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if seed is not None:
        torch.manual_seed(seed)

    text_model = load_model("text300M", device)
    decoder_model = load_model("decoder", device)
    diffusion = diffusion_from_config(load_config("diffusion"))

    latents = sample_latents(
        batch_size=1,
        model=text_model,
        diffusion=diffusion,
        guidance_scale=guidance_scale,
        model_kwargs={"texts": [prompt]},
        progress=True,
        clip_denoised=True,
        use_fp16=device.type == "cuda",
        use_karras=True,
        karras_steps=karras_steps,
    )

    mesh = decode_latent_mesh(decoder_model, latents[0]).tri_mesh()
    vertices = mesh.vertices
    return [(float(x), float(y), float(z)) for x, y, z in vertices]


def build_point_cloud(
    prompt: str,
    point_count: int,
    guidance_scale: float,
    karras_steps: int,
    seed: int | None,
) -> GenerationResult:
    vertices = generate_mesh_vertices(prompt, guidance_scale, karras_steps, seed)
    points = sample_points(vertices, point_count, seed)
    return GenerationResult(prompt=prompt, points=points)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a 3D point cloud from a word using VLM + Shap-E."
    )
    parser.add_argument("word", help="Word or short phrase to generate.")
    parser.add_argument(
        "--points",
        type=int,
        default=2048,
        help="Number of points to sample for the XYZ file.",
    )
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=15.0,
        help="Classifier-free guidance scale for Shap-E.",
    )
    parser.add_argument(
        "--karras-steps",
        type=int,
        default=64,
        help="Number of Karras sampling steps.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional RNG seed for deterministic generation.",
    )
    parser.add_argument(
        "--output",
        help="Output path for the XYZ file (defaults to <word>.xyz).",
    )
    parser.add_argument(
        "--image",
        help="Optional image path to send to the multimodal model.",
    )
    parser.add_argument(
        "--use-vlm",
        action="store_true",
        help="Use a multimodal model to expand the prompt before 3D generation.",
    )
    parser.add_argument(
        "--vlm-model",
        default="gpt-4o-mini",
        help="Multimodal model identifier (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "--vlm-endpoint",
        default="https://api.openai.com/v1/responses",
        help="VLM endpoint for the Responses API.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prompt = args.word.strip()
    use_vlm = args.use_vlm or bool(args.image)
    if use_vlm:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit("OPENAI_API_KEY is required when using --use-vlm or --image")
        prompt = call_vlm(
            prompt=prompt,
            image_path=args.image,
            api_key=api_key,
            endpoint=args.vlm_endpoint,
            model=args.vlm_model,
        )
        print(f"VLM prompt: {prompt}")
    result = build_point_cloud(
        prompt,
        point_count=args.points,
        guidance_scale=args.guidance_scale,
        karras_steps=args.karras_steps,
        seed=args.seed,
    )
    output_path = build_output_path(args.word, args.output)
    write_xyz(output_path, result.prompt, result.points)
    print(f"Generated {len(result.points)} points for '{result.prompt}'.")
    print(f"Saved XYZ file to: {output_path}")


if __name__ == "__main__":
    main()
