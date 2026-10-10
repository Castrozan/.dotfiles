import json
import os
import shutil
import signal
import sys
import time

import pytest

from private_session_process_fixture import OWNED_ROLES, process_is_alive, wait_until


def test_private_backend_and_worker_groups_remain_in_terminal_session(
    private_session, request
):
    private_session.start()
    identities = private_session.identities
    request.node.user_properties.append(("process_identities", json.dumps(identities)))
    launcher, server, client = (
        identities[role] for role in ("launcher", "server", "client")
    )
    assert server["session_identifier"] == launcher["session_identifier"]
    assert server["process_group_identifier"] == server["process_identifier"]
    assert server["process_group_identifier"] != launcher["process_group_identifier"]
    assert client["process_group_identifier"] == launcher["process_group_identifier"]
    for role in ("worker-one", "worker-two"):
        worker = identities[role]
        assert worker["session_identifier"] == launcher["session_identifier"]
        assert worker["process_group_identifier"] == worker["process_identifier"]
        assert worker["process_group_identifier"] != server["process_group_identifier"]


def test_foreground_interrupt_reaches_client_without_stopping_backend_or_peer(
    private_session, request
):
    private_session.start()
    identities = private_session.identities
    request.node.user_properties.append(("process_identities", json.dumps(identities)))
    os.killpg(identities["launcher"]["process_group_identifier"], signal.SIGINT)
    wait_until(lambda: (private_session.directory / "client.interrupt").exists())
    assert all(process_is_alive(identity) for identity in identities.values())
    assert not any(
        (private_session.directory / f"{role}.interrupt").exists()
        for role in ("server", "worker-one", "worker-two", "peer")
    )


def test_native_pane_teardown_stops_owned_groups_and_preserves_separate_session_peer(
    private_session, request
):
    if sys.platform != "linux" or shutil.which("herdr") is None:
        pytest.skip("native pane teardown requires Linux and installed Herdr")
    private_session.start(native=True)
    identities = private_session.identities
    request.node.user_properties.append(("process_identities", json.dumps(identities)))
    assert (
        identities["peer"]["session_identifier"]
        != identities["launcher"]["session_identifier"]
    )
    started_at = time.monotonic()
    private_session.run_herdr("pane", "close", private_session.pane)
    private_session.pane = None
    try:
        wait_until(
            lambda: not any(process_is_alive(identities[role]) for role in OWNED_ROLES),
            timeout=2.0,
        )
    finally:
        request.node.user_properties.extend(
            (
                ("native_teardown_seconds", time.monotonic() - started_at),
                (
                    "remaining_owned_roles",
                    json.dumps(
                        [
                            role
                            for role in OWNED_ROLES
                            if process_is_alive(identities[role])
                        ]
                    ),
                ),
                ("separate_session_peer_alive", process_is_alive(identities["peer"])),
            )
        )
        assert process_is_alive(identities["peer"])
