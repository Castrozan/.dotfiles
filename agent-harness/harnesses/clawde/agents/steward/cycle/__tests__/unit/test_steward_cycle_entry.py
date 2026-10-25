import json
from dataclasses import replace
from pathlib import Path

import steward_cycle
from cycle_decision import decide
from cycle_observation import synchronization_pending_seconds
from cycle_operator import unread_local_messages
from cycle_repository import RepositoryStateUnknown
from steward_cycle_facts_fixtures import RED_VALIDATION, SETTLED
from test_steward_cycle_records_and_worker import configuration_in


def test_attention_is_published_and_cleared(tmp_path):
    configuration = configuration_in(tmp_path)
    steward_cycle.publish(
        configuration, {"action": "attention", "attention": {"kind": "build-red"}}
    )
    assert json.loads(configuration.attention_file.read_text()) == {"kind": "build-red"}

    steward_cycle.publish(configuration, {"action": "idle", "attention": None})
    assert not configuration.attention_file.exists()


def test_dry_run_publishes_nothing(tmp_path):
    configuration = configuration_in(tmp_path, dry_run=True)

    steward_cycle.publish(
        configuration, {"action": "attention", "attention": {"kind": "build-red"}}
    )

    assert not configuration.attention_file.exists()
    assert not configuration.decision_file.exists()


def test_attention_probe_prints_nothing_without_a_failure(tmp_path, capsys):
    configuration = configuration_in(tmp_path)
    steward_cycle.print_attention(configuration)
    assert capsys.readouterr().out == ""

    configuration.attention_file.write_text(
        json.dumps({"kind": "ci-failing", "revision": "r"})
    )
    steward_cycle.print_attention(configuration)
    assert capsys.readouterr().out == '{"kind": "ci-failing", "revision": "r"}\n'


def test_a_repeated_cycle_error_wakes_the_agent_only_on_the_third_cycle(tmp_path):
    configuration = configuration_in(tmp_path)
    error = RepositoryStateUnknown("cannot count divergence from origin/main")

    reports = [steward_cycle.error_report(configuration, error) for _ in range(3)]

    assert [report["attention"] is not None for report in reports] == [
        False,
        False,
        True,
    ]


def test_a_concurrent_cycle_is_skipped(tmp_path):
    configuration = configuration_in(tmp_path)
    import fcntl

    with Path(configuration.lock_file).open("a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        report = steward_cycle.run_guarded(configuration, runner=None)

    assert report["action"] == "skipped"


def test_only_messages_from_local_senders_wake_the_agent(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (tmp_path / "peers.json").write_text(json.dumps({"peers": {"rin": {}, "kira": {}}}))
    (inbox / "1-from-rin.json").write_text(json.dumps({"from": "rin", "text": "fyi"}))
    (inbox / "2-from-nightly.json").write_text(
        json.dumps({"from": "nightly-deep-tiers", "text": "FAILED"})
    )
    (inbox / "read").mkdir()
    (inbox / "read" / "3-from-operator.json").write_text(
        json.dumps({"from": "operator"})
    )

    assert unread_local_messages(inbox, tmp_path / "peers.json") == (
        str(inbox / "2-from-nightly.json"),
    )


def test_a_local_message_raises_attention_without_stopping_maintenance():
    facts = replace(SETTLED, unread_local_messages=("/inbox/2-from-nightly.json",))

    decision = decide(facts)

    assert decision.action == "validate"
    assert decision.attention == {
        "kind": "inbox",
        "messages": ["/inbox/2-from-nightly.json"],
    }


def test_a_maintenance_failure_outranks_the_inbox():
    facts = replace(
        SETTLED,
        head_validation=RED_VALIDATION,
        unread_local_messages=("/inbox/2-from-nightly.json",),
    )

    assert decide(facts).attention["kind"] == "build-red"


def test_the_stall_timer_runs_only_while_the_checkout_stays_behind(tmp_path):
    configuration = configuration_in(tmp_path)

    assert synchronization_pending_seconds(configuration, 2, now=1000.0) == 0
    assert synchronization_pending_seconds(configuration, 5, now=1600.0) == 600
    assert synchronization_pending_seconds(configuration, 0, now=1700.0) == 0
    assert not configuration.synchronization_pending_file.exists()
    assert synchronization_pending_seconds(configuration, 1, now=1800.0) == 0
