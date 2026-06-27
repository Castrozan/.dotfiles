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


def write_video_file(frames, output_path, frames_per_second):
    from diffusers.utils import export_to_video

    export_to_video(frames, output_path, fps=frames_per_second)
