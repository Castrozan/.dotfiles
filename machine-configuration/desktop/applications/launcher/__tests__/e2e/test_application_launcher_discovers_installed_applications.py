from application_launcher_test_helpers import (
    collect_discovered_display_lines_via_dump_command,
)


def test_daemon_discovers_at_least_one_installed_application():
    display_lines = collect_discovered_display_lines_via_dump_command()
    assert len(display_lines) > 0, "no display lines were discovered by daemon"


def test_each_display_line_starts_with_a_status_indicator_character():
    display_lines = collect_discovered_display_lines_via_dump_command()
    for display_line in display_lines:
        first_character = display_line[0]
        assert first_character in {"●", " "}, (
            f"display line {display_line!r} does not start with a status indicator"
        )


def test_discovered_set_includes_at_least_one_built_in_macos_application():
    display_lines = collect_discovered_display_lines_via_dump_command()
    application_names_in_display_lines = [
        display_line[2:] for display_line in display_lines
    ]
    candidate_built_in_application_names = [
        "Calculator",
        "Calendar",
        "Safari",
        "System Settings",
    ]
    found_built_in_application_names = [
        application_name
        for application_name in candidate_built_in_application_names
        if application_name in application_names_in_display_lines
    ]
    assert found_built_in_application_names, (
        f"expected at least one of {candidate_built_in_application_names} in"
        f" discovered apps. first 10 discovered: {application_names_in_display_lines[:10]}"
    )


def test_discovered_set_includes_finder_from_core_services():
    display_lines = collect_discovered_display_lines_via_dump_command()
    application_names_in_display_lines = [
        display_line[2:] for display_line in display_lines
    ]
    assert "Finder" in application_names_in_display_lines, (
        "expected Finder to be discovered from /System/Library/CoreServices via the"
        " user-launchable allowlist"
    )
