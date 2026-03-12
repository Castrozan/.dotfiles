import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HOOKS_DIRECTORY = Path(__file__).resolve().parent.parent


def import_hyphenated_hook_module(hyphenated_name):
    module_path = HOOKS_DIRECTORY / f"{hyphenated_name}.py"
    spec = importlib.util.spec_from_file_location(
        hyphenated_name.replace("-", "_"), module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[hyphenated_name.replace("-", "_")] = module
    spec.loader.exec_module(module)
    return module


import_hyphenated_hook_module("deep-work-recovery")
