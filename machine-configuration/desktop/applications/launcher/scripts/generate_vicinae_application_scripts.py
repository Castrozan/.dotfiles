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
ICON_CONVERSION_TIMEOUT_SECONDS = 30


def opens_new_instance(bundle_path: Path) -> bool:
    return not str(bundle_path).startswith(FOCUS_ONLY_BUNDLE_ROOT)


def generated_script_name(identifier: str) -> str:
    return f"{GENERATED_SCRIPT_PREFIX}{identifier}{GENERATED_SCRIPT_SUFFIX}"


def render_application_script(
    application: InstalledApplication, icon_path: Path | None
) -> str:
    open_command = ["/usr/bin/open"]
    if opens_new_instance(application.bundle_path):
        open_command.append("-n")
    open_command.append(str(application.bundle_path))
    metadata_lines = [
        "# @vicinae.schemaVersion 1",
        f"# @vicinae.title {application.display_name}",
        "# @vicinae.mode silent",
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
            "",
        ]
    )


def icon_is_current(icon_path: Path, icon_source_path: Path) -> bool:
    try:
        return icon_path.stat().st_mtime >= icon_source_path.stat().st_mtime
    except OSError:
        return False


def convert_icon_to_png(icon_source_path: Path, icon_path: Path) -> bool:
    try:
        conversion = subprocess.run(
            [
                "/usr/bin/sips",
                "-s",
                "format",
                "png",
                "-Z",
                ICON_EDGE_PIXELS,
                str(icon_source_path),
                "--out",
                str(icon_path),
            ],
            capture_output=True,
            check=False,
            timeout=ICON_CONVERSION_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False
    return conversion.returncode == 0 and icon_path.is_file()


def exported_icon_path(
    application: InstalledApplication, icon_directory: Path
) -> Path | None:
    if application.icon_source_path is None:
        return None
    icon_path = icon_directory / f"{application.identifier}.png"
    if icon_is_current(icon_path, application.icon_source_path):
        return icon_path
    return (
        icon_path
        if convert_icon_to_png(application.icon_source_path, icon_path)
        else None
    )


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
    os.chmod(temporary_file.name, 0o700)
    os.replace(temporary_file.name, script_path)


def remove_children_except(
    directory: Path, name_prefix: str, names_to_keep: set[str]
) -> None:
    for existing_path in sorted_directory_children(directory):
        if (
            existing_path.name.startswith(name_prefix)
            and existing_path.name not in names_to_keep
        ):
            existing_path.unlink(missing_ok=True)


def remove_stale_generated_files(
    script_directory: Path,
    icon_directory: Path,
    applications: dict[str, InstalledApplication],
) -> None:
    current_script_names = {
        generated_script_name(identifier) for identifier in applications
    }
    remove_children_except(
        script_directory, GENERATED_SCRIPT_PREFIX, current_script_names
    )
    current_icon_names = {f"{identifier}.png" for identifier in applications}
    remove_children_except(icon_directory, "", current_icon_names)


def synchronize_application_scripts(
    script_directory: Path,
    applications: dict[str, InstalledApplication],
) -> None:
    icon_directory = script_directory / GENERATED_ICON_DIRECTORY_NAME
    icon_directory.mkdir(parents=True, exist_ok=True)
    for application in applications.values():
        icon_path = exported_icon_path(application, icon_directory)
        script_content = render_application_script(application, icon_path)
        script_path = script_directory / generated_script_name(application.identifier)
        write_executable_script_if_changed(script_path, script_content)
    remove_stale_generated_files(script_directory, icon_directory, applications)


def main() -> None:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--script-directory", type=Path, required=True)
    arguments = argument_parser.parse_args()
    bundle_paths = discover_application_bundle_paths(
        application_search_roots(Path.home())
    )
    synchronize_application_scripts(
        arguments.script_directory,
        installed_applications_by_identifier(bundle_paths),
    )


if __name__ == "__main__":
    main()
