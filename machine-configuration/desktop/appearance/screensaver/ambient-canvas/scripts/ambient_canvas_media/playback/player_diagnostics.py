import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime
from logging.handlers import RotatingFileHandler


MAXIMUM_LOG_BYTES = 1024 * 1024
LOG_BACKUP_COUNT = 2
RETAINED_PLAYER_RUN_COUNT = 10
OUTPUT_TAIL_BYTES = 64 * 1024


def diagnostic_timestamp():
    return datetime.now().astimezone().isoformat()


def create_diagnostic_logger(name, log_path):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_path,
        maxBytes=MAXIMUM_LOG_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    return logger


def write_player_report(run_directory, report):
    report_path = Path(run_directory) / "report.json"
    temporary_path = report_path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(report_path)


def player_run_is_active(run_directory):
    try:
        report = json.loads((run_directory / "report.json").read_text())
        if report.get("status") != "running":
            return False
        supervisor_pid = report.get("supervisor_pid")
        if not isinstance(supervisor_pid, int) or supervisor_pid <= 0:
            return False
        os.kill(supervisor_pid, 0)
        return True
    except PermissionError:
        return True
    except (OSError, ValueError):
        return False


def create_player_run(state_directory):
    runs_directory = Path(state_directory) / "player-runs"
    runs_directory.mkdir(parents=True, exist_ok=True)
    inactive_runs = sorted(
        path
        for path in runs_directory.iterdir()
        if path.is_dir() and not player_run_is_active(path)
    )
    for run_directory in inactive_runs[:-RETAINED_PLAYER_RUN_COUNT]:
        shutil.rmtree(run_directory)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f-")
    return Path(tempfile.mkdtemp(prefix=timestamp, dir=runs_directory))
