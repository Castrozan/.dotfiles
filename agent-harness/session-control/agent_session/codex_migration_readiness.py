import hashlib
import time

from agent_session.codex_migration_contract import require
from agent_session.codex_migration_processes import inspect_new_processes


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
