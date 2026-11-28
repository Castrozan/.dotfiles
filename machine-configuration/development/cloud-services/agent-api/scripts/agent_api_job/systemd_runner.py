from agent_api_job.errors import JobError
from agent_api_job.model import MAXIMUM_LOG_CHARACTERS, job_outcome
from agent_api_job.process import run_command

STATUS_PROPERTIES = ("ActiveState", "SubState", "Result", "ExecMainStatus")


def unit_name(job):
    return f"agent-api-{job.identifier}.service"


def job_state(properties):
    if properties["ActiveState"] == "failed":
        return "failed"
    if properties["ActiveState"] == "active" and properties["SubState"] == "exited":
        return "succeeded"
    if properties["ActiveState"] in ("active", "activating", "deactivating"):
        return "running"
    return "unknown"


class SystemdRunner:
    name = "systemd"
    limits_enforced = ["memory_megabytes", "cpu_percent", "runtime_seconds"]

    def start(self, job, limits, command):
        completed = run_command(
            [
                "systemd-run",
                "--user",
                "--quiet",
                f"--unit={unit_name(job)}",
                "--expand-environment=no",
                "--property=RemainAfterExit=yes",
                f"--property=MemoryMax={limits.memory_megabytes}M",
                f"--property=CPUQuota={limits.cpu_percent}%",
                f"--property=RuntimeMaxSec={limits.runtime_seconds}",
                f"--working-directory={job.working_directory}",
                "--",
                *command,
            ]
        )
        if completed.returncode != 0:
            raise JobError("start_failed")

    def status(self, job):
        completed = run_command(
            [
                "systemctl",
                "--user",
                "show",
                unit_name(job),
                *(f"--property={name}" for name in STATUS_PROPERTIES),
            ]
        )
        properties = dict(
            line.split("=", 1) for line in completed.stdout.splitlines() if "=" in line
        )
        if completed.returncode != 0 or set(STATUS_PROPERTIES) - set(properties):
            return job_outcome("unknown")
        state = job_state(properties)
        if state not in ("succeeded", "failed"):
            return job_outcome(state)
        return job_outcome(
            state, int(properties["ExecMainStatus"]), properties["Result"]
        )

    def logs(self, job, lines):
        completed = run_command(
            [
                "journalctl",
                "--user",
                f"--unit={unit_name(job)}",
                "--no-pager",
                "--output=cat",
                f"--lines={lines}",
            ]
        )
        if completed.returncode != 0:
            raise JobError("logs_unavailable")
        return completed.stdout[-MAXIMUM_LOG_CHARACTERS:]

    def cancel(self, job):
        stopped = run_command(["systemctl", "--user", "stop", unit_name(job)])
        run_command(["systemctl", "--user", "reset-failed", unit_name(job)])
        if stopped.returncode != 0:
            raise JobError("job_not_loaded")
