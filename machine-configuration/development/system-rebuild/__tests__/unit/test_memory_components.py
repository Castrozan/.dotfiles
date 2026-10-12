import importlib
import json
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/nixos-staged-rebuild"


@pytest.mark.parametrize("system,count", [("x86_64-linux", 5), ("aarch64-darwin", 4)])
def test_component_probes_are_serial_offline_and_cannot_build(
    monkeypatch, tmp_path, system, count
):
    monkeypatch.syspath_prepend(SCRIPTS)
    module = importlib.import_module("memory_components")
    calls = []

    def execute(phase, arguments, capture_output):
        calls.append((phase, arguments, capture_output))
        return json.dumps(["derivation"])

    monkeypatch.setattr(module, "run_command", execute)
    records = tmp_path / "records"
    monkeypatch.setenv("REBUILD_MEMORY_RECORDS", str(records))
    public = "git+file:///source?rev=immutable"
    configuration = "path:/nix/store/root#configuration"
    override = ["--override-input", "dependency", "path:/nix/store/dependency"]
    module.measure_components(public, configuration, system, override)
    assert len(calls) == count
    assert calls[0][0] == "component_home_manager_activation"
    assert calls[1][0] == "component_system_package_list"
    assert calls[2][0] == "component_devenv"
    for _, arguments, capture_output in calls:
        assert arguments[:3] == ["timeout", "--kill-after=5s", "600s"]
        assert "--offline" in arguments
        assert "--no-eval-cache" in arguments
        assert arguments[arguments.index("max-jobs") + 1] == "0"
        assert arguments[arguments.index("builders") + 1] == ""
        assert capture_output
    assert "--override-input" in calls[0][1]
    assert "--override-input" not in calls[2][1]
    assert any(public in argument for argument in calls[2][1])
    recorded = [json.loads(line) for line in records.read_text().splitlines()]
    assert recorded[0]["sources"]["public"] == public
    assert all(record["output_count"] == 1 for record in recorded[1:])
