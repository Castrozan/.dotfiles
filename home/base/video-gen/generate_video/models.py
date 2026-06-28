DEFAULT_MODEL = "ltx"

MODEL_REGISTRY = {
    "ltx": {
        "repository": "Lightricks/LTX-Video",
        "pipeline_class": "LTXPipeline",
        "preferred_dtype": "bfloat16",
        "defaults": {
            "width": 704,
            "height": 480,
            "num_frames": 97,
            "num_inference_steps": 40,
            "guidance_scale": 3.0,
            "fps": 24,
        },
        "description": "Lightricks LTX-Video, fast open T2V, best fit for Apple Silicon",
    },
    "wan": {
        "repository": "Wan-AI/Wan2.1-T2V-1.3B-Diffusers",
        "pipeline_class": "WanPipeline",
        "preferred_dtype": "bfloat16",
        "defaults": {
            "width": 832,
            "height": 480,
            "num_frames": 81,
            "num_inference_steps": 40,
            "guidance_scale": 5.0,
            "fps": 16,
        },
        "description": "Alibaba Wan2.1 1.3B, higher fidelity, heavier download",
    },
    "wan22": {
        "repository": "Wan-AI/Wan2.2-TI2V-5B-Diffusers",
        "pipeline_class": "WanPipeline",
        "preferred_dtype": "bfloat16",
        "defaults": {
            "width": 832,
            "height": 480,
            "num_frames": 49,
            "num_inference_steps": 30,
            "guidance_scale": 5.0,
            "fps": 16,
        },
        "description": "Alibaba Wan2.2 5B, Apache-2.0, unfiltered base, hub of the open NSFW-LoRA ecosystem; heavy (~24GB, use --cpu-offload)",
    },
    "hunyuanvideo": {
        "repository": "hunyuanvideo-community/HunyuanVideo-1.5-Diffusers-480p_t2v",
        "pipeline_class": "HunyuanVideo15Pipeline",
        "preferred_dtype": "bfloat16",
        "defaults": {
            "width": 832,
            "height": 480,
            "num_frames": 49,
            "num_inference_steps": 40,
            "guidance_scale": 7.0,
            "fps": 24,
        },
        "description": "Tencent HunyuanVideo-1.5, highest-quality unfiltered base; needs CUDA or a GGUF/ComfyUI route, its 8.3B transformer OOMs via diffusers on a 24GB Mac; license excludes EU/UK/South Korea",
    },
    "cogvideox": {
        "repository": "THUDM/CogVideoX-2b",
        "pipeline_class": "CogVideoXPipeline",
        "preferred_dtype": "float16",
        "defaults": {
            "width": 720,
            "height": 480,
            "num_frames": 49,
            "num_inference_steps": 50,
            "guidance_scale": 6.0,
            "fps": 8,
        },
        "description": "THUDM CogVideoX 2B, diffusers reference T2V",
    },
    "modelscope": {
        "repository": "damo-vilab/text-to-video-ms-1.7b",
        "pipeline_class": "DiffusionPipeline",
        "preferred_dtype": "float16",
        "defaults": {
            "width": 256,
            "height": 256,
            "num_frames": 16,
            "num_inference_steps": 25,
            "guidance_scale": 9.0,
            "fps": 8,
        },
        "description": "ModelScope 1.7B, small and fast, low fidelity smoke-test model",
    },
}


def print_model_registry():
    for name in sorted(MODEL_REGISTRY.keys()):
        spec = MODEL_REGISTRY[name]
        marker = " (default)" if name == DEFAULT_MODEL else ""
        print(f"{name}{marker}: {spec['description']}")
        print(f"    repository: {spec['repository']}")
