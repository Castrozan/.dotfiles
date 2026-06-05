import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import pytest

MERGE_CHROMIUM_PROFILE_PREFERENCES_SCRIPT_PATH = (
    Path(__file__).parent.parent / "scripts" / "merge-chromium-profile-preferences"
)


def _load_module_from_path(module_name, module_file_path):
    loader = importlib.machinery.SourceFileLoader(module_name, str(module_file_path))
    spec = importlib.util.spec_from_loader(module_name, loader)
    loaded_module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = loaded_module
    spec.loader.exec_module(loaded_module)
    return loaded_module


@pytest.fixture
def merge_chromium_profile_preferences_module():
    return _load_module_from_path(
        "merge_chromium_profile_preferences",
        MERGE_CHROMIUM_PROFILE_PREFERENCES_SCRIPT_PATH,
    )
