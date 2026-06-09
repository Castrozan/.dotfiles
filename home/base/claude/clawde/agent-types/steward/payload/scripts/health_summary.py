"""Runtime health summary for the dotfiles steward agent.

Runs `health-check --json` and reduces it to the failing probes the steward
must act on, dropping the steward's own daemon self-probe (a steward checking
its own liveness mid-tick always reads as down). Health is the live machine's
runtime state, never repo correctness, so this stays separate from the repo and
submodule diagnosis. run_capturing is injected to keep it testable, mirroring
continuous_integration and submodule_status.
"""

import json
from pathlib import Path

HEALTH_CHECK_TIMEOUT_SECONDS = 60


def is_own_daemon_self_probe(probe: dict) -> bool:
    return probe.get("category") == "daemon" and "clawde agent: steward" in probe.get(
        "name", ""
    )


def health_check_summary(run_capturing) -> dict:
    return_code, output = run_capturing(
        ["health-check", "--json"], Path.home(), HEALTH_CHECK_TIMEOUT_SECONDS
    )
    if return_code == 127:
        return {"available": False}
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return {"available": True, "parse_error": True, "exit_code": return_code}
    probes = parsed if isinstance(parsed, list) else parsed.get("probes", [])
    failing = [
        probe
        for probe in probes
        if probe.get("status", "pass") != "pass" and not is_own_daemon_self_probe(probe)
    ]
    return {
        "available": True,
        "exit_code": return_code,
        "total": len(probes),
        "failing": [
            f"{probe.get('category', '?')}/{probe.get('name', '?')}"
            for probe in failing
        ],
    }
