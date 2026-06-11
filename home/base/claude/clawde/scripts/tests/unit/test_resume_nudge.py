import importlib.util
import pathlib
import sys

HEARTBEAT_DIRECTORY = (
    pathlib.Path(__file__).resolve().parent.parent.parent / "heartbeat"
)


def _load_resume_nudge_module():
    sys.path.insert(0, str(HEARTBEAT_DIRECTORY))
    module_path = HEARTBEAT_DIRECTORY / "resume_nudge.py"
    module_spec = importlib.util.spec_from_file_location("resume_nudge", module_path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


resume_nudge = _load_resume_nudge_module()


class _CompletedProcessStub:
    def __init__(self, stdout):
        self.stdout = stdout


def test_find_agent_wrapper_process_id_returns_first_match(monkeypatch):
    monkeypatch.setattr(
        resume_nudge.subprocess,
        "run",
        lambda *args, **kwargs: _CompletedProcessStub("4242\n"),
    )
    assert resume_nudge.find_agent_wrapper_process_id("jenny") == 4242


def test_find_agent_wrapper_process_id_returns_none_when_absent(monkeypatch):
    monkeypatch.setattr(
        resume_nudge.subprocess,
        "run",
        lambda *args, **kwargs: _CompletedProcessStub(""),
    )
    assert resume_nudge.find_agent_wrapper_process_id("jenny") is None


def test_agent_wrapper_has_live_claude_child_detects_claude(monkeypatch):
    monkeypatch.setattr(
        resume_nudge.subprocess,
        "run",
        lambda *args, **kwargs: _CompletedProcessStub(
            "65068 claude\n65069 python3.12\n"
        ),
    )
    assert resume_nudge.agent_wrapper_has_live_claude_child(32060) is True


def test_agent_wrapper_has_live_claude_child_false_when_wrapper_sleeping(monkeypatch):
    monkeypatch.setattr(
        resume_nudge.subprocess,
        "run",
        lambda *args, **kwargs: _CompletedProcessStub(""),
    )
    assert resume_nudge.agent_wrapper_has_live_claude_child(3884) is False


def test_agent_has_live_claude_repl_false_when_no_wrapper(monkeypatch):
    monkeypatch.setattr(
        resume_nudge, "find_agent_wrapper_process_id", lambda agent_name: None
    )
    assert resume_nudge.agent_has_live_claude_repl("betha-pm") is False


def test_main_skips_injection_when_agent_dormant(monkeypatch):
    monkeypatch.setattr(
        resume_nudge.sys,
        "argv",
        ["clawde-resume-nudge", "--session", "clawde", "--window", "betha-pm"],
    )
    monkeypatch.setattr(
        resume_nudge, "wait_for_live_claude_repl", lambda agent_name: False
    )
    injected_targets = []
    monkeypatch.setattr(
        resume_nudge,
        "send_prompt_via_tmux_buffer",
        lambda socket, target, content: injected_targets.append(target),
    )
    resume_nudge.main()
    assert injected_targets == []


def test_main_injects_when_agent_has_live_claude(monkeypatch):
    monkeypatch.setattr(
        resume_nudge.sys,
        "argv",
        ["clawde-resume-nudge", "--session", "clawde", "--window", "jenny"],
    )
    monkeypatch.setattr(
        resume_nudge, "wait_for_live_claude_repl", lambda agent_name: True
    )
    monkeypatch.setattr(resume_nudge, "find_tmux_socket", lambda: "/socket")
    monkeypatch.setattr(
        resume_nudge, "capture_recent_pane", lambda socket, target: "some output\n❯\n"
    )
    monkeypatch.setattr(
        resume_nudge, "wait_for_claude_prompt", lambda socket, target: True
    )
    injected_targets = []
    monkeypatch.setattr(
        resume_nudge,
        "send_prompt_via_tmux_buffer",
        lambda socket, target, content: injected_targets.append(target),
    )
    resume_nudge.main()
    assert injected_targets == ["clawde:jenny"]


RESUME_CONFIRMATION_MODAL_PANE = (
    "This session is 13h 41m old and 111.2k tokens.\n"
    "Resuming the full session will consume a substantial portion of your usage "
    "limits. We recommend resuming from a summary.\n"
    "   1. Resume from summary (recommended)\n"
    "   2. Resume full session as-is\n"
    "   3. Don't ask me again\n"
    "Enter to confirm · Esc to cancel\n"
)


def test_main_dismisses_resume_confirmation_modal_before_injecting(monkeypatch):
    monkeypatch.setattr(
        resume_nudge.sys,
        "argv",
        ["clawde-resume-nudge", "--session", "clawde", "--window", "steward"],
    )
    monkeypatch.setattr(
        resume_nudge, "wait_for_live_claude_repl", lambda agent_name: True
    )
    monkeypatch.setattr(resume_nudge, "find_tmux_socket", lambda: "/socket")
    pane_captures = [RESUME_CONFIRMATION_MODAL_PANE, "● back at the prompt\n❯\n"]
    monkeypatch.setattr(
        resume_nudge,
        "capture_recent_pane",
        lambda socket, target: pane_captures.pop(0) if pane_captures else "❯\n",
    )
    keys_sent = []
    monkeypatch.setattr(
        resume_nudge,
        "send_single_key_to_pane",
        lambda socket, target, key: keys_sent.append(key),
    )
    monkeypatch.setattr(
        resume_nudge, "wait_for_claude_prompt", lambda socket, target: True
    )
    injected_targets = []
    monkeypatch.setattr(
        resume_nudge,
        "send_prompt_via_tmux_buffer",
        lambda socket, target, content: injected_targets.append(target),
    )
    resume_nudge.main()
    assert keys_sent == ["Enter"], (
        "a warm redeploy that lands on an oversized session must answer the "
        "resume-confirmation dialog with Enter (the pre-highlighted summary resume) "
        "so the agent reaches its REPL instead of wedging at the dialog"
    )
    assert injected_targets == ["clawde:steward"]
