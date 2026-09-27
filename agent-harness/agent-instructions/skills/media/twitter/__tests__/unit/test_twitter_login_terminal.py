import json
import os
import pty
import select
import signal
import sys
import time
from pathlib import Path

import pytest


@pytest.fixture
def login_terminal(tmp_path):
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    child_script = tmp_path / "login.py"
    child_script.write_text(
        "import importlib.util, sys\n"
        "from pathlib import Path\n"
        "from types import SimpleNamespace\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "import twikit_cli_authentication as authentication\n"
        "class Client:\n"
        "    def __init__(self, language): pass\n"
        "    async def login(self, **arguments):\n"
        "        assert arguments['password'] == 'fixture-password-hidden'\n"
        "    def save_cookies(self, path): Path(path).write_text('{}')\n"
        "sys.modules['twikit'] = SimpleNamespace(Client=Client)\n"
        "authentication.COOKIES_PATH = Path(sys.argv[2])\n"
        "authentication.USERNAME_FILE = ''\n"
        "authentication.EMAIL_FILE = ''\n"
        "authentication.PASSWORD_FILE = ''\n"
        "specification = importlib.util.spec_from_file_location('cli', Path(sys.argv[1]) / 'twikit-cli.py')\n"
        "cli = importlib.util.module_from_spec(specification)\n"
        "specification.loader.exec_module(cli)\n"
        "sys.argv = ['twikit-cli', 'login']\n"
        "cli.main()\n"
    )
    cookies = tmp_path / "cookies.json"
    process_identifier, terminal = pty.fork()
    if process_identifier == 0:
        os.execv(
            sys.executable,
            [sys.executable, str(child_script), str(scripts), str(cookies)],
        )
    try:
        yield process_identifier, terminal, cookies
    finally:
        os.close(terminal)
        try:
            os.kill(process_identifier, signal.SIGKILL)
            os.waitpid(process_identifier, 0)
        except ProcessLookupError:
            pass


def read_until(terminal, expected):
    transcript = b""
    deadline = time.monotonic() + 5
    while expected not in transcript:
        assert time.monotonic() < deadline, "login prompt timed out"
        if select.select([terminal], [], [], 0.05)[0]:
            transcript += os.read(terminal, 4096)
    return transcript


def wait_for_exit(process_identifier, terminal):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        completed, status = os.waitpid(process_identifier, os.WNOHANG)
        if completed:
            return os.waitstatus_to_exitcode(status)
        if terminal is not None and select.select([terminal], [], [], 0)[0]:
            try:
                os.read(terminal, 4096)
            except OSError:
                terminal = None
        time.sleep(0.02)
    pytest.fail("login did not exit within two seconds")


@pytest.mark.parametrize("cancel_prompt", [b"X username:", b"X email:", b"X password:"])
def test_interrupt_at_each_prompt_exits_without_saving(login_terminal, cancel_prompt):
    process_identifier, terminal, cookies = login_terminal
    for prompt, answer in [
        (b"X username:", b"fixture-user\n"),
        (b"X email:", b"fixture@example.test\n"),
        (b"X password:", b"fixture-password-hidden\n"),
    ]:
        read_until(terminal, prompt)
        if prompt == cancel_prompt:
            os.write(terminal, b"\x03")
            break
        os.write(terminal, answer)
    assert wait_for_exit(process_identifier, terminal) != 0
    assert not cookies.exists()


def test_password_is_not_echoed_and_login_completes(login_terminal):
    process_identifier, terminal, cookies = login_terminal
    transcript = b""
    for prompt, answer in [
        (b"X username:", b"fixture-user\n"),
        (b"X email:", b"fixture@example.test\n"),
        (b"X password:", b"fixture-password-hidden\n"),
    ]:
        transcript += read_until(terminal, prompt)
        os.write(terminal, answer)
    transcript += read_until(terminal, b"Cookies saved to")
    assert wait_for_exit(process_identifier, terminal) == 0
    assert b"fixture-password-hidden" not in transcript
    assert json.loads(cookies.read_text()) == {}
    assert cookies.stat().st_mode & 0o777 == 0o600
