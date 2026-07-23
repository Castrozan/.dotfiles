import os

import pytest

from application_launcher_test_helpers import (
    APPLICATION_LAUNCHER_DAEMON_SOCKET_PATH,
    send_datagram_command_to_application_launcher_daemon,
)


@pytest.fixture(autouse=True)
def skip_when_application_launcher_daemon_socket_is_not_present():
    if not os.path.exists(APPLICATION_LAUNCHER_DAEMON_SOCKET_PATH):
        pytest.skip(
            "application-launcher daemon socket not present at "
            + APPLICATION_LAUNCHER_DAEMON_SOCKET_PATH
            + "; daemon may not be running"
        )


@pytest.fixture(autouse=True)
def dismiss_any_visible_picker_around_each_test():
    if os.path.exists(APPLICATION_LAUNCHER_DAEMON_SOCKET_PATH):
        send_datagram_command_to_application_launcher_daemon("dismiss")
    yield
    if os.path.exists(APPLICATION_LAUNCHER_DAEMON_SOCKET_PATH):
        send_datagram_command_to_application_launcher_daemon("dismiss")
