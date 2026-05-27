"""Constants, file paths, and template scaffolding for the daily manager report."""

import datetime
import pathlib

PM_WORKSPACE_MARKER_RELATIVE_PATH = pathlib.Path(".pm") / "HEARTBEAT.md"
PM_WORKSPACE_REPORTS_RELATIVE_DIRECTORY = pathlib.Path("manager-reports")

BLOCKERS_HEADER = "Blockers:"
TODAY_HEADER = "Today:"
NEXT_HEADER = "Next:"
BULLET_INDENT = "    - "
DEFAULT_BLOCKERS_VALUE = "None"


def today_iso_date() -> str:
    return datetime.date.today().isoformat()


class DailyReportPmWorkspaceNotFoundError(Exception):
    pass


def find_pm_workspace_root_from(starting_directory: pathlib.Path) -> pathlib.Path:
    candidate_directory = starting_directory.resolve()
    while True:
        if (candidate_directory / PM_WORKSPACE_MARKER_RELATIVE_PATH).is_file():
            return candidate_directory
        if candidate_directory.parent == candidate_directory:
            raise DailyReportPmWorkspaceNotFoundError(
                f"no PM workspace marker ({PM_WORKSPACE_MARKER_RELATIVE_PATH}) found "
                f"walking up from {starting_directory}; run this skill from inside a "
                f"PM workspace"
            )
        candidate_directory = candidate_directory.parent


def reports_directory_for_current_workspace() -> pathlib.Path:
    return (
        find_pm_workspace_root_from(pathlib.Path.cwd())
        / PM_WORKSPACE_REPORTS_RELATIVE_DIRECTORY
    )


def report_path_for(date_iso: str) -> pathlib.Path:
    return reports_directory_for_current_workspace() / f"{date_iso}-manager-report.md"


def empty_report_text() -> str:
    return (
        f"{BLOCKERS_HEADER} {DEFAULT_BLOCKERS_VALUE}\n{TODAY_HEADER}\n{NEXT_HEADER}\n"
    )


def ensure_report_exists(report_file_path: pathlib.Path) -> None:
    report_file_path.parent.mkdir(parents=True, exist_ok=True)
    if not report_file_path.exists():
        report_file_path.write_text(empty_report_text(), encoding="utf-8")
