import socket

import monitor_hotplug_daemon as daemon


def serve_events(event_socket_path, payload: bytes, monkeypatch) -> list[str]:
    reconcile_calls = []
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(event_socket_path))
        listener.listen()

        def reconcile_and_publish_on_first_call() -> None:
            reconcile_calls.append("reconcile")
            if len(reconcile_calls) == 1:
                connection, _ = listener.accept()
                with connection:
                    connection.sendall(payload)

        monkeypatch.setattr(
            daemon,
            "reconcile_with_connected_monitors",
            reconcile_and_publish_on_first_call,
        )
        daemon.reconcile_and_dispatch_events(str(event_socket_path))
    return reconcile_calls


class TestReconcileAndDispatchEvents:
    def test_reconciles_on_connect_and_on_every_monitor_change(
        self, tmp_path, monkeypatch
    ):
        reconcile_calls = serve_events(
            tmp_path / "events.sock",
            b"monitoradded>>DP-1\nmonitorremoved>>DP-1\nmonitoraddedv2>>1,DP-1,Acer\n",
            monkeypatch,
        )
        assert len(reconcile_calls) == 3

    def test_ignores_unrelated_and_malformed_events(self, tmp_path, monkeypatch):
        reconcile_calls = serve_events(
            tmp_path / "events.sock",
            b"workspace>>2\nmonitoradded\nfocusedmon>>DP-1,1\n",
            monkeypatch,
        )
        assert len(reconcile_calls) == 1

    def test_event_raised_during_the_initial_reconcile_is_not_lost(
        self, tmp_path, monkeypatch
    ):
        reconcile_calls = serve_events(
            tmp_path / "events.sock", b"monitoradded>>DP-1\n", monkeypatch
        )
        assert len(reconcile_calls) == 2


class TestMonitorChangeEvents:
    def test_reacts_only_to_monitor_connection_changes(self):
        assert daemon.MONITOR_CHANGE_EVENTS == {"monitoradded", "monitorremoved"}
