import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

specification = importlib.util.spec_from_file_location(
    "opencli_fixture",
    Path(__file__).resolve().parents[4] / "__tests__/e2e/opencli_fixture.py",
)
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)


def test_darwin_inspection_finds_owned_backends_and_keeps_other_browsers(monkeypatch):
    processes = "\n".join(
        [
            "101 /Applications/Google Chrome.app/Contents/MacOS/Google Chrome --user-data-dir=/Users/example/.config/chrome-global",
            "102 /nix/store/browser/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing --user-data-dir=/tmp/trial/opencli/profiles/acceptance",
            "103 /nix/store/node/bin/node /nix/store/runtime/lib/opencli/node_modules/@jackwener/opencli/dist/src/daemon.js",
            "104 /nix/store/python/bin/python3 prove_opencli.py",
        ]
    )
    inspect = Mock(return_value=SimpleNamespace(stdout=processes))
    monkeypatch.setattr(module, "sys", SimpleNamespace(platform="darwin"))
    monkeypatch.setattr(module.subprocess, "run", inspect)
    assert module.owned_processes() == [102, 103]
    inspect.assert_called_once_with(
        ["/bin/ps", "-axww", "-o", "pid=,command="],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )


def test_darwin_inspection_failure_never_reports_clean(monkeypatch):
    monkeypatch.setattr(module, "sys", SimpleNamespace(platform="darwin"))
    monkeypatch.setattr(
        module.subprocess,
        "run",
        Mock(side_effect=subprocess.CalledProcessError(1, ["/bin/ps"])),
    )
    with pytest.raises(subprocess.CalledProcessError):
        module.clean()
