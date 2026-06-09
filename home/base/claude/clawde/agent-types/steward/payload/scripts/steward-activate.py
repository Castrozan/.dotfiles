import argparse
import json
import os
import re
import shutil
import subprocess
import sys

ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
HEALTH_PASS_MARKER = "✓"
HEALTH_FAIL_MARKER = "✗"
ACTIVATION_UNIT_NAME = "steward-activation"
ACTIVATION_RESULT_FILENAME = "activation-result.json"
LAST_ACTIVATED_REVISION_FILENAME = "last-activated-sha"


def strip_ansi_color_codes(text):
    return ANSI_ESCAPE_PATTERN.sub("", text)


def parse_health_check_results(health_check_output):
    results = {}
    for raw_line in health_check_output.splitlines():
        line = strip_ansi_color_codes(raw_line).strip()
        if line.startswith(HEALTH_PASS_MARKER):
            results[line[len(HEALTH_PASS_MARKER) :].strip()] = True
        elif line.startswith(HEALTH_FAIL_MARKER):
            results[line[len(HEALTH_FAIL_MARKER) :].strip()] = False
    return results


def compute_activation_regressions(health_before, health_after):
    return sorted(
        label
        for label, passed_before in health_before.items()
        if passed_before and health_after.get(label) is False
    )


def run_command(command_argv):
    completed = subprocess.run(command_argv, capture_output=True, text=True)
    return completed.returncode, completed.stdout + completed.stderr


def run_health_check():
    return run_command(["health-check"])


def run_activating_switch():
    return run_command(["rebuild"])


def machine_runs_nixos():
    return os.path.exists("/etc/NIXOS")


def roll_back_to_previous_generation():
    return run_command(["sudo", "nixos-rebuild", "switch", "--rollback"])


def current_checkout_revision(repository_directory):
    exit_code, output = run_command(
        ["git", "-C", repository_directory, "rev-parse", "HEAD"]
    )
    return output.strip() if exit_code == 0 else None


def write_state_file(state_directory, filename, content):
    os.makedirs(state_directory, exist_ok=True)
    with open(os.path.join(state_directory, filename), "w") as state_file:
        state_file.write(content)


def record_activation_result(state_directory, result):
    write_state_file(
        state_directory,
        ACTIVATION_RESULT_FILENAME,
        json.dumps(result, indent=2, sort_keys=True),
    )


def activation_unit_is_running():
    exit_code, output = run_command(
        ["systemctl", "--user", "is-active", f"{ACTIVATION_UNIT_NAME}.service"]
    )
    return output.strip() == "active"


def launch_detached_activation_worker(state_directory):
    if activation_unit_is_running():
        return 1, "an activation is already in progress"
    worker_argv = [
        "systemd-run",
        "--user",
        "--collect",
        f"--unit={ACTIVATION_UNIT_NAME}",
        f"--setenv=PATH={os.environ.get('PATH', '')}",
        sys.executable,
        os.path.abspath(__file__),
        "--detached-worker",
        f"--state-dir={state_directory}",
    ]
    return run_command(worker_argv)


def run_activation_worker(state_directory, repository_directory):
    target_revision = current_checkout_revision(repository_directory)
    _, health_before_output = run_health_check()
    health_before = parse_health_check_results(health_before_output)
    write_state_file(state_directory, "pre-activation-health.txt", health_before_output)

    switch_exit_code, switch_output = run_activating_switch()
    write_state_file(state_directory, "activation-switch.txt", switch_output)

    if switch_exit_code != 0:
        record_activation_result(
            state_directory,
            {
                "status": "switch_failed",
                "target_revision": target_revision,
                "switch_exit_code": switch_exit_code,
            },
        )
        return switch_exit_code

    _, health_after_output = run_health_check()
    health_after = parse_health_check_results(health_after_output)
    write_state_file(state_directory, "post-activation-health.txt", health_after_output)
    regressions = compute_activation_regressions(health_before, health_after)

    if regressions:
        rollback_exit_code, rollback_output = (
            roll_back_to_previous_generation()
            if machine_runs_nixos()
            else (None, "automatic rollback unavailable off NixOS")
        )
        write_state_file(state_directory, "activation-rollback.txt", rollback_output)
        record_activation_result(
            state_directory,
            {
                "status": "rolled_back" if machine_runs_nixos() else "regressed",
                "target_revision": target_revision,
                "regressions": regressions,
                "rollback_exit_code": rollback_exit_code,
            },
        )
        return 1

    if target_revision:
        write_state_file(
            state_directory, LAST_ACTIVATED_REVISION_FILENAME, target_revision
        )
    record_activation_result(
        state_directory,
        {"status": "activated", "target_revision": target_revision},
    )
    return 0


def resolve_repository_directory():
    return os.environ.get("STEWARD_REPOSITORY", os.path.expanduser("~/.dotfiles"))


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="steward-activate",
        description="Activate the validated-green dotfiles revision on this machine, "
        "detached so the switch's service restart cannot abandon it, then health-check "
        "the result and roll back any regression.",
    )
    parser.add_argument("--detached-worker", action="store_true")
    parser.add_argument("--state-dir", required=True)
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    repository_directory = resolve_repository_directory()
    if arguments.detached_worker:
        sys.exit(run_activation_worker(arguments.state_dir, repository_directory))
    if shutil.which("systemd-run") is None:
        print("systemd-run not available; cannot activate detached", file=sys.stderr)
        sys.exit(1)
    launch_exit_code, launch_output = launch_detached_activation_worker(
        arguments.state_dir
    )
    print(launch_output)
    sys.exit(launch_exit_code)


if __name__ == "__main__":
    main()
