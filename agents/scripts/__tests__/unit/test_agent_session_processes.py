from agent_session import processes


def test_detects_a_clawde_wrapper_in_the_process_ancestry(monkeypatch):
    process_records = {
        101: (102, "/bin/sh"),
        102: (1, "python wrapper.py --agent-name steward --config-file steward.json"),
    }
    monkeypatch.setattr(
        processes,
        "process_info_for",
        lambda process_identifier: process_records.get(process_identifier),
    )

    assert processes.clawde_wrapper_is_ancestor_of(101)


def test_terminating_an_agent_session_reaps_descendants_before_its_parent(monkeypatch):
    process_children = {123: [124], 124: [125], 125: []}
    signals = []
    monkeypatch.setattr(
        processes,
        "child_process_identifiers_for",
        lambda process_identifier: process_children[process_identifier],
    )
    monkeypatch.setattr(
        processes.os,
        "kill",
        lambda process_identifier, signal: signals.append((process_identifier, signal)),
    )
    monkeypatch.setattr(processes.time, "sleep", lambda _seconds: None)

    processes.terminate_agent_session(123)

    assert signals == [
        (125, processes.signal.SIGTERM),
        (124, processes.signal.SIGTERM),
        (123, processes.signal.SIGTERM),
        (125, processes.signal.SIGKILL),
        (124, processes.signal.SIGKILL),
    ]


def test_restart_teardown_keeps_its_controller_and_launcher_alive(monkeypatch):
    process_children = {123: [124], 124: [125], 125: [126], 126: []}
    signals = []
    monkeypatch.setattr(
        processes,
        "child_process_identifiers_for",
        lambda process_identifier: process_children[process_identifier],
    )
    monkeypatch.setattr(
        processes.os,
        "kill",
        lambda process_identifier, signal: signals.append((process_identifier, signal)),
    )
    monkeypatch.setattr(processes.time, "sleep", lambda _seconds: None)

    processes.terminate_agent_session(123, frozenset({125, 126}))

    assert signals == [
        (124, processes.signal.SIGTERM),
        (123, processes.signal.SIGTERM),
        (124, processes.signal.SIGKILL),
    ]
