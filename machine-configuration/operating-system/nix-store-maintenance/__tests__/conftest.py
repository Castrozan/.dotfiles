import os
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(autouse=True)
def restore_process_path_after_each_test():
    original_process_path = os.environ.get("PATH")
    yield
    if original_process_path is None:
        os.environ.pop("PATH", None)
    else:
        os.environ["PATH"] = original_process_path
