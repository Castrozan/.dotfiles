import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from container_cleanup_watch import ensure_cleanup_running, watch_cleanup
from container_configuration import ContainerPolicy
from container_leases import project_is_idle, project_lock, record_use, runtime_lock
from container_runtime import ContainerRuntime


def saved_projects(policy):
    root = Path(policy.state_root)
    if not root.exists():
        return []
    projects = []
    for state_path in root.glob("*/project.json"):
        try:
            state = json.loads(state_path.read_text())
            project = policy.project_identity(state["directory"])
            if project.state_directory == state_path.parent:
                projects.append(project)
        except (ValueError, OSError, KeyError):
            continue
    return projects


def collect_projects(policy, runtime):
    if not runtime.machine_running():
        return
    running = False
    for project in saved_projects(policy):
        try:
            with project_lock(project, blocking=False):
                with project_lock(project, "clients", blocking=False):
                    if not project.compose_path.exists():
                        continue
                    project_running = runtime.project_running(project)
                    if project_running and project_is_idle(
                        project, policy.idle_timeout_seconds
                    ):
                        runtime.stop_project(project)
                        project_running = False
                    running |= project_running
        except BlockingIOError:
            running = True
    if not running:
        runtime.stop_machine()


def collect(policy, runtime):
    try:
        with runtime_lock(policy, blocking=False):
            collect_projects(policy, runtime)
    except BlockingIOError:
        return


def execute(policy, runtime, project, command, timeout_seconds, interactive):
    with project_lock(project, "clients", exclusive=False):
        with runtime_lock(policy):
            with project_lock(project):
                record_use(project)
                runtime.start_machine()
                running_projects = [
                    other
                    for other in saved_projects(policy)
                    if other.identity != project.identity
                    and other.compose_path.exists()
                    and runtime.project_running(other)
                ]
                if len(running_projects) >= policy.maximum_running_containers:
                    raise ValueError(
                        f"Development resource budget is occupied by {running_projects[0].directory}; stop that environment first"
                    )
                runtime.start_project(project)
        try:
            return runtime.execute(project, command, timeout_seconds, interactive)
        finally:
            with project_lock(project):
                record_use(project)


def main():
    parser = argparse.ArgumentParser(
        description="Run a checkout's devenv inside a bounded, persistent container.",
    )
    commands = parser.add_subparsers(dest="action", required=True)
    for name in ("shell", "exec", "stop", "status"):
        command_parser = commands.add_parser(name)
        command_parser.add_argument("project")
        if name in ("shell", "exec"):
            command_parser.add_argument("--timeout", type=int)
            command_parser.add_argument("command", nargs=argparse.REMAINDER)
    commands.add_parser("collect")
    commands.add_parser("watch")
    arguments = parser.parse_args()
    policy = ContainerPolicy.load(os.environ["DEVENV_CONTAINER_POLICY"])
    runtime = ContainerRuntime(policy)
    if arguments.action == "watch":
        watch_cleanup(policy)
        return 0
    if arguments.action == "collect":
        collect(policy, runtime)
        return 0
    project = policy.project(arguments.project)
    if arguments.action == "status":
        if not runtime.machine_running() or not project.compose_path.exists():
            print("stopped")
            return 0
        print(runtime.status(project))
        return 0
    if arguments.action == "stop":
        with runtime_lock(policy):
            with project_lock(project):
                with project_lock(project, "clients", blocking=False):
                    if runtime.machine_running() and project.compose_path.exists():
                        runtime.stop_project(project)
        collect(policy, runtime)
        return 0
    interactive = arguments.action == "shell" and sys.stdin.isatty()
    timeout_seconds = (
        arguments.timeout
        if arguments.timeout is not None
        else (
            policy.session_timeout_seconds
            if arguments.action == "shell"
            else policy.command_timeout_seconds
        )
    )
    if not 0 < timeout_seconds <= policy.session_timeout_seconds:
        parser.error(
            f"timeout must be between 1 and {policy.session_timeout_seconds} seconds"
        )
    command = arguments.command
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        if arguments.action == "exec":
            parser.error("exec requires a command after --")
        command = ["bash", "--noprofile", "--norc", "-i"]
    ensure_cleanup_running(policy)
    return execute(policy, runtime, project, command, timeout_seconds, interactive)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"devenv-container: {error}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
