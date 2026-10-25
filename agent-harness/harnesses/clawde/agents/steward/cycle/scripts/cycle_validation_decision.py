from cycle_configuration import MAXIMUM_VALIDATION_ATTEMPTS
from cycle_facts import CycleDecision, CycleFacts, attention, wait


def validation_covers_entrypoint(facts: CycleFacts, validation: dict) -> bool:
    return validation.get("entrypoint_head") == facts.entrypoint_head


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
