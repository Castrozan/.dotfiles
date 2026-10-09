import hashlib
import json
import os
from pathlib import Path
import shlex
import sys
from uuid import UUID

from agent_session.codex_migration_contract import require


SOURCE_NAMES = {
    "launch_private_session.py",
    "profile_connection.py",
    "profile_write_adapter.py",
    "session_server_configuration.py",
    "session_server_diagnostics.py",
    "codex_app_server_client.py",
}


def validate_configuration(plan):
    fingerprints = plan["configuration_sources"]
    require(
        isinstance(fingerprints, dict) and bool(fingerprints),
        "installed configuration fingerprints required",
    )
    for path, expected in fingerprints.items():
        require(Path(path).is_absolute(), "absolute installed configuration required")
        require(
            hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected,
            "installed configuration changed: " + path,
        )


def validate_rollout(plan):
    with Path(plan["rollout"]).open(encoding="utf-8") as stream:
        record = json.loads(stream.readline())
    require(
        record.get("type") == "session_meta"
        and record.get("payload", {}).get("id") == plan["thread_identifier"],
        "saved rollout thread mismatch",
    )


def validate_package(plan):
    package = Path(plan["launcher"])
    _require_store_executable(package, "declared launcher unavailable")
    command = _launcher_command(package)
    python, script = map(Path, command[1:3])
    _validate_package_paths(python, script)
    _validate_package_sources(script, plan["source_hashes"])
    _validate_declared_store_sources(plan)
    return {
        "package": str(package),
        "python": str(python),
        "launch_script": str(script),
    }


def _require_store_executable(path, message):
    require(
        str(path.resolve()).startswith("/nix/store/")
        and path.is_file()
        and os.access(path, os.X_OK),
        message,
    )


def _launcher_command(package):
    lines = [line for line in package.read_text().splitlines() if line.strip()]
    require(
        len(lines) == 2 and lines[0].startswith("#!/nix/store/"),
        "unexpected declared launcher recipe",
    )
    command = shlex.split(lines[1])
    _validate_launcher_execution(command)
    return command


def _validate_launcher_execution(command):
    require(
        len(command) == 4 and command[0] == "exec" and command[-1] == "$@",
        "unexpected launcher execution",
    )


def _validate_package_paths(python, script):
    require(
        python.is_absolute() and script.is_absolute(), "packaged Python unavailable"
    )
    _require_store_executable(python, "packaged Python unavailable")
    require(
        script.name == "launch_private_session.py"
        and str(script.resolve().parent).startswith("/nix/store/"),
        "packaged script path mismatch",
    )


def _validate_package_sources(script, source_hashes):
    require(set(source_hashes) == SOURCE_NAMES, "six source hashes required")
    require(
        {path.name for path in script.parent.glob("*.py")} == SOURCE_NAMES,
        "six packaged sources required",
    )
    for name, expected in source_hashes.items():
        require(
            hashlib.sha256((script.parent / name).read_bytes()).hexdigest() == expected,
            "packaged source changed: " + name,
        )


def _validate_declared_store_sources(plan):
    for name in ("upstream_binary", "preferences"):
        require(
            str(Path(plan[name]).resolve()).startswith("/nix/store/")
            and Path(plan[name]).is_file(),
            name + " immutable source unavailable",
        )
    require(
        os.access(plan["upstream_binary"], os.X_OK), "upstream binary is not executable"
    )


def validate_plan(plan):
    require(sys.platform == "linux", "launcher migration requires Linux procfs")
    require(
        plan["pane_identifier"] == os.environ.get("HERDR_PANE_ID"),
        "migration must target enclosing pane",
    )
    require(
        not os.environ.get("CLAWDE_AGENT_NAME"), "managed launcher migration refused"
    )
    _validate_thread_identity(plan["thread_identifier"])
    _validate_seeded_processes(plan["old_processes"])
    require(
        isinstance(plan["continuation"], str) and bool(plan["continuation"].strip()),
        "retained continuation required",
    )


def _validate_thread_identity(thread_identifier):
    require(
        str(UUID(thread_identifier)) == thread_identifier,
        "exact canonical thread required",
    )
    inherited = os.environ.get("CODEX_THREAD_ID")
    require(
        not inherited or inherited == thread_identifier, "inherited thread mismatch"
    )


def _validate_seeded_processes(seeded):
    require(
        isinstance(seeded, list) and 0 < len(seeded) <= 256,
        "bounded old process seed required",
    )
    require(
        all(_valid_process_birth(process) for process in seeded),
        "invalid old process birth",
    )
    require(
        len({process["pid"] for process in seeded}) == len(seeded),
        "duplicate old process seed",
    )


def _valid_process_birth(process):
    return (
        type(process.get("pid")) is int
        and process["pid"] > 0
        and type(process.get("start_ticks")) is int
        and process["start_ticks"] > 0
    )
