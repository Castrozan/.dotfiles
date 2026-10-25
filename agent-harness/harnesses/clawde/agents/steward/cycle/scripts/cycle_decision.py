from dataclasses import replace

from cycle_configuration import UPSTREAM_BRANCH
from cycle_deployment_decision import decide_for_entrypoint
from cycle_facts import CycleDecision, CycleFacts, attention, wait
from cycle_validation_decision import decide_validation, validation_covers_entrypoint

SYNCHRONIZATION_BLOCKED = {"kind": "synchronization-blocked"}


def decide(facts: CycleFacts) -> CycleDecision:
    decision = decide_maintenance(facts)
    if decision.attention or not facts.unread_local_messages:
        return decision
    return replace(
        decision,
        attention={"kind": "inbox", "messages": list(facts.unread_local_messages)},
    )


def busy_reason(facts: CycleFacts) -> str:
    if facts.active_job_scopes:
        return f"job running: {', '.join(facts.active_job_scopes)}"
    if facts.rebuild_running:
        return "a rebuild is running"
    if facts.branch != UPSTREAM_BRANCH or facts.operation_in_progress:
        return "the checkout is off main or in the middle of a git operation"
    return ""


def decide_maintenance(facts: CycleFacts) -> CycleDecision:
    reason = busy_reason(facts)
    if reason:
        return wait(reason)
    if facts.behind:
        return decide_synchronization(facts)
    return decide_for_synchronized_head(facts)


def decide_synchronization(facts: CycleFacts) -> CycleDecision:
    blocked = facts.synchronization_stalled and facts.tracked_dirty
    if not facts.ahead:
        return CycleDecision(
            "fast-forward",
            f"{facts.behind} commits behind origin/main",
            SYNCHRONIZATION_BLOCKED if blocked else None,
        )
    if blocked:
        return CycleDecision(
            "attention",
            "uncommitted edits have blocked the rebase onto origin/main for hours",
            SYNCHRONIZATION_BLOCKED,
        )
    return decide_rebase(facts)


def decide_rebase(facts: CycleFacts) -> CycleDecision:
    conflict = facts.rebase_conflict
    if (conflict.get("head"), conflict.get("upstream")) == (facts.head, facts.upstream):
        return attention(
            "rebase-conflict",
            "local commits conflict with origin/main",
            head=facts.head,
            upstream=facts.upstream,
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
    validation = facts.validation
    status = validation.get("status")
    if status == "red":
        return decide_after_red_build(facts, validation)
    if status != "green":
        return decide_validation(facts, validation)
    if facts.ahead:
        return decide_push(facts)
    return decide_for_entrypoint(facts, validation)


def decide_after_red_build(facts: CycleFacts, validation: dict) -> CycleDecision:
    if not validation_covers_entrypoint(facts, validation):
        return decide_for_entrypoint(facts, validation)
    return attention(
        "build-red",
        "the chise build failed",
        revision=facts.head,
        entrypoint_revision=facts.entrypoint_head,
        log=validation.get("log", ""),
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
