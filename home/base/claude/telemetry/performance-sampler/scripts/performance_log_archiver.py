import shutil
from pathlib import Path

ARCHIVED_TMP_LOG_PATHS = [
    Path("/tmp/workspace-switcher-perf.log"),
    Path("/tmp/karabiner-daemon.log"),
    Path("/tmp/chrome-devtools-mcp-runaway-watchdog.log"),
]

ARCHIVED_LOGS_SUBDIRECTORY_NAME = "archived-logs"


def last_archive_date_marker_path(state_directory: Path) -> Path:
    return state_directory / ".last-archive-date"


def should_archive_today(state_directory: Path, today_iso_date: str) -> bool:
    marker_path = last_archive_date_marker_path(state_directory)
    if not marker_path.exists():
        return True
    return marker_path.read_text(encoding="utf-8").strip() != today_iso_date


def parse_month_key_from_archived_log_stem(archived_log_stem: str):
    trailing_date_parts = archived_log_stem.rsplit("-", 3)
    if len(trailing_date_parts) != 4:
        return None
    try:
        year = int(trailing_date_parts[1])
        month = int(trailing_date_parts[2])
        int(trailing_date_parts[3])
    except ValueError:
        return None
    if not 1 <= month <= 12:
        return None
    return year * 12 + (month - 1)


def prune_archived_logs_older_than(
    state_directory: Path, sample_timestamp, retained_months: int
) -> list:
    archive_directory = state_directory / ARCHIVED_LOGS_SUBDIRECTORY_NAME
    if not archive_directory.is_dir():
        return []
    current_month_key = sample_timestamp.year * 12 + (sample_timestamp.month - 1)
    oldest_retained_month_key = current_month_key - (retained_months - 1)
    removed_archived_log_paths = []
    for archived_log_path in archive_directory.iterdir():
        archived_month_key = parse_month_key_from_archived_log_stem(
            archived_log_path.stem
        )
        if archived_month_key is None:
            continue
        if archived_month_key < oldest_retained_month_key:
            archived_log_path.unlink()
            removed_archived_log_paths.append(archived_log_path)
    return removed_archived_log_paths


def archive_tmp_logs(
    state_directory: Path, sample_timestamp, retained_months: int
) -> list:
    archive_directory = state_directory / ARCHIVED_LOGS_SUBDIRECTORY_NAME
    archive_directory.mkdir(parents=True, exist_ok=True)
    today_iso_date = sample_timestamp.strftime("%Y-%m-%d")
    archived_log_paths = []
    for source_log_path in ARCHIVED_TMP_LOG_PATHS:
        if not source_log_path.exists():
            continue
        destination_path = (
            archive_directory
            / f"{source_log_path.stem}-{today_iso_date}{source_log_path.suffix}"
        )
        shutil.copy2(source_log_path, destination_path)
        archived_log_paths.append(destination_path)
    prune_archived_logs_older_than(state_directory, sample_timestamp, retained_months)
    last_archive_date_marker_path(state_directory).write_text(
        today_iso_date, encoding="utf-8"
    )
    return archived_log_paths
