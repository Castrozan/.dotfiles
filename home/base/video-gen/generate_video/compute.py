import torch


def select_compute_device(requested_device):
    if requested_device != "auto":
        return requested_device
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def select_torch_dtype(device, preferred_dtype_name):
    if device == "cpu":
        return torch.float32
    dtype_by_name = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    return dtype_by_name.get(preferred_dtype_name, torch.float16)


def build_generator(seed):
    if seed is None:
        return None
    return torch.Generator(device="cpu").manual_seed(seed)
