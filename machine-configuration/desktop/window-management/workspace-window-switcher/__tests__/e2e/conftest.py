import os
import socket
import tempfile
import time

import pytest

from workspace_window_switcher_helpers import (
    COMMAND_SETTLE_DELAY_SECONDS,
    SOCKET_PATH,
    send_command_to_daemon,
)


@pytest.fixture
def ipc_test_socket():
    temporary_directory = tempfile.mkdtemp(dir="/tmp")
    socket_path = os.path.join(temporary_directory, "test.sock")
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(socket_path)
    server_socket.listen(1)
    yield socket_path, server_socket
    server_socket.close()
    try:
        os.unlink(socket_path)
    except FileNotFoundError:
        pass
    os.rmdir(temporary_directory)


@pytest.fixture(autouse=True)
def workspace_switcher_integration_cancel_around_test(request):
    if not request.node.get_closest_marker("workspace_switcher_integration"):
        yield
        return
    if not os.path.exists(SOCKET_PATH):
        pytest.skip(
            "workspace-window-switcher daemon socket not present at " + SOCKET_PATH
        )
    send_command_to_daemon("cancel")
    time.sleep(COMMAND_SETTLE_DELAY_SECONDS / 2)
    try:
        yield
    finally:
        send_command_to_daemon("cancel")
        time.sleep(COMMAND_SETTLE_DELAY_SECONDS / 2)
