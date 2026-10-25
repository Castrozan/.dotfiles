from dataclasses import replace

import pytest

from cycle_decision import decide
from steward_cycle_facts_fixtures import (
    ENTRYPOINT,
    GREEN_VALIDATION,
    HEAD,
    RED_VALIDATION,
    SETTLED,
    UPSTREAM,
)

STALLED_SECONDS = 3 * 60 * 60


@pytest.mark.parametrize(
    ("facts", "action", "attention_kind"),
    [
        (
            replace(SETTLED, active_job_scopes=("steward-validate-aaaaaaaa.scope",)),
            "wait",
            None,
        ),
        (replace(SETTLED, branch="feature"), "wait", None),
        (replace(SETTLED, operation_in_progress=True), "wait", None),
        (replace(SETTLED, behind=3, upstream=UPSTREAM), "fast-forward", None),
        (
            replace(
                SETTLED, behind=1, ahead=2, upstream=UPSTREAM, dirty_paths=("a.nix",)
            ),
            "wait",
            None,
        ),
        (
            replace(
                SETTLED,
                behind=1,
                ahead=2,
                upstream=UPSTREAM,
                newest_activity_age_seconds=60,
            ),
            "wait",
            None,
        ),
        (replace(SETTLED, behind=1, ahead=2, upstream=UPSTREAM), "rebase", None),
        (
            replace(
                SETTLED,
                behind=1,
                ahead=2,
                upstream=UPSTREAM,
                dirty_paths=("a.nix",),
                synchronization_pending_seconds=STALLED_SECONDS,
            ),
            "attention",
            "synchronization-blocked",
        ),
        (
            replace(
                SETTLED,
                behind=1,
                ahead=2,
                upstream=UPSTREAM,
                newest_activity_age_seconds=60,
                synchronization_pending_seconds=STALLED_SECONDS,
            ),
            "rebase",
            None,
        ),
        (
            replace(
                SETTLED,
                behind=3,
                upstream=UPSTREAM,
                dirty_paths=("a.nix",),
                synchronization_pending_seconds=STALLED_SECONDS,
            ),
            "fast-forward",
            "synchronization-blocked",
        ),
        (
            replace(SETTLED, head_validation=RED_VALIDATION, entrypoint_head="f" * 40),
            "validate",
            None,
        ),
        (
            replace(
                SETTLED,
                behind=1,
                ahead=2,
                upstream=UPSTREAM,
                recorded_rebase_conflict={"head": HEAD, "upstream": UPSTREAM},
            ),
            "attention",
            "rebase-conflict",
        ),
        (replace(SETTLED, newest_activity_age_seconds=60), "wait", None),
        (
            replace(
                SETTLED,
                newest_activity_age_seconds=60,
                oldest_unvalidated_age_seconds=3 * 60 * 60,
            ),
            "validate",
            None,
        ),
        (SETTLED, "validate", None),
        (
            replace(SETTLED, head_validation={"status": "transient", "attempt": 1}),
            "validate",
            None,
        ),
        (
            replace(SETTLED, head_validation={"status": "transient", "attempt": 3}),
            "attention",
            "validation-unavailable",
        ),
        (
            replace(SETTLED, head_validation=RED_VALIDATION),
            "attention",
            "build-red",
        ),
        (replace(SETTLED, head_validation=GREEN_VALIDATION, ahead=2), "push", None),
        (
            replace(
                SETTLED,
                head_validation=GREEN_VALIDATION,
                ahead=2,
                unpublished_submodule_pins=("private@c",),
            ),
            "attention",
            "submodule-pin-unpublished",
        ),
        (replace(SETTLED, behind=2, rebuild_running=True), "wait", None),
    ],
)
def test_decision_for_observed_facts(facts, action, attention_kind):
    decision = decide(facts)

    assert decision.action == action
    assert (decision.attention or {}).get("kind") == attention_kind


def test_validation_attempts_count_up_from_the_recorded_attempt():
    decision = decide(
        replace(SETTLED, head_validation={"status": "transient", "attempt": 2})
    )

    assert decision.attempt == 3


def test_attention_names_the_revision_and_log_the_agent_must_fix():
    decision = decide(
        replace(
            SETTLED,
            head_validation={**RED_VALIDATION, "log": "/state/validations/a.log"},
        )
    )

    assert decision.attention == {
        "kind": "build-red",
        "revision": HEAD,
        "entrypoint_revision": ENTRYPOINT,
        "log": "/state/validations/a.log",
    }
