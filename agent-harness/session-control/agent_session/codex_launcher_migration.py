import hashlib
import json
import os
from pathlib import Path
import shlex
import time
from uuid import UUID

from agent_session.codex_migration_processes import (
    inspect_new_processes,
    process_birth,
    require,
    resume_arguments,
)


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
    require(
        str(package.resolve()).startswith("/nix/store/")
        and package.is_file()
        and os.access(package, os.X_OK),
        "declared launcher unavailable",
    )
    lines = [line for line in package.read_text().splitlines() if line.strip()]
    require(
        len(lines) == 2 and lines[0].startswith("#!/nix/store/"),
        "unexpected declared launcher recipe",
    )
    command = shlex.split(lines[1])
    require(
        len(command) == 4 and command[0] == "exec" and command[-1] == "$@",
        "unexpected launcher execution",
    )
    python, script = map(Path, command[1:3])
    require(
        str(python.resolve()).startswith("/nix/store/")
        and python.is_absolute()
        and script.is_absolute()
        and python.is_file()
        and os.access(python, os.X_OK),
        "packaged Python unavailable",
    )
    require(
        script.name == "launch_private_session.py"
        and str(script.resolve().parent).startswith("/nix/store/"),
        "packaged script path mismatch",
    )
    require(set(plan["source_hashes"]) == SOURCE_NAMES, "six source hashes required")
    require(
        {path.name for path in script.parent.glob("*.py")} == SOURCE_NAMES,
        "six packaged sources required",
    )
    for name, expected in plan["source_hashes"].items():
        require(
            hashlib.sha256((script.parent / name).read_bytes()).hexdigest() == expected,
            "packaged source changed: " + name,
        )
    for name in ("upstream_binary", "preferences"):
        require(
            str(Path(plan[name]).resolve()).startswith("/nix/store/")
            and Path(plan[name]).is_file(),
            name + " immutable source unavailable",
        )
    require(
        os.access(plan["upstream_binary"], os.X_OK), "upstream binary is not executable"
    )
    return {
        "package": str(package),
        "python": str(python),
        "launch_script": str(script),
    }


def validate_plan(plan):
    require(
        plan["pane_identifier"] == os.environ.get("HERDR_PANE_ID"),
        "migration must target enclosing pane",
    )
    require(
        not os.environ.get("CLAWDE_AGENT_NAME"), "managed launcher migration refused"
    )
    require(
        str(UUID(plan["thread_identifier"])) == plan["thread_identifier"],
        "exact canonical thread required",
    )
    inherited = os.environ.get("CODEX_THREAD_ID")
    require(
        not inherited or inherited == plan["thread_identifier"],
        "inherited thread mismatch",
    )
    seeded = plan["old_processes"]
    require(
        isinstance(seeded, list) and 0 < len(seeded) <= 256,
        "bounded old process seed required",
    )
    require(
        all(
            type(process.get("pid")) is int
            and process["pid"] > 0
            and type(process.get("start_ticks")) is int
            and process["start_ticks"] > 0
            for process in seeded
        ),
        "invalid old process birth",
    )
    require(
        len({process["pid"] for process in seeded}) == len(seeded),
        "duplicate old process seed",
    )
    require(
        isinstance(plan["continuation"], str) and bool(plan["continuation"].strip()),
        "retained continuation required",
    )


class MigrationJournal:
    def __init__(self, directory, plan):
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700)
        self.index = 0
        self.result = {
            "status": "starting",
            "pane_identifier": plan.get("pane_identifier"),
            "thread_identifier": plan.get("thread_identifier"),
        }
        (self.directory / "old-processes.json").write_text(
            json.dumps(plan.get("old_processes"), indent=2) + "\n"
        )
        self.save()

    def save(self):
        text = json.dumps(self.result, indent=2) + "\n"
        with (self.directory / f"event-{self.index:04d}.json").open("x") as stream:
            stream.write(text)
        self.index += 1
        temporary = self.directory / "result.json.tmp"
        temporary.write_text(text)
        temporary.replace(self.directory / "result.json")

    def phase(self, name):
        self.result["phase"] = name
        self.save()


def wait_for_owned_exit(plan, journal):
    deadline = time.monotonic() + 30.0
    while True:
        remaining = []
        for process in plan["old_processes"]:
            observed = process_birth(process["pid"])
            if (
                observed
                and observed["start_ticks"] == process["start_ticks"]
                and observed["state"] != "Z"
            ):
                remaining.append({**process, "observed": observed})
        journal.result["remaining_old_processes"] = remaining
        if not remaining:
            return
        if time.monotonic() >= deadline:
            raise TimeoutError("owned process births remain after30s")
        time.sleep(min(0.2, deadline - time.monotonic()))


def read_pane_frame(commands, pane_identifier, deadline=None):
    timeout = 3.0 if deadline is None else min(3.0, deadline - time.monotonic())
    require(timeout > 0, "frame readiness deadline expired")
    return commands.run(
        "pane frame",
        [
            "herdr",
            "pane",
            "read",
            pane_identifier,
            "--source",
            "recent-unwrapped",
            "--lines",
            "160",
        ],
        timeout,
    )


def frame_complete(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return (
        bool(lines)
        and any("ask codex to do anything" in line.lower() for line in lines[-4:-1])
        and "context" in lines[-1].lower()
        and "gpt-" in lines[-1].lower()
    )


def replacement_state(plan, commands, package, deadline):
    pane_identifier = plan["pane_identifier"]
    information = commands.herdr(
        "replacement process-info",
        ["pane", "process-info", "--pane", pane_identifier],
        deadline,
    )["process_info"]
    pane = commands.herdr(
        "replacement pane", ["pane", "get", pane_identifier], deadline
    )["pane"]
    require(
        information["pane_id"] == pane_identifier
        and pane["pane_id"] == pane_identifier,
        "replacement pane mismatch",
    )
    session = pane.get("agent_session") or {}
    if session.get("value") is None:
        raise LookupError("recorded resumed thread is not available")
    require(
        session.get("value") == plan["thread_identifier"]
        and session.get("agent") == "codex",
        "resumed thread mismatch",
    )
    state = inspect_new_processes(information, pane, package, plan)
    seeded = {
        process["pid"]: process["start_ticks"] for process in plan["old_processes"]
    }
    require(
        all(
            seeded.get(pid) != state["births"][name]["start_ticks"]
            for name, pid in state["pids"].items()
        ),
        "old birth mistaken for replacement",
    )
    return state


def runtime_signature(state):
    return tuple(
        sorted(
            (name, pid, state["births"][name]["start_ticks"])
            for name, pid in state["pids"].items()
        )
    )


def await_replacement(plan, commands, package, baseline):
    deadline = time.monotonic() + 60.0
    previous = None
    quiet_since = None
    last_reason = "first complete repaint not observed"
    while time.monotonic() < deadline:
        try:
            state = replacement_state(plan, commands, package, deadline)
        except LookupError as error:
            last_reason = str(error)
            time.sleep(min(0.2, max(0.0, deadline - time.monotonic())))
            continue
        frame = read_pane_frame(commands, plan["pane_identifier"], deadline)
        digest = hashlib.sha256(frame.encode()).hexdigest()
        if digest != baseline and frame_complete(frame):
            signature = (digest, runtime_signature(state))
            if signature != previous:
                previous, quiet_since = signature, time.monotonic()
            elif time.monotonic() - quiet_since >= 1.0:
                final = replacement_state(plan, commands, package, deadline)
                require(
                    runtime_signature(final) == runtime_signature(state),
                    "replacement changed before continuation",
                )
                final["frame_digest"] = digest
                return final
        else:
            previous, quiet_since = None, None
        time.sleep(min(0.2, max(0.0, deadline - time.monotonic())))
    raise TimeoutError("replacement not ready within60s: " + last_reason)


def migrate(plan, commands, directory):
    journal = MigrationJournal(directory, plan)
    result = journal.result
    started = time.monotonic()
    try:
        journal.phase("validate-declared-inputs")
        validate_plan(plan)
        validate_configuration(plan)
        validate_rollout(plan)
        package = validate_package(plan)
        result["package"] = package
        journal.phase("await-old-processes")
        wait_for_owned_exit(plan, journal)
        journal.phase("inspect-idle-shell")
        information = commands.herdr(
            "cleared process-info",
            ["pane", "process-info", "--pane", plan["pane_identifier"]],
        )["process_info"]
        require(
            information["pane_id"] == plan["pane_identifier"]
            and information["foreground_process_group_id"] == information["shell_pid"],
            "pane is not its cleared shell",
        )
        baseline = hashlib.sha256(
            read_pane_frame(commands, plan["pane_identifier"]).encode()
        ).hexdigest()
        validate_configuration(plan)
        journal.phase("launch-exact-thread")
        result["launch_attempted"] = True
        journal.save()
        arguments = [
            "herdr",
            "pane",
            "run",
            plan["pane_identifier"],
            "env",
            "CODEX_LAUNCHER_BINARY=" + plan["upstream_binary"],
            "AGENT_INTERACTIVE_PREFERENCES_PATH=" + plan["preferences"],
            plan["launcher"],
            *resume_arguments(plan),
        ]
        commands.run("native pane run", arguments, 30.0)
        journal.phase("await-replacement")
        result["replacement"] = await_replacement(plan, commands, package, baseline)
        journal.phase("submit-continuation")
        result["continuation_attempted"] = True
        journal.save()
        result["continuation"] = commands.send(
            plan["pane_identifier"], plan["continuation"]
        )
        result["status"] = "continuation-submitted"
    except Exception as error:
        result.update(status="failed", error=type(error).__name__ + ": " + str(error))
    finally:
        result["elapsed_seconds"] = time.monotonic() - started
        journal.save()
    return result
