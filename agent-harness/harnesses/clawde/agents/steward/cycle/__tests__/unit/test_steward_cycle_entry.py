import json
from dataclasses import replace
from pathlib import Path

import steward_cycle
from cycle_decision import decide
from cycle_inbox import unread_local_messages
from cycle_jobs import (
    ACTIVATION_SCOPE_PREFIX,
    VALIDATION_SCOPE_PREFIX,
    rebuild_running,
    scope_command,
)
from cycle_repository import RepositoryStateUnknown
from steward_cycle_facts_fixtures import SETTLED
from test_steward_cycle_records_and_worker import configuration_in


def test_scopes_keep_the_prefix_the_memory_bound_attaches_to():
    command = scope_command(VALIDATION_SCOPE_PREFIX, "a" * 40, ["worker"])

    assert "--unit=steward-validate-aaaaaaaa" in command
    assert command[-2:] == ["--", "worker"]
    assert ACTIVATION_SCOPE_PREFIX != VALIDATION_SCOPE_PREFIX


def test_a_running_rebuild_is_recognized_by_its_executable(tmp_path):
    def process(identifier: str, *arguments: bytes) -> None:
        (tmp_path / identifier).mkdir()
        (tmp_path / identifier / "cmdline").write_bytes(b"\0".join(arguments) + b"\0")

    process("10", b"bash", b"-c", b"cd ~/.dotfiles && rebuild")
    process("11", b"vim", b"notes", b"/nix/store/aaa-rebuild/bin/rebuild")
    assert not rebuild_running(tmp_path)

    process("12", b"bash", b"/nix/store/aaa-rebuild/bin/rebuild", b"--override-input")
    assert rebuild_running(tmp_path)


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
        head_validation={"status": "red", "log": "/log"},
        unread_local_messages=("/inbox/2-from-nightly.json",),
    )

    assert decide(facts).attention["kind"] == "build-red"
