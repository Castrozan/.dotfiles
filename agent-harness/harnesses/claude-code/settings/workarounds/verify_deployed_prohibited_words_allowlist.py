import json
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path


def machine_allowed_words_file(dotfiles_directory: Path, machine_alias: str) -> Path:
    return (
        dotfiles_directory
        / "private-configuration"
        / "machines"
        / machine_alias
        / "claude-prohibited-words-allowed.nix"
    )


def load_machine_allowed_words(
    dotfiles_directory: Path, machine_alias: str
) -> list[str] | None:
    allowed_words_file = machine_allowed_words_file(dotfiles_directory, machine_alias)
    if not allowed_words_file.is_file():
        return None

    result = subprocess.run(
        [
            "nix",
            "eval",
            "--impure",
            "--json",
            "--expr",
            f"import {json.dumps(str(allowed_words_file))}",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"could not evaluate {allowed_words_file}")

    allowed_words = json.loads(result.stdout)
    if not isinstance(allowed_words, list) or not all(
        isinstance(allowed_word, str) for allowed_word in allowed_words
    ):
        raise RuntimeError(f"{allowed_words_file} must evaluate to a list of strings")
    return allowed_words


def load_allowed_words_from_hook_events(hook_events: dict, source_file: Path) -> str:
    deployed_allowed_words = set()
    for hook_group in hook_events.get("PreToolUse", []):
        for hook in hook_group.get("hooks", []):
            command = hook.get("command")
            if not isinstance(command, str):
                continue
            command_tokens = shlex.split(command)
            assignment_tokens = [
                token
                for token in command_tokens
                if token.startswith("PROHIBITED_WORDS_ALLOWED=")
            ]
            if not assignment_tokens:
                continue
            if len(assignment_tokens) != 1 or command_tokens[0] != assignment_tokens[0]:
                raise RuntimeError(
                    f"{source_file} must register PROHIBITED_WORDS_ALLOWED exactly once as the first command token"
                )
            deployed_allowed_words.add(
                assignment_tokens[0].removeprefix("PROHIBITED_WORDS_ALLOWED=")
            )

    if not deployed_allowed_words:
        raise RuntimeError(f"{source_file} does not register PROHIBITED_WORDS_ALLOWED")
    if len(deployed_allowed_words) != 1:
        raise RuntimeError(
            f"{source_file} registers multiple prohibited-words allowlists"
        )
    return deployed_allowed_words.pop()


def load_claude_allowed_words(settings_file: Path) -> str:
    settings = json.loads(settings_file.read_text(encoding="utf-8"))
    return load_allowed_words_from_hook_events(settings.get("hooks", {}), settings_file)


def load_codex_allowed_words(requirements_file: Path) -> str:
    with requirements_file.open("rb") as file:
        requirements = tomllib.load(file)
    return load_allowed_words_from_hook_events(
        requirements.get("hooks", {}), requirements_file
    )


def verify_deployed_allowed_words(
    dotfiles_directory: Path,
    machine_alias: str,
    settings_source_file: Path,
    settings_file: Path,
    codex_requirements_file: Path,
) -> None:
    machine_allowed_words = load_machine_allowed_words(
        dotfiles_directory, machine_alias
    )
    if machine_allowed_words is None:
        return

    expected_allowed_words = ",".join(machine_allowed_words)
    deployed_allowed_words = {
        "the deployed Claude settings source": load_claude_allowed_words(
            settings_source_file
        ),
        "the active Claude settings": load_claude_allowed_words(settings_file),
        "the active Codex requirements": load_codex_allowed_words(
            codex_requirements_file
        ),
    }
    for deployment_target, actual_allowed_words in deployed_allowed_words.items():
        if actual_allowed_words != expected_allowed_words:
            raise RuntimeError(
                f"{deployment_target} does not match the per-machine prohibited-words allowlist"
            )


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: verify-deployed-prohibited-words-allowlist <dotfiles-directory> <machine-alias>",
            file=sys.stderr,
        )
        return 2

    try:
        verify_deployed_allowed_words(
            Path(sys.argv[1]),
            sys.argv[2],
            Path.home() / ".claude" / "settings.json.nix-source",
            Path.home() / ".claude" / "settings.json",
            Path("/etc/codex/requirements.toml"),
        )
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
