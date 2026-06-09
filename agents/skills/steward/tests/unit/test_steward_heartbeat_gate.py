from steward_test_helpers import steward_heartbeat_gate


def diverged_status(**overrides) -> dict:
    status = {
        "verdict": "needs_sync",
        "head": "ba1418b8",
        "upstream": "0203c361",
        "behind": 1,
        "ahead": 1,
        "dirty": True,
        "inbox_unread": [],
        "continuous_integration": {"state": "passing", "url": "first"},
        "attention_required": True,
    }
    status.update(overrides)
    return status


def run_gate(monkeypatch, tmp_path, status) -> int:
    monkeypatch.setenv("STEWARD_WORKSPACE_DIR", str(tmp_path))
    monkeypatch.setattr(
        steward_heartbeat_gate, "collect_steward_status", lambda: status
    )
    return steward_heartbeat_gate.main()


def test_clean_state_never_wakes(monkeypatch, tmp_path):
    clean = {"verdict": "clean", "attention_required": False}
    assert run_gate(monkeypatch, tmp_path, clean) == 1


def test_unchanged_divergence_wakes_once_then_suppresses(monkeypatch, tmp_path):
    assert run_gate(monkeypatch, tmp_path, diverged_status()) == 0
    assert run_gate(monkeypatch, tmp_path, diverged_status()) == 1
    assert run_gate(monkeypatch, tmp_path, diverged_status()) == 1


def test_changed_divergence_wakes_again(monkeypatch, tmp_path):
    assert run_gate(monkeypatch, tmp_path, diverged_status()) == 0
    assert run_gate(monkeypatch, tmp_path, diverged_status()) == 1
    assert run_gate(monkeypatch, tmp_path, diverged_status(upstream="cafef00d")) == 0


def test_new_inbox_message_wakes_again(monkeypatch, tmp_path):
    assert run_gate(monkeypatch, tmp_path, diverged_status()) == 0
    assert (
        run_gate(
            monkeypatch, tmp_path, diverged_status(inbox_unread=["1-from-jojo.json"])
        )
        == 0
    )


def test_continuous_integration_state_flip_wakes_again(monkeypatch, tmp_path):
    pending = diverged_status(continuous_integration={"state": "pending", "url": "a"})
    assert run_gate(monkeypatch, tmp_path, pending) == 0
    assert run_gate(monkeypatch, tmp_path, pending) == 1
    failing = diverged_status(continuous_integration={"state": "failing", "url": "b"})
    assert run_gate(monkeypatch, tmp_path, failing) == 0


def test_volatile_continuous_integration_detail_does_not_rewake(monkeypatch, tmp_path):
    assert run_gate(monkeypatch, tmp_path, diverged_status()) == 0
    same_state_new_url = diverged_status(
        continuous_integration={"state": "passing", "url": "second"}
    )
    assert run_gate(monkeypatch, tmp_path, same_state_new_url) == 1


def test_returning_to_clean_resets_so_recurrence_wakes(monkeypatch, tmp_path):
    assert run_gate(monkeypatch, tmp_path, diverged_status()) == 0
    assert run_gate(monkeypatch, tmp_path, diverged_status()) == 1
    clean = {"verdict": "clean", "attention_required": False}
    assert run_gate(monkeypatch, tmp_path, clean) == 1
    assert run_gate(monkeypatch, tmp_path, diverged_status()) == 0
