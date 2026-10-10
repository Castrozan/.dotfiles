import json
from urllib.parse import parse_qs, urlsplit

import pytest

from staged_rebuild_support import (
    PRIVATE_PATH,
    SOURCE_PATH,
    read_events,
    write_prepared_request,
)
from test_staged_rebuild import run_staged
from test_staged_sources import prefetch_environment, run_prefetch


@pytest.mark.parametrize("entrypoint_flag", [None, "--flake", "--flake="])
def test_prefetch_preserves_selected_public_worktree_and_committed_revisions(
    managed_rebuild_environment, tmp_path, entrypoint_flag
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    public_directory = tmp_path / "dotfiles-repair"
    public_revision = "b" * 40
    private_revision = "c" * 40
    arguments = [
        "--override-input",
        "dotfiles",
        "github:owner/retired-source",
        "--override-input",
        "dotfiles",
        f"git+file://{public_directory}?rev={public_revision}&submodules=1",
    ]
    if entrypoint_flag:
        private_reference = (
            f"git+file://{tmp_path}/private?rev={private_revision}#chise"
        )
        arguments.extend(
            [entrypoint_flag, private_reference]
            if entrypoint_flag == "--flake"
            else [entrypoint_flag + private_reference]
        )
    completed = run_prefetch(environment, tmp_path, *arguments)
    assert completed.returncode == 0, completed.stderr
    archives = [
        event for event in read_events(tmp_path) if "archive" in event["arguments"]
    ]
    public_reference = urlsplit(archives[0]["arguments"][-1])
    assert public_reference.path == str(public_directory)
    assert parse_qs(public_reference.query) == {
        "rev": [public_revision],
        "submodules": ["1"],
    }
    private_reference = urlsplit(archives[1]["arguments"][-1])
    assert parse_qs(private_reference.query)["rev"] == [
        private_revision if entrypoint_flag else "a" * 40
    ]
    prepared = json.loads((tmp_path / "request.json").read_text())
    assert prepared["arguments"].count("--flake") == 1
    assert prepared["arguments"][2] == f"path:{PRIVATE_PATH}#chise"
    assert prepared["arguments"][-3:] == [
        "--override-input",
        "dotfiles",
        f"path:{SOURCE_PATH}",
    ]
    assert all("git+file:" not in argument for argument in prepared["arguments"])
    revisions = [
        event["arguments"]
        for event in read_events(tmp_path, "git-commands")
        if "rev-parse" in event["arguments"]
    ]
    assert revisions[0][1] == str(public_directory)
    assert revisions[0][-1] == public_revision + "^{commit}"
    activated = run_staged(environment, "switch", tmp_path / "request.json")
    assert activated.returncode == 0, activated.stderr
    assert read_events(tmp_path, "native-events")[-1]["action"] == "switch"


def test_invalid_native_override_syntax_fails_before_source_archive_or_handoff(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    completed = run_prefetch(
        environment,
        tmp_path,
        "--override-input=dotfiles",
        f"git+file://{tmp_path}/dotfiles-repair",
    )
    assert completed.returncode == 2
    assert "expected 2 arguments" in completed.stderr
    assert not read_events(tmp_path)
    assert not (tmp_path / "request.json").exists()


def test_missing_selected_revision_fails_before_source_archive_or_handoff(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    completed = run_prefetch(
        environment,
        tmp_path,
        "--override-input",
        "dotfiles",
        f"git+file://{tmp_path}/dotfiles-repair?rev=missing",
    )
    assert completed.returncode == 1
    assert "revision is not immutable" in completed.stderr
    assert not read_events(tmp_path)
    assert not (tmp_path / "request.json").exists()


def test_remote_public_source_override_is_rejected_before_any_nix_client(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    completed = run_prefetch(
        environment, tmp_path, "--override-input", "dotfiles", "github:owner/repository"
    )
    assert completed.returncode == 1
    assert "local flake" in completed.stderr
    assert not read_events(tmp_path)


def test_public_entrypoint_uses_its_selected_revision_with_one_archive(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    revision = "d" * 40
    completed = run_prefetch(
        environment,
        tmp_path,
        "--flake",
        f"git+file://{tmp_path}/dotfiles?rev={revision}&submodules=1#host",
    )
    assert completed.returncode == 0, completed.stderr
    archives = [
        event for event in read_events(tmp_path) if "archive" in event["arguments"]
    ]
    assert len(archives) == 1
    reference = urlsplit(archives[0]["arguments"][-1])
    assert parse_qs(reference.query)["rev"] == [revision]
    prepared = json.loads((tmp_path / "request.json").read_text())
    assert prepared["arguments"][2] == f"path:{SOURCE_PATH}#host"
    assert PRIVATE_PATH not in prepared["sources"]


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("arguments", ["switch", 7], "arguments are invalid"),
        ("sources", ["invalid"], "immutable store path"),
        (
            "arguments",
            ["switch", "--flake", f"path:{PRIVATE_PATH}#chise", "--override-input"],
            "input override is incomplete",
        ),
        (
            "arguments",
            ["switch", "--flake", "git+file:///private#chise"],
            "source was not prefetched",
        ),
    ],
)
def test_malformed_source_handoff_fails_before_any_privileged_client(
    managed_rebuild_environment, tmp_path, field, value, error
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    request = write_prepared_request(tmp_path)
    prepared = json.loads(request.read_text())
    prepared[field] = value
    request.write_text(json.dumps(prepared))
    completed = run_staged(environment, "switch", request)
    assert completed.returncode == 1
    assert error in completed.stderr
    assert not read_events(tmp_path)
    assert not read_events(tmp_path, "native-events")
