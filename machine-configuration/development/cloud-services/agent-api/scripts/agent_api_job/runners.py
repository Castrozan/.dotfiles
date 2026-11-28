import shutil

from agent_api_job.process import run_command
from agent_api_job.supervisor_runner import SupervisorRunner
from agent_api_job.systemd_runner import SystemdRunner

RUNNERS = {runner.name: runner for runner in (SystemdRunner(), SupervisorRunner())}


def user_manager_answers():
    if shutil.which("systemd-run") is None:
        return False
    completed = run_command(["systemctl", "--user", "is-system-running"])
    return completed.stdout.strip() in ("running", "degraded")


def select_runner():
    return RUNNERS["systemd" if user_manager_answers() else "supervisor"]
