import importlib.machinery
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIRECTORY = Path(__file__).resolve().parent.parent
MEMORY_WRITE_SCRIPT_PATH = SCRIPTS_DIRECTORY / "memory-write"


def import_extensionless_python_script(extensionless_name):
    script_path = SCRIPTS_DIRECTORY / extensionless_name
    module_name = extensionless_name.replace("-", "_")
    loader = importlib.machinery.SourceFileLoader(module_name, str(script_path))
    spec = importlib.util.spec_from_loader(module_name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


import_extensionless_python_script("memory-write")
import_extensionless_python_script("memory-prune")


@pytest.fixture
def isolated_environment(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    return fake_home, workspace


@pytest.fixture
def expected_memory_directory():
    def resolve(fake_home: Path, workspace: Path) -> Path:
        encoded = str(workspace).replace("/", "-").replace(".", "-")
        return fake_home / ".claude" / "projects" / encoded / "memory"

    return resolve


@pytest.fixture
def invoke_memory_write():
    def invoke(workspace: Path, **arguments) -> subprocess.CompletedProcess:
        command = [sys.executable, str(MEMORY_WRITE_SCRIPT_PATH)]
        for key, value in arguments.items():
            if value is None:
                continue
            command.extend([f"--{key.replace('_', '-')}", value])
        return subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=5,
        )

    return invoke
