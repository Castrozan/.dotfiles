from dataclasses import replace

import pytest

from cycle_decision import decide
from steward_cycle_facts_fixtures import READY_TO_ACTIVATE, TOPLEVEL


@pytest.mark.parametrize(
    ("facts", "action", "attention_kind"),
    [
        (
            replace(
                READY_TO_ACTIVATE,
                continuous_integration={"state": "failing", "failing": []},
            ),
            "attention",
            "ci-failing",
        ),
        (replace(READY_TO_ACTIVATE, live_toplevel=TOPLEVEL), "idle", None),
        (
            replace(READY_TO_ACTIVATE, continuous_integration={"state": "pending"}),
            "wait",
            None,
        ),
        (replace(READY_TO_ACTIVATE, operator_idle=False), "wait", None),
        (replace(READY_TO_ACTIVATE, rebuild_running=True), "wait", None),
        (replace(READY_TO_ACTIVATE, entrypoint_settled=False), "wait", None),
        (replace(READY_TO_ACTIVATE, entrypoint_head="f" * 40), "validate", None),
        (
            replace(
                READY_TO_ACTIVATE,
                head_activation={
                    "status": "failed",
                    "log": "/log",
                    "toplevel": TOPLEVEL,
                },
            ),
            "attention",
            "activation-failed",
        ),
        (
            replace(
                READY_TO_ACTIVATE,
                head_activation={"status": "activated", "toplevel": TOPLEVEL},
            ),
            "idle",
            None,
        ),
        (
            replace(
                READY_TO_ACTIVATE,
                head_activation={"status": "activated", "toplevel": "/nix/store/old"},
            ),
            "activate",
            None,
        ),
        (
            replace(READY_TO_ACTIVATE, entrypoint_behind=1),
            "fast-forward-entrypoint",
            None,
        ),
        (
            replace(READY_TO_ACTIVATE, entrypoint_behind=1, entrypoint_ahead=1),
            "attention",
            "entrypoint-diverged",
        ),
        (replace(READY_TO_ACTIVATE, entrypoint_ahead=1), "push-entrypoint", None),
        (
            replace(READY_TO_ACTIVATE, entrypoint_ahead=1, entrypoint_head="f" * 40),
            "validate",
            None,
        ),
        (
            replace(
                READY_TO_ACTIVATE,
                entrypoint_head="f" * 40,
                newest_activity_age_seconds=60,
            ),
            "wait",
            None,
        ),
        (READY_TO_ACTIVATE, "activate", None),
        (
            replace(READY_TO_ACTIVATE, continuous_integration={"state": "none"}),
            "activate",
            None,
        ),
    ],
)
def test_decision_for_observed_facts(facts, action, attention_kind):
    decision = decide(facts)

    assert decision.action == action
    assert (decision.attention or {}).get("kind") == attention_kind


def test_a_dirty_entrypoint_never_loops_into_revalidation():
    facts = replace(
        READY_TO_ACTIVATE, entrypoint_settled=False, entrypoint_head="f" * 40
    )

    assert decide(facts).action == "wait"
