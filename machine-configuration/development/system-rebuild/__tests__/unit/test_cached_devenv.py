import importlib
import json
import subprocess
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/nixos-staged-rebuild"
PUBLIC_SOURCE = "/nix/store/00000000000000000000000000000000-public-source"


@pytest.fixture
def cached_devenv(monkeypatch):
    monkeypatch.syspath_prepend(SCRIPTS)
    return importlib.import_module("cached_devenv")


@pytest.fixture
def metadata():
    path = (
        Path(__file__).resolve().parents[3]
        / "development-environments/devenv-cache.json"
    )
    return json.loads(path.read_text())


def install_transport(monkeypatch, module, metadata, responses=None):
    completed = []
    values = {
        "prefetch_devenv_metadata": json.dumps(metadata),
        "prefetch_devenv": metadata.get("storePath"),
        "prefetch_devenv_integrity": metadata.get("narHash"),
        **(responses or {}),
    }

    def execute(phase, arguments, capture_output=False):
        completed.append((phase, arguments, capture_output))
        response = values[phase]
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(module, "run_command", execute)
    return completed


@pytest.mark.parametrize("offline", [False, True])
def test_cached_package_is_rooted_verified_and_never_compiled(
    cached_devenv, metadata, monkeypatch, tmp_path, offline
):
    completed = install_transport(monkeypatch, cached_devenv, metadata)
    root = tmp_path / "devenv"
    result = cached_devenv.prefetch_cached_devenv(
        {"path": PUBLIC_SOURCE}, root, ["--offline"] if offline else []
    )
    assert result == metadata["storePath"]
    assert [phase for phase, *_ in completed] == [
        "prefetch_devenv_metadata",
        "prefetch_devenv",
        "prefetch_devenv_integrity",
    ]
    metadata_arguments = completed[0][1]
    assert metadata_arguments[-1] == (
        f"path:{PUBLIC_SOURCE}#packages.x86_64-linux.devenv.binaryCache"
    )
    fetch_arguments = completed[1][1]
    assert fetch_arguments[fetch_arguments.index("--add-root") + 1] == root
    assert fetch_arguments[fetch_arguments.index("--max-jobs") + 1] == "0"
    assert metadata["publicKey"] in fetch_arguments
    assert metadata["cacheUrl"] in fetch_arguments
    assert ("substitute" in fetch_arguments) is offline
    assert completed[2][1][-1] == result


def test_archived_input_overrides_are_used_for_metadata(
    cached_devenv, metadata, monkeypatch
):
    completed = install_transport(monkeypatch, cached_devenv, metadata)
    source = "/nix/store/11111111111111111111111111111111-devenv-source"
    cached_devenv.read_cached_devenv(
        {"path": PUBLIC_SOURCE, "inputs": {"devenv": {"path": source}}}
    )
    arguments = completed[0][1]
    position = arguments.index("--override-input")
    assert arguments[position + 1 : position + 3] == ["devenv", f"path:{source}"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("storePath", "/tmp/mutable"),
        ("storePath", True),
        ("narHash", "sha256:incorrect"),
        ("cacheUrl", "http://devenv.cachix.org"),
        ("publicKey", ""),
    ],
)
def test_invalid_metadata_stops_before_any_fetch(
    cached_devenv, metadata, monkeypatch, field, value
):
    metadata[field] = value
    completed = install_transport(monkeypatch, cached_devenv, metadata)
    with pytest.raises(ValueError):
        cached_devenv.read_cached_devenv({"path": PUBLIC_SOURCE})
    assert len(completed) == 1


def test_metadata_transport_must_return_an_object(cached_devenv, metadata, monkeypatch):
    completed = install_transport(
        monkeypatch, cached_devenv, metadata, {"prefetch_devenv_metadata": "[]"}
    )
    with pytest.raises(ValueError, match="object"):
        cached_devenv.read_cached_devenv({"path": PUBLIC_SOURCE})
    assert len(completed) == 1


@pytest.mark.parametrize(
    "phase,response",
    [
        ("prefetch_devenv", "/nix/store/11111111111111111111111111111111-wrong"),
        ("prefetch_devenv_integrity", "sha256:" + "0" * 52),
        ("prefetch_devenv", subprocess.CalledProcessError(42, ["nix-store"])),
    ],
)
def test_cache_failure_never_falls_back_to_package_evaluation(
    cached_devenv, metadata, monkeypatch, tmp_path, phase, response
):
    completed = install_transport(
        monkeypatch, cached_devenv, metadata, {phase: response}
    )
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        cached_devenv.prefetch_cached_devenv(
            {"path": PUBLIC_SOURCE}, tmp_path / "root", []
        )
    assert sum("eval" in arguments for _, arguments, _ in completed) == 1
