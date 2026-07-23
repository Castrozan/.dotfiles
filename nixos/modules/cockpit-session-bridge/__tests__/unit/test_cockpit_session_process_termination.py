import asyncio
import os
import signal

from cockpit_session_bridge_runtime_test_doubles import FakeSessionProcess

import server


def test_terminate_skips_signals_when_session_process_already_exited():
    already_exited_process = FakeSessionProcess(returncode=0, first_wait_hangs=False)

    asyncio.run(server.terminate_session_process(already_exited_process))

    assert already_exited_process.signals_sent == []


def test_terminate_escalates_to_sigkill_when_sighup_does_not_reap(monkeypatch):
    monkeypatch.setattr(server, "SESSION_PROCESS_TERMINATION_TIMEOUT_SECONDS", 0.05)
    process_group_kill_calls = []
    monkeypatch.setattr(os, "getpgid", lambda process_id: process_id)
    monkeypatch.setattr(
        os,
        "killpg",
        lambda process_group_id, signal_number: process_group_kill_calls.append(
            (process_group_id, signal_number)
        ),
    )
    unresponsive_process = FakeSessionProcess(returncode=None, first_wait_hangs=True)

    asyncio.run(server.terminate_session_process(unresponsive_process))

    assert signal.SIGHUP in unresponsive_process.signals_sent
    assert process_group_kill_calls == [(4242, signal.SIGKILL)]
