from dataclasses import replace

from cycle_facts import CycleFacts

HEAD = "a" * 40
UPSTREAM = "b" * 40
TOPLEVEL = "/nix/store/validated-system"
SETTLED_SECONDS = 20 * 60
ENTRYPOINT = "e" * 40
RED_VALIDATION = {"status": "red", "log": "/log", "entrypoint_head": ENTRYPOINT}

GREEN_VALIDATION = {
    "status": "green",
    "toplevel": TOPLEVEL,
    "entrypoint_head": ENTRYPOINT,
}

SETTLED = CycleFacts(
    branch="main",
    operation_in_progress=False,
    active_job_scopes=(),
    head=HEAD,
    upstream=HEAD,
    behind=0,
    ahead=0,
    dirty_paths=(),
    newest_activity_age_seconds=SETTLED_SECONDS,
    oldest_unvalidated_age_seconds=SETTLED_SECONDS,
    head_validation=None,
    entrypoint_head=ENTRYPOINT,
    entrypoint_settled=True,
)

READY_TO_ACTIVATE = replace(
    SETTLED,
    head_validation=GREEN_VALIDATION,
    continuous_integration={"state": "passing"},
    live_toplevel="/nix/store/older-system",
    operator_idle=True,
)
