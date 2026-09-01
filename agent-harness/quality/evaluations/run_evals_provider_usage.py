from copy import deepcopy
from threading import Lock

TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)

_usage_lock = Lock()
_usage_by_role = {}


def reset_provider_usage() -> None:
    with _usage_lock:
        _usage_by_role.clear()


def record_provider_invocation(role: str, harness: str) -> None:
    with _usage_lock:
        bucket = _usage_by_role.setdefault(role, {}).setdefault(
            harness,
            {
                "invocations": 0,
                "measured_invocations": 0,
                **{field: 0 for field in TOKEN_FIELDS},
            },
        )
        bucket["invocations"] += 1


def record_provider_usage(role: str, harness: str, usage: dict | None) -> None:
    if not isinstance(usage, dict):
        return
    with _usage_lock:
        bucket = _usage_by_role[role][harness]
        bucket["measured_invocations"] += 1
        for field in TOKEN_FIELDS:
            bucket[field] += int(usage.get(field) or 0)


def provider_usage_summary() -> dict:
    with _usage_lock:
        return deepcopy(_usage_by_role)
