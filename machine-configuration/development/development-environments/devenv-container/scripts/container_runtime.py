import json
import os
from pathlib import Path

from container_commands import run_command
from container_configuration import compose_configuration
from container_source_control import shared_git_metadata


class ContainerRuntime:
    def __init__(self, policy):
        self.policy = policy
        self.environment = os.environ.copy()
        if policy.virtual_machine:
            self.environment.pop("DOCKER_CONTEXT", None)
            self.environment.pop("DOCKER_TLS_VERIFY", None)
            self.environment.pop("DOCKER_CERT_PATH", None)
            self.environment["DOCKER_HOST"] = (
                f"unix://{Path.home()}/.colima/{policy.virtual_machine_profile}/docker.sock"
            )

    def run(self, arguments, **options):
        return run_command(
            arguments,
            self.environment,
            **options,
        )

    def machine_running(self):
        if not self.policy.virtual_machine:
            return True
        return (
            self.run(
                ["colima", "status", self.policy.virtual_machine_profile],
                capture=True,
                timeout=10,
                check=False,
            ).returncode
            == 0
        )

    def start_machine(self):
        if self.machine_running():
            self.verify_machine_budget()
            return
        self.run(
            [
                "colima",
                "start",
                self.policy.virtual_machine_profile,
                "--cpus",
                str(self.policy.virtual_machine_cpus),
                "--memory",
                str(self.policy.virtual_machine_memory_gib),
                "--disk",
                str(self.policy.virtual_machine_disk_gib),
                "--vm-type",
                "vz",
                "--mount-type",
                "virtiofs",
                "--mount",
                f"{self.policy.workspace_root}:w",
                "--activate=false",
                "--ssh-config=false",
                "--ssh-agent=false",
            ],
            timeout=600,
        )
        self.verify_machine_budget()

    def verify_machine_budget(self):
        if not self.policy.virtual_machine:
            return
        result = self.run(
            [
                "colima",
                "--profile",
                self.policy.virtual_machine_profile,
                "list",
                "--json",
            ],
            capture=True,
            timeout=10,
        )
        instances = [
            json.loads(line) for line in result.stdout.splitlines() if line.strip()
        ]
        if len(instances) != 1:
            raise ValueError("Cannot verify the development VM's resource budget")
        instance = instances[0]
        if (
            instance["cpus"] > self.policy.virtual_machine_cpus
            or instance["memory"] > self.policy.virtual_machine_memory_gib * 1024**3
        ):
            raise ValueError(
                "The running development VM exceeds its declared budget; stop it before restarting"
            )

    def stop_machine(self):
        if self.policy.virtual_machine and self.machine_running():
            self.run(
                ["colima", "stop", self.policy.virtual_machine_profile], timeout=45
            )

    def compose(self, project, arguments, **options):
        return self.run(
            [
                "docker-compose",
                "--project-name",
                project.name,
                "--file",
                str(project.compose_path),
                *arguments,
            ],
            **options,
        )

    def start_project(self, project):
        metadata = shared_git_metadata(project, self.policy.workspace_root, self.run)
        configuration = json.dumps(
            compose_configuration(self.policy, project, metadata)
        )
        if (
            project.compose_path.exists()
            and project.compose_path.read_text() == configuration
            and self.project_running(project)
        ):
            return
        project.compose_path.write_text(configuration)
        self.compose(project, ["up", "--detach", "--build"], timeout=1200)

    def stop_project(self, project):
        self.compose(project, ["stop", "--timeout", "10"], timeout=30)

    def project_running(self, project):
        result = self.compose(
            project, ["ps", "--status", "running", "--quiet"], capture=True
        )
        return bool(result.stdout.strip())

    def execute(self, project, command, timeout_seconds, interactive=False):
        arguments = ["exec"] + ([] if interactive else ["-T"])
        arguments += [
            "environment",
            "timeout",
            "-k",
            "10",
            str(timeout_seconds + 30),
            "devenv",
            "--max-jobs",
            "1",
            "--cores",
            str(self.policy.container_cpus),
            "--option",
            "packages:pkgs",
            "coreutils python312 curl ripgrep",
            "shell",
            "--",
            "timeout",
            "--kill-after=10s",
        ]
        if interactive:
            arguments.append("--foreground")
        arguments += [str(timeout_seconds), *command]
        return self.compose(
            project,
            arguments,
            timeout=timeout_seconds + 45,
            check=False,
            interactive=interactive,
        ).returncode

    def status(self, project):
        return self.compose(project, ["ps", "--format", "json"], capture=True).stdout
