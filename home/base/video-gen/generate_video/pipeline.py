import subprocess

import numpy as np


def build_video_pipeline(model_spec, torch_dtype):
    import diffusers

    pipeline_class = getattr(diffusers, model_spec["pipeline_class"])
    return pipeline_class.from_pretrained(
        model_spec["repository"], torch_dtype=torch_dtype
    )


def apply_inference_memory_savers(pipeline):
    for method_name in (
        "enable_attention_slicing",
        "enable_vae_slicing",
        "enable_vae_tiling",
    ):
        method = getattr(pipeline, method_name, None)
        if callable(method):
            try:
                method()
            except Exception:
                pass


def place_pipeline_on_device(pipeline, device, enable_cpu_offload):
    apply_inference_memory_savers(pipeline)
    if enable_cpu_offload:
        offload = getattr(pipeline, "enable_model_cpu_offload", None)
        if callable(offload):
            try:
                offload(device=device)
                return
            except Exception:
                pass
    pipeline.to(device)


def generate_video_frames(pipeline, prompt, negative_prompt, parameters, generator):
    call_keyword_arguments = {
        "prompt": prompt,
        "width": parameters["width"],
        "height": parameters["height"],
        "num_frames": parameters["num_frames"],
        "num_inference_steps": parameters["num_inference_steps"],
        "guidance_scale": parameters["guidance_scale"],
    }
    if negative_prompt is not None:
        call_keyword_arguments["negative_prompt"] = negative_prompt
    if generator is not None:
        call_keyword_arguments["generator"] = generator
    result = pipeline(**call_keyword_arguments)
    return result.frames[0]


def coerce_frame_to_uint8_rgb(frame):
    array = np.asarray(frame)
    if np.issubdtype(array.dtype, np.floating):
        array = (np.clip(array, 0.0, 1.0) * 255.0).round().astype(np.uint8)
    else:
        array = array.astype(np.uint8)
    if array.ndim == 2:
        array = np.stack([array, array, array], axis=-1)
    return np.ascontiguousarray(array[:, :, :3])


def write_video_file(frames, output_path, frames_per_second):
    rgb_frames = [coerce_frame_to_uint8_rgb(frame) for frame in frames]
    height, width = rgb_frames[0].shape[:2]
    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-framerate",
        str(frames_per_second),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]
    encoder = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
    for frame in rgb_frames:
        encoder.stdin.write(frame.tobytes())
    encoder.stdin.close()
    return_code = encoder.wait()
    if return_code != 0:
        raise RuntimeError(f"ffmpeg exited with status {return_code}")
    return len(rgb_frames)
