import json
import os
import signal
import subprocess


def run_analysis(command, repository):
    with subprocess.Popen(
        command,
        cwd=repository,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as process:
        try:
            output, errors = process.communicate(timeout=180)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            raise RuntimeError(f"{command[1]} exceeded 180 seconds") from None
    if process.returncode:
        raise RuntimeError(f"{' '.join(command)} failed: {errors.strip()}")
    return json.loads(output)


def collect_analysis(repository, selection):
    reports = {}
    failures = []
    operations = {
        "lint": [
            "check",
            "--json",
            "--no-fix",
            "--no-fail",
            "--no-progress",
            "--no-formatters",
            "--no-cache",
            "--jobs",
            "2",
            "--print-errors",
        ],
        "smells": ["smells", "--json", "--quiet"],
        "complexity": [
            "metrics",
            "--functions",
            "--exclude-tests",
            "--json",
            "--quiet",
        ],
    }
    for name, arguments in operations.items():
        try:
            reports[name] = run_analysis(
                ["qlty", "--no-upgrade-check", *arguments, *selection], repository
            )
        except (OSError, ValueError, RuntimeError) as error:
            failures.append(f"{name}: {error}")
    return reports, failures
