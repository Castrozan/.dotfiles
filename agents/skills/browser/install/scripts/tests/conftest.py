import importlib.machinery
import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent.parent


def import_python_script_by_filename(script_filename):
    script_path = SCRIPTS_DIRECTORY / script_filename
    module_name = script_path.stem.replace("-", "_")
    loader = importlib.machinery.SourceFileLoader(module_name, str(script_path))
    spec = importlib.util.spec_from_loader(module_name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


import_python_script_by_filename("reap-chrome-devtools-mcp-children.py")
