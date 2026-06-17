import importlib.util
import subprocess
import sys
from pathlib import Path

HOOKS_DIRECTORY = Path(__file__).resolve().parent.parent


def find_hook_module_path(hyphenated_name):
    candidate_module_paths = [
        candidate
        for candidate in HOOKS_DIRECTORY.rglob(f"{hyphenated_name}.py")
        if "tests" not in candidate.parts and "__pycache__" not in candidate.parts
    ]
    if not candidate_module_paths:
        raise FileNotFoundError(f"hook script not found: {hyphenated_name}.py")
    return candidate_module_paths[0]


def import_hyphenated_hook_module(hyphenated_name):
    module_path = find_hook_module_path(hyphenated_name)
    spec = importlib.util.spec_from_file_location(
        hyphenated_name.replace("-", "_"), module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[hyphenated_name.replace("-", "_")] = module
    spec.loader.exec_module(module)
    return module


def run_hook_subprocess(hook_script_path, stdin_text, timeout=5):
    return subprocess.run(
        [sys.executable, str(hook_script_path)],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
