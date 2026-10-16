"""Bounded calls through existing A2A/Herdr CLIs and existing SSH aliases."""

from __future__ import annotations

import json
import os
import selectors
import shlex
import signal
import subprocess
import time

from .registry import label

MAX_HOSTS = 4
MAX_OUTPUT_BYTES = 2 * 1024 * 1024


class ObservationError(Exception):
    def __init__(self, kind):
        self.kind = kind
        super().__init__(kind)


def command_argv(host, command):
    if host["transport"] == "local":
        return command
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        "ClearAllForwardings=yes",
        "--",
        host["transport"],
        shlex.join(command),
    ]


def run(host, command, timeout=5):
    """Bound runtime and combined output; never copy raw stderr into the registry."""
    deadline = time.monotonic() + timeout
    try:
        process = subprocess.Popen(
            command_argv(host, command),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as error:
        raise ObservationError("unreachable") from error
    output = {"stdout": bytearray(), "stderr": bytearray()}
    size = 0
    drained = False
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ObservationError("unreachable")
                for key, _ in selector.select(remaining):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    size += len(chunk)
                    if size > MAX_OUTPUT_BYTES:
                        raise ObservationError("failed")
                    output[key.data].extend(chunk)
            process.wait(timeout=max(0.001, deadline - time.monotonic()))
        drained = True
        stdout = output["stdout"].decode("utf-8")
        # Existing CLI has a nonzero exit for a healthy empty directory.
        empty = b"the a2a daemon is running but no pane is hosting an agent right now"
        if (
            command == ["a2a", "list", "--json"]
            and process.returncode == 1
            and bytes(output["stderr"]).strip() == empty
        ):
            return "{}"
        if process.returncode:
            raise ObservationError(
                "unreachable" if process.returncode == 255 else "failed"
            )
        return stdout
    except (UnicodeDecodeError, subprocess.TimeoutExpired) as error:
        raise ObservationError("failed") from error
    finally:
        if not drained or process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait()
        process.stdout.close()
        process.stderr.close()


def refresh(registry, hosts, runner=run, budget=30):
    if not hosts or len(hosts) > MAX_HOSTS or len(set(hosts)) != len(hosts):
        raise ValueError(f"select one to {MAX_HOSTS} distinct confirmed hosts")
    # Validate the complete target set before touching the network.
    targets = [(host, registry.host(host)) for host in hosts]
    deadline = time.monotonic() + budget
    live = []
    for host_id, host in targets:
        try:

            def query(command):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ObservationError("unreachable")
                return json.loads(runner(host, command, timeout=min(5, remaining)))

            directory = query(["a2a", "list", "--json"])
            snapshot = query(["herdr", "api", "snapshot"])
            applied = registry.ingest(
                host_id,
                directory,
                snapshot,
                registry.clock(),
                "a2a list + herdr api snapshot",
                "live",
            )
            if applied:
                live.append(host_id)
        except ObservationError as error:
            registry.failure(host_id, error.kind)
        except (ValueError, TypeError, AttributeError):
            registry.failure(host_id, "failed")
    return live


def dispatch(
    registry, request_id, host, pane, session, owner, task, prompt, runner=run
):
    label(prompt, "single-line prompt")
    arguments = (request_id, host, pane, session, owner, task, prompt)
    if registry.job(request_id):
        return registry.reserve(*arguments)[0]
    if host not in refresh(registry, [host], runner):
        raise ValueError("live preflight failed; no task submitted")
    job, created = registry.reserve(*arguments)
    if not created:
        return job
    try:
        receipt = runner(
            registry.host(host),
            ["a2a", "send", pane, f"{job['correlation']} {prompt}", "--sender", owner],
            timeout=10,
        ).strip()
        label(receipt, "remote task ID")
    except (ObservationError, ValueError):
        # The request may have reached the peer even when the receipt was lost.
        return registry.update_job(
            request_id, "uncertain", blocker="receipt_missing_do_not_retry"
        )
    return registry.update_job(request_id, "dispatched", remote_task_id=receipt)


def result(registry, request_id, runner=run):
    job = registry.job(request_id)
    if job is None:
        raise ValueError("unknown request ID")
    if job["state"] in {"completed", "failed", "canceled", "reported_completed"}:
        return job
    if not job["remote_task_id"]:
        raise ValueError("no receipt; reconcile target evidence manually, never resend")
    host = job["host_id"]
    if host not in refresh(registry, [host], runner):
        return registry.update_job(
            request_id, job["state"], blocker="status_unavailable"
        )
    agent = registry.agent(host, job["pane_id"], job["session_id"])
    if not agent["present"]:
        return registry.update_job(
            request_id, "uncertain", blocker="session_identity_changed"
        )
    try:
        document = json.loads(
            runner(
                registry.host(host),
                ["a2a", "status", job["pane_id"], job["remote_task_id"]],
                timeout=10,
            )
        )
        if (
            not isinstance(document, dict)
            or document.get("id") != job["remote_task_id"]
        ):
            raise ValueError("task identity mismatch")
        states = {
            "submitted": "dispatched",
            "working": "working",
            "input_required": "blocked",
            "completed": "reported_completed",
            "failed": "failed",
            "canceled": "canceled",
        }
        state = states[document["state"]]
    except (ObservationError, ValueError, KeyError, TypeError):
        return registry.update_job(
            request_id, job["state"], blocker="status_unavailable"
        )
    # A2A completion is heuristic; artifacts must still be independently checked.
    blocker = "verify_artifact_and_session" if state == "reported_completed" else None
    if state == "blocked":
        blocker = "peer_requires_input"
    if state == "failed":
        error = document.get("errorMessage")
        blocker = "remote_task_failed"
        if isinstance(error, str) and "composer_occupied_or_unrecognized" in error:
            blocker = "composer_occupied_or_unrecognized"
    return registry.update_job(request_id, state, blocker=blocker)
