import importlib.util
import pathlib
import signal

CLAWDE_SCRIPTS_DIRECTORY = pathlib.Path(__file__).resolve().parent.parent.parent


def _load_clawde_redeploy_module():
    module_spec = importlib.util.spec_from_file_location(
        "clawde_redeploy", CLAWDE_SCRIPTS_DIRECTORY / "clawde-redeploy.py"
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


clawde_redeploy = _load_clawde_redeploy_module()


def test_find_agent_wrapper_process_ids_parses_pgrep_output(monkeypatch):
    class CompletedProcessStub:
        stdout = "111\n222\n333\n"

    monkeypatch.setattr(
        clawde_redeploy.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcessStub(),
    )
    assert clawde_redeploy.find_agent_wrapper_process_ids() == [111, 222, 333]


def test_find_agent_wrapper_process_ids_ignores_non_numeric_lines(monkeypatch):
    class CompletedProcessStub:
        stdout = "\n   \n444\n"

    monkeypatch.setattr(
        clawde_redeploy.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcessStub(),
    )
    assert clawde_redeploy.find_agent_wrapper_process_ids() == [444]


def test_signal_agent_wrappers_sends_sigusr1_to_each(monkeypatch):
    signalled_calls = []
    monkeypatch.setattr(
        clawde_redeploy.os,
        "kill",
        lambda process_id, signal_number: signalled_calls.append(
            (process_id, signal_number)
        ),
    )
    clawde_redeploy.signal_agent_wrappers_to_restart_on_continued_sessions([7, 8])
    assert signalled_calls == [(7, signal.SIGUSR1), (8, signal.SIGUSR1)]


def test_signal_agent_wrappers_ignores_already_exited_process(monkeypatch):
    def raise_process_lookup_error(process_id, signal_number):
        raise ProcessLookupError

    monkeypatch.setattr(clawde_redeploy.os, "kill", raise_process_lookup_error)
    clawde_redeploy.signal_agent_wrappers_to_restart_on_continued_sessions([9])
