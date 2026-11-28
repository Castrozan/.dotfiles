import json
import shutil
from pathlib import PurePosixPath

from agent_api.catalog import describe
from agent_api.contract import CapabilityError, validate_operation_id
from agent_api.inventory import host, hosts
from agent_api.providers.host_transport import run_on_host

MAXIMUM_LOG_CHARACTERS = 1024 * 1024
STATUS_PROPERTIES = ("LoadState", "ActiveState", "SubState", "Result", "ExecMainStatus")


def unit_name(job):
    return f"agent-api-{job}.service"


def submit_limit(inputs, name):
    schema = describe("compute.submit")["input_schema"]["properties"][name]
    return inputs.get(name, schema["default"])


def submit_arguments(job, inputs):
    arguments = [
        "systemd-run",
        "--user",
        "--quiet",
        f"--unit={unit_name(job)}",
        "--expand-environment=no",
        "--property=RemainAfterExit=yes",
        f"--property=MemoryMax={submit_limit(inputs, 'memory_megabytes')}M",
        f"--property=CPUQuota={submit_limit(inputs, 'cpu_percent')}%",
        f"--property=RuntimeMaxSec={submit_limit(inputs, 'runtime_seconds')}",
    ]
    if "directory" in inputs:
        arguments.append(f"--working-directory={inputs['directory']}")
    return [*arguments, "--", *inputs["command"]]


def validate_submission(inputs):
    directory = inputs.get("directory", "/")
    valid = (
        all("\x00" not in value for value in (*inputs["command"], directory)),
        PurePosixPath(directory).is_absolute(),
    )
    if not all(valid):
        raise CapabilityError("invalid_input")


def submitted_host(directory, job):
    validate_operation_id(job)
    try:
        envelope = json.loads((directory.parent / job / "request.json").read_bytes())
    except FileNotFoundError:
        raise CapabilityError("job_not_found") from None
    if envelope["request"]["capability"] != "compute.submit":
        raise CapabilityError("job_not_found")
    return host(envelope["request"]["input"]["host"])


def job_state(properties):
    if properties["ActiveState"] == "failed":
        return "failed"
    if properties["ActiveState"] == "active" and properties["SubState"] == "exited":
        return "succeeded"
    if properties["ActiveState"] in ("active", "activating", "deactivating"):
        return "running"
    return "unknown"


def list_hosts(request, directory, operation_id):
    return {"hosts": hosts()}


def submit(request, directory, operation_id):
    entry = host(request.input["host"])
    completed = run_on_host(entry, submit_arguments(operation_id, request.input))
    if completed.returncode != 0:
        raise CapabilityError("submission_failed")
    return {
        "job": operation_id,
        "host": entry["name"],
        "unit": unit_name(operation_id),
    }


def status(request, directory, operation_id):
    job = request.input["job"]
    entry = submitted_host(directory, job)
    completed = run_on_host(
        entry,
        [
            "systemctl",
            "--user",
            "show",
            unit_name(job),
            *(f"--property={name}" for name in STATUS_PROPERTIES),
        ],
    )
    properties = dict(
        line.split("=", 1) for line in completed.stdout.splitlines() if "=" in line
    )
    if completed.returncode != 0 or set(STATUS_PROPERTIES) - set(properties):
        raise CapabilityError("status_unavailable")
    state = job_state(properties)
    finished = state in ("succeeded", "failed")
    return {
        "job": job,
        "host": entry["name"],
        "state": state,
        "exit_code": int(properties["ExecMainStatus"]) if finished else None,
        "result": properties["Result"] if finished else None,
    }


def logs(request, directory, operation_id):
    job = request.input["job"]
    entry = submitted_host(directory, job)
    lines = request.input.get(
        "lines",
        describe("compute.logs")["input_schema"]["properties"]["lines"]["default"],
    )
    completed = run_on_host(
        entry,
        [
            "journalctl",
            "--user",
            f"--unit={unit_name(job)}",
            "--no-pager",
            "--output=cat",
            f"--lines={lines}",
        ],
    )
    if completed.returncode != 0:
        raise CapabilityError("logs_unavailable")
    return {
        "job": job,
        "host": entry["name"],
        "log": completed.stdout[-MAXIMUM_LOG_CHARACTERS:],
    }


def cancel(request, directory, operation_id):
    job = request.input["job"]
    entry = submitted_host(directory, job)
    stopped = run_on_host(entry, ["systemctl", "--user", "stop", unit_name(job)])
    run_on_host(entry, ["systemctl", "--user", "reset-failed", unit_name(job)])
    if stopped.returncode != 0:
        raise CapabilityError("job_not_loaded")
    return {"job": job, "host": entry["name"], "cancelled": True}


OPERATIONS = {
    "compute.hosts": list_hosts,
    "compute.submit": submit,
    "compute.status": status,
    "compute.logs": logs,
    "compute.cancel": cancel,
}


class ComputeProvider:
    def preflight(self, request):
        if request.capability != "compute.submit":
            return
        validate_submission(request.input)
        entry = host(request.input["host"])
        if entry["transport"] == "local" and shutil.which("systemd-run") is None:
            raise CapabilityError("unsupported_host")

    def execute(self, request, directory, operation_id):
        return OPERATIONS[request.capability](request, directory, operation_id)
