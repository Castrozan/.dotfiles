from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

from dotfiles_repository_scope import repository_is_personal_tooling


def nearest_ancestor_with_marker(directory: Path, marker: str):
    return next(
        (
            candidate
            for candidate in (directory, *directory.parents)
            if (candidate / marker).exists()
        ),
        None,
    )


def resolved_configuration_path():
    working_directory = Path.cwd()
    declared = os.environ.get("AGENT_EVALS_CONFIG")
    if declared:
        root = (
            nearest_ancestor_with_marker(working_directory, ".git") or working_directory
        )
        return (root / declared).resolve()
    root = nearest_ancestor_with_marker(
        working_directory, "evals/config.yaml"
    ) or nearest_ancestor_with_marker(working_directory, ".git")
    return root / "evals/config.yaml" if root is not None else None


def require_codex_arguments(arguments):
    for index, argument in enumerate(arguments):
        flag, separator, value = argument.partition("=")
        if flag not in ("--client", "--cliente"):
            continue
        if not separator:
            value = arguments[index + 1] if index + 1 < len(arguments) else ""
        if value != "codex":
            raise ValueError(
                "Dotfiles evaluations support Codex only. Use --client codex."
            )


def require_codex_configuration(configuration):
    for section_names in (("sujeito", "subject"), ("juiz", "judge")):
        sections = [
            configuration[name] for name in section_names if name in configuration
        ]
        if len(sections) != 1 or not isinstance(sections[0], dict):
            raise ValueError(
                "Dotfiles evaluation subject and judge must explicitly select Codex."
            )
        clients = [
            sections[0][name] for name in ("cliente", "client") if name in sections[0]
        ]
        if clients != ["codex"]:
            raise ValueError(
                "Dotfiles evaluation subject and judge must explicitly select Codex."
            )


def execute_guarded_evaluations(executable, arguments):
    config_path = resolved_configuration_path()
    configuration = None
    if config_path is not None and config_path.is_file():
        configuration = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    project = (
        configuration.get("projeto", configuration.get("project"))
        if isinstance(configuration, dict)
        else None
    )
    personal_tooling = (
        repository_is_personal_tooling(str(Path.cwd()))
        or project == "dotfiles-agent-instructions"
    )
    if config_path is not None:
        personal_tooling = personal_tooling or repository_is_personal_tooling(
            str(config_path.parent)
        )
    if personal_tooling:
        require_codex_arguments(arguments)
        if not isinstance(configuration, dict):
            raise ValueError(
                "Dotfiles evaluations require a Codex configuration mapping."
            )
        require_codex_configuration(configuration)
    os.execv(executable, [executable, *arguments])


def main():
    try:
        execute_guarded_evaluations(sys.argv[1], sys.argv[2:])
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"agent-evals: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
