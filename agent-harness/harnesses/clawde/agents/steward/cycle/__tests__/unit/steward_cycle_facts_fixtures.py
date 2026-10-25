from dataclasses import replace

from cycle_facts import CycleFacts

HEAD = "a" * 40
UPSTREAM = "b" * 40
TOPLEVEL = "/nix/store/validated-system"
SETTLED_SECONDS = 20 * 60

GREEN_VALIDATION = {
    "status": "green",
    "toplevel": TOPLEVEL,
    "entrypoint_head": "e" * 40,
}

SETTLED = CycleFacts(
    branch="main",
    operation_in_progress=False,
    active_job_scopes=(),
    head=HEAD,
    upstream=HEAD,
    behind=0,
    ahead=0,
    tracked_dirty=False,
    newest_activity_age_seconds=SETTLED_SECONDS,
    oldest_unvalidated_age_seconds=SETTLED_SECONDS,
    head_validation=None,
)

READY_TO_ACTIVATE = replace(
    SETTLED,
    head_validation=GREEN_VALIDATION,
    continuous_integration={"state": "passing"},
    live_toplevel="/nix/store/older-system",
    operator_idle=True,
    entrypoint_head="e" * 40,
    entrypoint_settled=True,
)
