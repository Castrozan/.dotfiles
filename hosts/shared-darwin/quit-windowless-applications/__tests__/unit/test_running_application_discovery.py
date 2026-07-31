import os
import subprocess
import types


def test_an_application_whose_process_already_exited_is_not_reported_as_running(
    daemon, monkeypatch
):
    already_exited_process = subprocess.Popen(["/bin/sh", "-c", "exit 0"])
    already_exited_process.wait()
    running_process_identifier = os.getpid()
    workspace_entries = [
        types.SimpleNamespace(
            processIdentifier=lambda: running_process_identifier,
            activationPolicy=lambda: daemon.NSApplicationActivationPolicyRegular,
        ),
        types.SimpleNamespace(
            processIdentifier=lambda: already_exited_process.pid,
            activationPolicy=lambda: daemon.NSApplicationActivationPolicyRegular,
        ),
    ]
    monkeypatch.setattr(
        daemon,
        "NSWorkspace",
        types.SimpleNamespace(
            sharedWorkspace=lambda: types.SimpleNamespace(
                runningApplications=lambda: workspace_entries
            )
        ),
    )

    still_running = daemon.get_running_regular_applications()

    assert [entry.processIdentifier() for entry in still_running] == [
        running_process_identifier
    ]


def test_history_of_applications_that_exited_is_discarded(daemon):
    window_history_by_process_identifier = {
        101: daemon.ApplicationWindowHistory(first_seen_at=0.0),
        202: daemon.ApplicationWindowHistory(first_seen_at=0.0),
    }
    still_running_applications = [
        types.SimpleNamespace(processIdentifier=lambda: 101),
    ]

    daemon.forget_applications_that_exited(
        window_history_by_process_identifier, still_running_applications
    )

    assert list(window_history_by_process_identifier) == [101]
