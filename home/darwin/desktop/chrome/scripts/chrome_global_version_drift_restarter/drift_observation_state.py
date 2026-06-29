from __future__ import annotations

import json
from pathlib import Path

DRIFT_OBSERVATION_STATE_FILE_PATH = Path(
    "/tmp/chrome-global-version-drift-restarter-state.json"
)
DRIFT_OBSERVATION_COUNT_STATE_KEY = "consecutive_drift_observations"
CONSECUTIVE_DRIFT_OBSERVATIONS_BEFORE_RESTART = 2


def should_restart_after_observation(
    consecutive_drift_observations: int, observations_before_restart: int
) -> bool:
    return consecutive_drift_observations >= observations_before_restart


def read_consecutive_drift_observation_count(state_file_path: Path) -> int:
    try:
        return int(
            json.loads(state_file_path.read_text())[DRIFT_OBSERVATION_COUNT_STATE_KEY]
        )
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError, TypeError):
        return 0


def write_consecutive_drift_observation_count(
    state_file_path: Path, consecutive_drift_observations: int
) -> None:
    state_file_path.write_text(
        json.dumps({DRIFT_OBSERVATION_COUNT_STATE_KEY: consecutive_drift_observations})
    )
