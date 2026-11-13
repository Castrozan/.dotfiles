from __future__ import annotations

import json
import subprocess

from ccusage_daily_summary import CcusageDocumentError, summarize_ccusage_daily

CCUSAGE_DAILY_COMMAND = (
    "ccusage",
    "claude",
    "daily",
    "--json",
    "--breakdown",
    "--offline",
    "--timezone",
    "UTC",
)
CCUSAGE_DAILY_TIMEOUT_SECONDS = 60


class CcusageCollectionError(RuntimeError):
    pass


def read_ccusage_daily_summary() -> dict | None:
    ccusage_daily_document = run_ccusage_daily_export()
    try:
        return summarize_ccusage_daily(ccusage_daily_document)
    except CcusageDocumentError as document_error:
        raise CcusageCollectionError(
            f"ccusage daily output is invalid: {document_error}"
        ) from document_error


def run_ccusage_daily_export():
    try:
        completed_process = subprocess.run(
            CCUSAGE_DAILY_COMMAND,
            capture_output=True,
            text=True,
            timeout=CCUSAGE_DAILY_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as timeout_error:
        raise CcusageCollectionError(
            f"ccusage daily export timed out after {CCUSAGE_DAILY_TIMEOUT_SECONDS} seconds"
        ) from timeout_error
    except OSError as start_error:
        raise CcusageCollectionError(
            "ccusage executable could not be started"
        ) from start_error
    if completed_process.returncode != 0:
        raise CcusageCollectionError(
            f"ccusage daily export exited with status {completed_process.returncode}"
        )
    try:
        return json.loads(completed_process.stdout)
    except json.JSONDecodeError as malformed_error:
        raise CcusageCollectionError(
            "ccusage daily output is not valid JSON"
        ) from malformed_error
