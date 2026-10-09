import json
import subprocess
import sys

from staged_rebuild_support import (
    PRIVATE_PATH,
    SOURCE_PATH,
    SCRIPTS,
    build_staged_environment,
    read_events,
)


def prefetch_environment(managed_environment, directory):
    environment = build_staged_environment(managed_environment, directory)
    environment.pop("GC_INITIAL_HEAP_SIZE", None)
    environment.pop("GC_FREE_SPACE_DIVISOR", None)
    git = directory / "git"
    git.write_text(
        f"""#!{sys.executable}
import json
import os
import sys
from pathlib import Path
with (Path(os.environ["TEST_PHASE_DIRECTORY"]) / "git-commands").open("a") as events:
    events.write(json.dumps({{"arguments": sys.argv[1:]}}) + "\\n")
if "rev-parse" in sys.argv:
    selected_revision = sys.argv[-1].removesuffix("^{{commit}}")
    print("a" * 40 if selected_revision == "HEAD" else selected_revision)
elif "status" in sys.argv:
    print(" M flake.nix" if os.environ.get("TEST_DIRTY_SOURCE") == "1" else "", end="")
else:
    raise SystemExit("unexpected Git mutation")
"""
    )
    git.chmod(0o755)
    return environment


def run_prefetch(environment, directory, *extra_arguments):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "prefetch_rebuild.py"),
            str(directory / "request.json"),
            str(directory / "dotfiles"),
            "switch",
            "--flake",
            f"git+file://{directory}/private#chise",
            *extra_arguments,
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )


def test_user_prefetch_captures_public_inputs_and_private_immutable_root(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    completed = run_prefetch(environment, tmp_path)
    assert completed.returncode == 0, completed.stderr
    request = json.loads((tmp_path / "request.json").read_text())
    assert set(request["sources"]) == {
        PRIVATE_PATH,
        SOURCE_PATH,
        "/nix/store/33333333333333333333333333333333-nested-source",
    }
    assert f"path:{PRIVATE_PATH}#chise" in request["arguments"]
    assert request["arguments"][-3:] == [
        "--override-input",
        "dotfiles",
        f"path:{SOURCE_PATH}",
    ]
    events = read_events(tmp_path)
    assert len(events) == 4
    archives = [event for event in events if "archive" in event["arguments"]]
    assert len(archives) == 2
    assert all("rev=" + "a" * 40 in event["arguments"][-1] for event in archives)
    assert all(event["gc"] == [None, None] for event in events)
    assert "phase=prefetch_public" in completed.stderr
    assert "phase=prefetch_private" in completed.stderr


def test_dirty_source_rejected_before_fetch_or_privilege_handoff(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    environment["TEST_DIRTY_SOURCE"] = "1"
    completed = run_prefetch(environment, tmp_path)
    assert completed.returncode != 0
    assert "dirty" in completed.stderr
    assert not read_events(tmp_path)
    assert not (tmp_path / "request.json").exists()


def test_unsupported_remote_mode_rejected_before_prefetch(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    completed = run_prefetch(environment, tmp_path, "--target-host", "remote")
    assert completed.returncode != 0
    assert "local flake" in completed.stderr
    assert not read_events(tmp_path)


def test_switch_specialisation_preserved_in_prepared_request(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    command = run_prefetch(environment, tmp_path, "--specialisation", "desktop")
    assert command.returncode == 0, command.stderr
    request = json.loads((tmp_path / "request.json").read_text())
    assert "--specialisation" in request["arguments"]


def test_public_sources_stay_gc_rooted_while_private_sources_are_prefetched(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    environment["TEST_REQUIRE_PUBLIC_ROOT"] = "1"
    completed = run_prefetch(environment, tmp_path)
    assert completed.returncode == 0, completed.stderr


def test_ordinary_host_uses_public_immutable_root_and_archived_input_overrides(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "prefetch_rebuild.py"),
            str(tmp_path / "request.json"),
            str(tmp_path / "dotfiles"),
            "boot",
            "--flake",
            f"{tmp_path}/dotfiles?submodules=1#host",
            "--override-input",
            "nested",
            "github:example/input/pinned",
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    request = json.loads((tmp_path / "request.json").read_text())
    assert request["arguments"][2] == f"path:{SOURCE_PATH}#host"
    assert "github:example/input/pinned" not in request["arguments"]
    assert request["arguments"][-1].startswith("path:/nix/store/")
    assert (
        len(
            [
                event
                for event in read_events(tmp_path)
                if "archive" in event["arguments"]
            ]
        )
        == 1
    )
