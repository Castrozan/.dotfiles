from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from vicinae_installed_applications import (
    InstalledApplication,
    application_search_roots,
    discover_application_bundle_paths,
    installed_applications_by_identifier,
    sorted_directory_children,
)

GENERATED_SCRIPT_PREFIX = "generated-application."
GENERATED_SCRIPT_SUFFIX = ".sh"
GENERATED_ICON_DIRECTORY_NAME = ".generated-application-icons"
FOCUS_ONLY_BUNDLE_ROOT = "/System/Library/CoreServices/"
ICON_EDGE_PIXELS = "128"
WINDOW_CLOSE_DELAY_SECONDS = "0.05"
CLOSE_LAUNCHER_DEEPLINK = "vicinae://close?clearRootSearch=true&popToRootType=immediate"


def opens_new_instance(bundle_path: Path) -> bool:
    return not str(bundle_path).startswith(FOCUS_ONLY_BUNDLE_ROOT)


def generated_script_name(identifier: str) -> str:
    return f"{GENERATED_SCRIPT_PREFIX}{identifier}{GENERATED_SCRIPT_SUFFIX}"


def render_application_script(
    application: InstalledApplication, icon_path: Path | None, vicinae_command_path: str
) -> str:
    open_command = ["/usr/bin/open"]
    if opens_new_instance(application.bundle_path):
        open_command.append("-n")
    open_command.append(str(application.bundle_path))
    close_command = [vicinae_command_path, "deeplink", CLOSE_LAUNCHER_DEEPLINK]
    metadata_lines = [
        "# @vicinae.schemaVersion 1",
        f"# @vicinae.title {application.display_name}",
        "# @vicinae.mode inline",
        "# @vicinae.packageName Application",
    ]
    if icon_path is not None:
        metadata_lines.append(f"# @vicinae.icon {icon_path}")
    if application.search_keywords:
        metadata_lines.append(
            f"# @vicinae.keywords {json.dumps(list(application.search_keywords))}"
        )
    return "\n".join(
        [
            "#!/bin/bash",
            *metadata_lines,
            f"{shlex.join(open_command)} >/dev/null 2>&1 &",
            f"(sleep {WINDOW_CLOSE_DELAY_SECONDS}; {shlex.join(close_command)}) >/dev/null 2>&1 &",
            "",
        ]
    )


def icon_is_current(icon_path: Path, icon_source_path: Path) -> bool:
    try:
        return icon_path.stat().st_mtime >= icon_source_path.stat().st_mtime
    except OSError:
        return False


def exported_icon_path(
    application: InstalledApplication, icon_directory: Path
) -> Path | None:
    if application.icon_source_path is None:
        return None
    icon_path = icon_directory / f"{application.identifier}.png"
    if icon_is_current(icon_path, application.icon_source_path):
        return icon_path
    conversion = subprocess.run(
        [
            "/usr/bin/sips",
            "-s",
            "format",
            "png",
            "-Z",
            ICON_EDGE_PIXELS,
            str(application.icon_source_path),
            "--out",
            str(icon_path),
        ],
        capture_output=True,
        check=False,
    )
    return icon_path if conversion.returncode == 0 and icon_path.is_file() else None


def write_executable_script_if_changed(script_path: Path, content: str) -> None:
    try:
        if script_path.read_text() == content:
            return
    except (OSError, UnicodeDecodeError):
        pass
    with tempfile.NamedTemporaryFile(
        "w", dir=script_path.parent, prefix=".generating-", delete=False
    ) as temporary_file:
        temporary_file.write(content)
    os.chmod(temporary_file.name, 0o755)
    os.replace(temporary_file.name, script_path)


def remove_stale_generated_files(
    script_directory: Path,
    icon_directory: Path,
    applications: dict[str, InstalledApplication],
) -> None:
    current_script_names = {
        generated_script_name(identifier) for identifier in applications
    }
    for existing_path in sorted_directory_children(script_directory):
        is_generated_script = existing_path.name.startswith(GENERATED_SCRIPT_PREFIX)
        if is_generated_script and existing_path.name not in current_script_names:
            existing_path.unlink(missing_ok=True)
    current_icon_names = {f"{identifier}.png" for identifier in applications}
    for existing_path in sorted_directory_children(icon_directory):
        if existing_path.name not in current_icon_names:
            existing_path.unlink(missing_ok=True)


def synchronize_application_scripts(
    script_directory: Path,
    applications: dict[str, InstalledApplication],
    vicinae_command_path: str,
) -> None:
    icon_directory = script_directory / GENERATED_ICON_DIRECTORY_NAME
    icon_directory.mkdir(parents=True, exist_ok=True)
    for application in applications.values():
        icon_path = exported_icon_path(application, icon_directory)
        script_content = render_application_script(
            application, icon_path, vicinae_command_path
        )
        script_path = script_directory / generated_script_name(application.identifier)
        write_executable_script_if_changed(script_path, script_content)
    remove_stale_generated_files(script_directory, icon_directory, applications)


def main() -> None:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--script-directory", type=Path, required=True)
    argument_parser.add_argument("--vicinae-command", required=True)
    arguments = argument_parser.parse_args()
    bundle_paths = discover_application_bundle_paths(
        application_search_roots(Path.home())
    )
    synchronize_application_scripts(
        arguments.script_directory,
        installed_applications_by_identifier(bundle_paths),
        arguments.vicinae_command,
    )


if __name__ == "__main__":
    main()
