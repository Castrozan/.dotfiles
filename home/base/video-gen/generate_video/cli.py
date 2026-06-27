import argparse
import os
import sys

from .compute import build_generator, select_compute_device, select_torch_dtype
from .models import DEFAULT_MODEL, MODEL_REGISTRY, print_model_registry
from .pipeline import (
    build_video_pipeline,
    generate_video_frames,
    place_pipeline_on_device,
    write_video_file,
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="video-gen",
        description="Generate a video clip from a text prompt using a local open-weight model.",
    )
    parser.add_argument(
        "prompt", nargs="?", help="text description of the clip to generate"
    )
    parser.add_argument(
        "--model",
        choices=sorted(MODEL_REGISTRY.keys()),
        default=DEFAULT_MODEL,
        help=f"open-weight model to run (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output", default="clip.mp4", help="output video path (default: clip.mp4)"
    )
    parser.add_argument(
        "--negative-prompt", default=None, help="things to avoid in the clip"
    )
    parser.add_argument("--width", type=int, default=None, help="frame width in pixels")
    parser.add_argument(
        "--height", type=int, default=None, help="frame height in pixels"
    )
    parser.add_argument(
        "--num-frames", type=int, default=None, help="number of frames to render"
    )
    parser.add_argument("--steps", type=int, default=None, help="denoising steps")
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=None,
        help="classifier-free guidance scale",
    )
    parser.add_argument(
        "--fps", type=int, default=None, help="frames per second of the output video"
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="random seed for reproducibility"
    )
    parser.add_argument(
        "--cpu-offload",
        action="store_true",
        help="offload model layers to host memory between steps to fit tight memory",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "mps", "cuda", "cpu"],
        default="auto",
        help="compute device (default: auto-detect mps, then cuda, then cpu)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="print the available models and exit",
    )
    return parser.parse_args()


def resolve_generation_parameters(model_spec, arguments):
    parameters = dict(model_spec["defaults"])
    overrides = {
        "width": arguments.width,
        "height": arguments.height,
        "num_frames": arguments.num_frames,
        "num_inference_steps": arguments.steps,
        "guidance_scale": arguments.guidance_scale,
        "fps": arguments.fps,
    }
    for key, value in overrides.items():
        if value is not None:
            parameters[key] = value
    return parameters


def main():
    arguments = parse_arguments()

    if arguments.list_models:
        print_model_registry()
        return 0

    if not arguments.prompt:
        print(
            "error: a text prompt is required (or pass --list-models)", file=sys.stderr
        )
        return 2

    model_spec = MODEL_REGISTRY[arguments.model]
    device = select_compute_device(arguments.device)
    torch_dtype = select_torch_dtype(device, model_spec["preferred_dtype"])
    parameters = resolve_generation_parameters(model_spec, arguments)

    print(f"model: {arguments.model} ({model_spec['repository']})")
    print(f"device: {device}  dtype: {torch_dtype}")
    print(
        f"resolution: {parameters['width']}x{parameters['height']}  "
        f"frames: {parameters['num_frames']}  steps: {parameters['num_inference_steps']}"
    )
    print("loading pipeline (first run downloads weights to the Hugging Face cache)...")

    pipeline = build_video_pipeline(model_spec, torch_dtype)
    place_pipeline_on_device(pipeline, device, arguments.cpu_offload)

    generator = build_generator(arguments.seed)

    print("generating frames...")
    frames = generate_video_frames(
        pipeline,
        arguments.prompt,
        arguments.negative_prompt,
        parameters,
        generator,
    )

    output_path = os.path.abspath(arguments.output)
    write_video_file(frames, output_path, parameters["fps"])
    print(f"wrote {len(frames)} frames to {output_path}")
    return 0
