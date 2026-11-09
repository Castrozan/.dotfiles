from __future__ import annotations

import plistlib
import shlex
import stat
import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import generate_vicinae_application_scripts as generator
import vicinae_installed_applications as discovery

VICINAE_COMMAND = "/Applications/Vicinae.app/Contents/MacOS/vicinae-cli"


def create_application_bundle(bundle_path: Path, information: dict) -> Path:
    contents = bundle_path / "Contents"
    contents.mkdir(parents=True)
    with (contents / "Info.plist").open("wb") as information_file:
        plistlib.dump(information, information_file)
    return bundle_path


def installed_application(bundle_path: Path) -> discovery.InstalledApplication:
    return discovery.InstalledApplication(
        bundle_path=bundle_path,
        identifier="com.example.application",
        display_name="Example",
        search_keywords=(),
        icon_source_path=None,
    )


def open_command_tokens(script: str) -> list[str]:
    open_line = next(
        line for line in script.split("\n") if line.startswith("/usr/bin/open")
    )
    return shlex.split(open_line.removesuffix(" &"))[: -len(">/dev/null 2>&1".split())]


@given(
    bundle_name=st.text(
        alphabet=st.characters(
            exclude_characters="/\x00\n\r", exclude_categories=["Cs"]
        ),
        min_size=1,
    )
)
def test_every_bundle_path_reaches_open_as_one_argument(bundle_name):
    bundle_path = Path("/Applications") / f"{bundle_name}.app"

    script = generator.render_application_script(
        installed_application(bundle_path), None, VICINAE_COMMAND
    )

    assert open_command_tokens(script) == ["/usr/bin/open", "-n", str(bundle_path)]


@pytest.mark.parametrize(
    "bundle_path",
    [
        "/System/Library/CoreServices/Finder.app",
        "/System/Library/CoreServices/Applications/Keychain Access.app",
    ],
)
def test_core_services_applications_are_only_focused(bundle_path):
    script = generator.render_application_script(
        installed_application(Path(bundle_path)), None, VICINAE_COMMAND
    )

    assert open_command_tokens(script) == ["/usr/bin/open", bundle_path]


def test_script_exits_before_the_launcher_closes_so_vicinae_does_not_reopen_it():
    script = generator.render_application_script(
        installed_application(Path("/Applications/Example.app")), None, VICINAE_COMMAND
    )

    command_lines = [
        line for line in script.splitlines() if line and not line.startswith("#")
    ]

    assert all(line.endswith("&") for line in command_lines)
    assert any("sleep 0.05" in line and "deeplink" in line for line in command_lines)


def test_earlier_search_root_wins_for_a_duplicate_bundle_identifier(tmp_path):
    first_bundle = create_application_bundle(
        tmp_path / "first" / "Tool.app", {"CFBundleIdentifier": "com.example.tool"}
    )
    second_bundle = create_application_bundle(
        tmp_path / "second" / "Tool.app", {"CFBundleIdentifier": "com.example.tool"}
    )

    applications = discovery.installed_applications_by_identifier(
        [first_bundle, second_bundle]
    )

    assert applications["com.example.tool"].bundle_path == first_bundle


def test_discovery_reaches_one_folder_deep_and_stops_inside_bundles(tmp_path):
    direct_bundle = tmp_path / "Direct.app"
    nested_bundle = tmp_path / "Home Manager Apps" / "Nested.app"
    embedded_bundle = direct_bundle / "Contents" / "Applications" / "Embedded.app"
    too_deep_bundle = tmp_path / "Folder" / "Inner" / "TooDeep.app"
    bundle_inside_bundle = direct_bundle / "Contents" / "Resources" / "Helper.app"
    for bundle_path in (
        direct_bundle,
        nested_bundle,
        embedded_bundle,
        too_deep_bundle,
        bundle_inside_bundle,
    ):
        bundle_path.mkdir(parents=True)

    discovered = set(discovery.discover_application_bundle_paths([tmp_path]))

    assert {direct_bundle, nested_bundle, embedded_bundle} <= discovered
    assert not {too_deep_bundle, bundle_inside_bundle} & discovered


def test_bundle_without_identifier_or_runnable_executable_is_ignored(tmp_path):
    bundle_path = create_application_bundle(
        tmp_path / "Broken.app", {"CFBundleName": "Broken"}
    )

    assert discovery.read_installed_application(bundle_path) is None


def test_synchronization_replaces_stale_output_and_keeps_user_scripts(tmp_path):
    script_directory = tmp_path / "scripts"
    script_directory.mkdir()
    user_script = script_directory / "my-own-script.sh"
    user_script.write_text("#!/bin/bash\n")
    stale_script = script_directory / generator.generated_script_name(
        "com.example.removed"
    )
    stale_script.write_text("#!/bin/bash\n")
    application = discovery.read_installed_application(
        create_application_bundle(
            tmp_path / "Tool.app",
            {"CFBundleIdentifier": "com.example.tool", "CFBundleExecutable": "tool"},
        )
    )

    generator.synchronize_application_scripts(
        script_directory, {application.identifier: application}, VICINAE_COMMAND
    )

    generated_script = script_directory / generator.generated_script_name(
        "com.example.tool"
    )
    assert generated_script.stat().st_mode & stat.S_IXUSR
    assert '# @vicinae.keywords ["tool"]' in generated_script.read_text()
    assert user_script.exists()
    assert not stale_script.exists()


def test_unchanged_script_is_not_rewritten(tmp_path):
    script_path = tmp_path / "script.sh"
    generator.write_executable_script_if_changed(script_path, "content")
    first_modification = script_path.stat().st_mtime_ns

    generator.write_executable_script_if_changed(script_path, "content")

    assert script_path.stat().st_mtime_ns == first_modification
