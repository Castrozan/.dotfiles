from cycle_facts import CycleDecision, CycleFacts, attention, wait
from cycle_validation_decision import decide_validation, validation_covers_entrypoint


def entrypoint_synchronization(facts: CycleFacts) -> CycleDecision | None:
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
    return None


def decide_for_entrypoint(facts: CycleFacts, validation: dict) -> CycleDecision:
    synchronization = entrypoint_synchronization(facts)
    if synchronization:
        return synchronization
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
    if continuous_integration.get("state") == "failing":
        return attention(
            "ci-failing",
            "CI is failing on origin/main",
            revision=facts.upstream,
            workflows=continuous_integration.get("failing", []),
        )
    if facts.live_toplevel == validation.get("toplevel"):
        return CycleDecision("idle", "the live system runs the validated revision")
    return decide_after_recorded_activation(
        facts, validation, continuous_integration.get("state")
    )


def decide_after_recorded_activation(
    facts: CycleFacts, validation: dict, state: str | None
) -> CycleDecision:
    activation = facts.head_activation or {}
    status = (
        activation.get("status")
        if activation.get("toplevel") == validation.get("toplevel")
        else None
    )
    if status == "failed":
        return attention(
            "activation-failed",
            "switching to the validated revision failed",
            revision=facts.head,
            log=activation.get("log", ""),
        )
    if status == "activated":
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
