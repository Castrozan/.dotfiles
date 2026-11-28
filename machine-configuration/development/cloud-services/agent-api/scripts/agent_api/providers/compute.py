import json
import shutil
from pathlib import PurePosixPath

from agent_api.catalog import describe
from agent_api.contract import CapabilityError, validate_operation_id
from agent_api.inventory import host, hosts
from agent_api.providers.host_transport import JOB_PROGRAM, run_job
from agent_api.providers.tree_copy import copy_tree

FETCH_ARTIFACT = "fetch.tar"


def submit_limit(inputs, name):
    schema = describe("compute.submit")["input_schema"]["properties"][name]
    return inputs.get(name, schema["default"])


def job_location(entry, inputs):
    if "directory" not in inputs:
        return []
    if entry["transport"] == "local":
        return ["--directory", inputs["directory"]]
    return ["--tree", copy_tree(entry, inputs["directory"])]


def start_arguments(job, entry, inputs):
    return [
        "start",
        job,
        *job_location(entry, inputs),
        "--memory-megabytes",
        str(submit_limit(inputs, "memory_megabytes")),
        "--cpu-percent",
        str(submit_limit(inputs, "cpu_percent")),
        "--runtime-seconds",
        str(submit_limit(inputs, "runtime_seconds")),
        "--",
        *inputs["command"],
    ]


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


def list_hosts(request, directory, operation_id):
    return {"hosts": hosts()}


def submit(request, directory, operation_id):
    entry = host(request.input["host"])
    started = run_job(entry, start_arguments(operation_id, entry, request.input))
    return {
        "job": operation_id,
        "host": entry["name"],
        "runner": started["runner"],
        "limits_enforced": started["limits_enforced"],
    }


def status(request, directory, operation_id):
    job = request.input["job"]
    entry = submitted_host(directory, job)
    answer = run_job(entry, ["status", job])
    return {
        "job": job,
        "host": entry["name"],
        "state": answer["state"],
        "exit_code": answer["exit_code"],
        "result": answer["result"],
    }


def logs(request, directory, operation_id):
    job = request.input["job"]
    entry = submitted_host(directory, job)
    lines = request.input.get(
        "lines",
        describe("compute.logs")["input_schema"]["properties"]["lines"]["default"],
    )
    answer = run_job(entry, ["logs", job, "--lines", str(lines)])
    return {"job": job, "host": entry["name"], "log": answer["log"]}


def cancel(request, directory, operation_id):
    job = request.input["job"]
    entry = submitted_host(directory, job)
    run_job(entry, ["cancel", job])
    return {"job": job, "host": entry["name"], "cancelled": True}


def fetch(request, directory, operation_id):
    job = request.input["job"]
    entry = submitted_host(directory, job)
    artifact = directory / FETCH_ARTIFACT
    with artifact.open("wb") as stream:
        run_job(
            entry, ["send", job, "--", request.input["relative_path"]], stdout=stream
        )
    return {
        "job": job,
        "host": entry["name"],
        "artifact": FETCH_ARTIFACT,
        "size_bytes": artifact.stat().st_size,
    }


OPERATIONS = {
    "compute.hosts": list_hosts,
    "compute.submit": submit,
    "compute.status": status,
    "compute.logs": logs,
    "compute.cancel": cancel,
    "compute.fetch": fetch,
}


class ComputeProvider:
    def preflight(self, request):
        if request.capability != "compute.submit":
            return
        validate_submission(request.input)
        entry = host(request.input["host"])
        if entry["transport"] == "local" and shutil.which(JOB_PROGRAM) is None:
            raise CapabilityError("unsupported_host")

    def execute(self, request, directory, operation_id):
        return OPERATIONS[request.capability](request, directory, operation_id)
