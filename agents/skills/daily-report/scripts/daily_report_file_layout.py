"""Constants, file paths, and template scaffolding for the daily manager report."""

import datetime
import pathlib

REPORTS_DIRECTORY = pathlib.Path.home() / "vault" / "manager-reports"

BLOCKERS_HEADER = "Blockers:"
TODAY_HEADER = "Today:"
NEXT_HEADER = "Next:"
BULLET_INDENT = "    - "
DEFAULT_BLOCKERS_VALUE = "None"


def today_iso_date() -> str:
    return datetime.date.today().isoformat()


def report_path_for(date_iso: str) -> pathlib.Path:
    return REPORTS_DIRECTORY / f"{date_iso}-manager-report.md"


def empty_report_text() -> str:
    return (
        f"{BLOCKERS_HEADER} {DEFAULT_BLOCKERS_VALUE}\n{TODAY_HEADER}\n{NEXT_HEADER}\n"
    )


def ensure_report_exists(report_file_path: pathlib.Path) -> None:
    REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    if not report_file_path.exists():
        report_file_path.write_text(empty_report_text(), encoding="utf-8")
