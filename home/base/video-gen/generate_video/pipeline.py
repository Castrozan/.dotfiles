import av
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
    array = array[:, :, :3]
    height, width = array.shape[:2]
    array = array[: height - (height % 2), : width - (width % 2)]
    return np.ascontiguousarray(array)


def write_video_file(frames, output_path, frames_per_second):
    rgb_frames = [coerce_frame_to_uint8_rgb(frame) for frame in frames]
    height, width = rgb_frames[0].shape[:2]
    container = av.open(output_path, mode="w")
    try:
        stream = container.add_stream("libx264", rate=frames_per_second)
        stream.width = width
        stream.height = height
        stream.pix_fmt = "yuv420p"
        for array in rgb_frames:
            video_frame = av.VideoFrame.from_ndarray(array, format="rgb24")
            for packet in stream.encode(video_frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    finally:
        container.close()
    return len(rgb_frames)
