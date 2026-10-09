import subprocess
import sys


def command_failure(repository, command):
    try:
        result = subprocess.run(
            command,
            cwd=repository,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"{' '.join(command)}: {error}"
    if not result.returncode:
        return None
    return f"{' '.join(command)}: {result.stderr.strip() or result.stdout.strip()}"


def repository_failures(repository):
    commands = [
        [
            sys.executable,
            str(repository / "repository/verification/check-line-counts.py"),
        ],
        [
            sys.executable,
            str(
                repository
                / "repository/verification/quality/directory-entries/check.py"
            ),
        ],
        [
            "ast-grep",
            "test",
            "--config",
            ".qlty/sgconfig.yml",
            "--skip-snapshot-tests",
        ],
    ]
    failures = []
    for command in commands:
        failure = command_failure(repository, command)
        if failure is not None:
            failures.append(failure)
    return failures
