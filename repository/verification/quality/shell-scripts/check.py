import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SHELL_EXTENSIONS = {".sh", ".bash", ".bats"}
SHELL_INTERPRETERS = ("bash", "sh")
SHEBANG_BYTES = 128
SHELLCHECK_TIMEOUT_SECONDS = 45


def tracked_files(repository):
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--", ".", ":!private-configuration"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    return [name for name in listing.stdout.split("\0") if name]


def names_a_shell_interpreter(first_line):
    if not first_line.startswith("#!"):
        return False
    words = first_line[2:].replace("/", " ").split()
    return any(word in SHELL_INTERPRETERS for word in words)


def extensionless_shell_scripts(repository):
    scripts = []
    for name in tracked_files(repository):
        path = repository / name
        if path.suffix in SHELL_EXTENSIONS or not path.is_file():
            continue
        with path.open("rb") as script:
            first_line = script.readline(SHEBANG_BYTES).decode("utf-8", "replace")
        if names_a_shell_interpreter(first_line):
            scripts.append(name)
    return scripts


def main():
    scripts = extensionless_shell_scripts(REPOSITORY_ROOT)
    if not scripts:
        print("Shell script check: no extensionless shell scripts")
        return 0
    analysis = subprocess.run(
        [
            "shellcheck",
            "--external-sources",
            "--source-path=SCRIPTDIR",
            "--format=gcc",
            "--",
            *scripts,
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        timeout=SHELLCHECK_TIMEOUT_SECONDS,
    )
    if analysis.returncode:
        print(analysis.stdout.strip() or analysis.stderr.strip(), file=sys.stderr)
        return 1
    print(f"Shell script check: OK ({len(scripts)} extensionless shell scripts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
