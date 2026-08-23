import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

MAXIMUM_BASELINE_AGE_DAYS = 30


@dataclass(frozen=True)
class BaselineValidation:
    document: dict
    age_days: int | None
    failures: list[str]


def write_baseline(baseline_path: Path, baseline: dict) -> None:
    with open(baseline_path, "w") as file_handle:
        json.dump(baseline, file_handle, indent=2)
        file_handle.write("\n")


def validate_tracked_baseline(
    baseline_path: Path,
    value_key: str,
    ceiling_key: str,
    save_baseline_command: str,
) -> BaselineValidation:
    document, unreadable = _read_baseline_document(
        baseline_path,
        save_baseline_command,
    )
    if unreadable is not None:
        return BaselineValidation({}, None, [unreadable])

    age_days = _baseline_age_days(document)
    failures = _freshness_failures(age_days, save_baseline_command)
    failures.extend(_measurement_failures(document, value_key, ceiling_key))
    return BaselineValidation(document, age_days, failures)


def _read_baseline_document(
    baseline_path: Path,
    save_baseline_command: str,
) -> tuple[dict, str | None]:
    if not baseline_path.exists():
        return {}, (
            f"No baseline file at {baseline_path}. "
            f"Run '{save_baseline_command}' to generate it."
        )
    try:
        document = json.loads(baseline_path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return {}, (
            f"Baseline at {baseline_path} is not readable JSON. "
            f"Re-run '{save_baseline_command}'."
        )
    if not isinstance(document, dict):
        return {}, (
            f"Baseline at {baseline_path} is not a JSON object. "
            f"Re-run '{save_baseline_command}'."
        )
    return document, None


def _baseline_age_days(document: dict) -> int | None:
    generated_at = document.get("generated_at")
    if not isinstance(generated_at, str):
        return None
    try:
        generated = datetime.fromisoformat(generated_at)
    except ValueError:
        return None
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - generated).days


def _freshness_failures(
    age_days: int | None,
    save_baseline_command: str,
) -> list[str]:
    if age_days is None:
        return [
            "Baseline has no usable generated_at timestamp. "
            f"Re-run '{save_baseline_command}'."
        ]
    if age_days > MAXIMUM_BASELINE_AGE_DAYS:
        return [
            f"Baseline is {age_days} days old "
            f"(max {MAXIMUM_BASELINE_AGE_DAYS}). "
            f"Re-run '{save_baseline_command}'."
        ]
    return []


def _measurement_failures(
    document: dict,
    value_key: str,
    ceiling_key: str,
) -> list[str]:
    measurements = document.get("measurements")
    if not isinstance(measurements, dict):
        return ["Baseline measurements are not a JSON object."]
    if not measurements:
        return ["Baseline has no measurements."]

    failures: list[str] = []
    for name, data in measurements.items():
        if not isinstance(data, dict):
            failures.append(f"{name}: measurement entry is not a JSON object")
            continue
        for key in (value_key, ceiling_key):
            failures.extend(_measurement_value_failures(name, data, key))
    return failures


def _measurement_value_failures(name: str, data: dict, key: str) -> list[str]:
    if key not in data:
        return [f"{name}: missing {key}"]
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return [f"{name}: {key} is not a number"]
    if value <= 0:
        return [f"{name}: {key} must be greater than zero"]
    return []
