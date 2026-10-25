from dataclasses import replace

from cycle_configuration import MAXIMUM_VALIDATION_ATTEMPTS, UPSTREAM_BRANCH
from cycle_facts import CycleDecision, CycleFacts, attention, wait


def decide(facts: CycleFacts) -> CycleDecision:
    decision = decide_maintenance(facts)
    if decision.attention or not facts.unread_local_messages:
        return decision
    return replace(
        decision,
        attention={"kind": "inbox", "messages": list(facts.unread_local_messages)},
    )


def decide_maintenance(facts: CycleFacts) -> CycleDecision:
    if facts.active_job_scopes:
        return wait(f"job running: {', '.join(facts.active_job_scopes)}")
    if facts.rebuild_running:
        return wait("a rebuild is running")
    if facts.branch != UPSTREAM_BRANCH or facts.operation_in_progress:
        return wait("the checkout is off main or in the middle of a git operation")
    if facts.behind:
        return decide_synchronization(facts)
    return decide_for_synchronized_head(facts)


def synchronization_blocked(facts: CycleFacts) -> dict:
    return {
        "kind": "synchronization-blocked",
        "dirty_paths": list(facts.dirty_paths),
    }


def decide_synchronization(facts: CycleFacts) -> CycleDecision:
    if not facts.ahead:
        return CycleDecision(
            "fast-forward",
            f"{facts.behind} commits behind origin/main",
            synchronization_blocked(facts)
            if facts.synchronization_stalled and facts.tracked_dirty
            else None,
        )
    conflict = facts.recorded_rebase_conflict or {}
    if (
        conflict.get("head") == facts.head
        and conflict.get("upstream") == facts.upstream
    ):
        return attention(
            "rebase-conflict",
            "local commits conflict with origin/main",
            head=facts.head,
            upstream=facts.upstream,
        )
    if facts.tracked_dirty and facts.synchronization_stalled:
        return CycleDecision(
            "attention",
            "uncommitted edits have blocked the rebase onto origin/main for hours",
            synchronization_blocked(facts),
        )
    if facts.tracked_dirty or (
        facts.work_in_progress and not facts.synchronization_stalled
    ):
        return wait(
            "diverged from origin/main while the checkout is still being worked on"
        )
    return CycleDecision(
        "rebase", f"{facts.ahead} local commits diverged from origin/main"
    )


def decide_for_synchronized_head(facts: CycleFacts) -> CycleDecision:
    validation = facts.head_validation or {}
    status = validation.get("status")
    if status == "red" and validation_covers_entrypoint(facts, validation):
        return attention(
            "build-red",
            "the chise build failed",
            revision=facts.head,
            entrypoint_revision=facts.entrypoint_head,
            log=validation.get("log", ""),
        )
    if status not in ("green", "red"):
        return decide_validation(facts, validation)
    if status == "green" and facts.ahead:
        return decide_push(facts)
    return decide_for_entrypoint(facts, validation)


def decide_validation(facts: CycleFacts, validation: dict) -> CycleDecision:
    attempt = int(validation.get("attempt", 0))
    if attempt >= MAXIMUM_VALIDATION_ATTEMPTS:
        return attention(
            "validation-unavailable",
            f"{attempt} validation attempts ended without a verdict",
            revision=facts.head,
            log=validation.get("log", ""),
        )
    if facts.work_in_progress and not facts.starving:
        return wait("commits or edits landed within the quiet window")
    return CycleDecision(
        "validate", "the settled revision has no verdict", attempt=attempt + 1
    )


def decide_push(facts: CycleFacts) -> CycleDecision:
    if facts.unpublished_submodule_pins:
        return attention(
            "submodule-pin-unpublished",
            "a gitlink points at a commit its submodule remote lacks",
            revision=facts.head,
            pins=list(facts.unpublished_submodule_pins),
        )
    return CycleDecision(
        "push", f"{facts.ahead} validated commits ahead of origin/main"
    )


def validation_covers_entrypoint(facts: CycleFacts, validation: dict) -> bool:
    return validation.get("entrypoint_head") == facts.entrypoint_head


def decide_for_entrypoint(facts: CycleFacts, validation: dict) -> CycleDecision:
    if not facts.entrypoint_settled:
        return wait("the machine entrypoint is being worked on")
    if facts.entrypoint_behind and facts.entrypoint_ahead:
        return attention(
            "entrypoint-diverged",
            "the machine entrypoint diverged from its origin",
            revision=facts.entrypoint_head,
        )
    if facts.entrypoint_behind:
        return CycleDecision(
            "fast-forward-entrypoint",
            f"the machine entrypoint is {facts.entrypoint_behind} commits behind",
        )
    if not validation_covers_entrypoint(facts, validation):
        return decide_validation(facts, {})
    if facts.entrypoint_ahead:
        return CycleDecision(
            "push-entrypoint",
            f"{facts.entrypoint_ahead} validated machine entrypoint commits ahead",
        )
    return decide_activation(facts, validation)


def decide_activation(facts: CycleFacts, validation: dict) -> CycleDecision:
    continuous_integration = facts.continuous_integration or {}
    state = continuous_integration.get("state")
    if state == "failing":
        return attention(
            "ci-failing",
            "CI is failing on origin/main",
            revision=facts.upstream,
            workflows=continuous_integration.get("failing", []),
        )
    if facts.live_toplevel == validation.get("toplevel"):
        return CycleDecision("idle", "the live system runs the validated revision")
    activation = facts.head_activation or {}
    if activation.get("toplevel") != validation.get("toplevel"):
        activation = {}
    if activation.get("status") == "failed":
        return attention(
            "activation-failed",
            "switching to the validated revision failed",
            revision=facts.head,
            log=activation.get("log", ""),
        )
    if activation.get("status") == "activated":
        return CycleDecision(
            "idle", "this system was activated once; the live system changed since"
        )
    return decide_activation_window(facts, state)


def decide_activation_window(facts: CycleFacts, state: str | None) -> CycleDecision:
    if state not in ("passing", "none"):
        return wait("CI on origin/main has not passed yet")
    if not facts.operator_idle:
        return wait("the operator is active")
    return CycleDecision(
        "activate", "validated, pushed, CI passing and the operator is idle"
    )
