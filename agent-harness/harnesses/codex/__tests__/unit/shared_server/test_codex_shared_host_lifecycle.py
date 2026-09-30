import asyncio
import os
import subprocess
import sys

import pytest

from codex_client_endpoint import ClientEndpoint
from codex_client_host import ClientHost


def test_binary_only_upgrade_defers_shared_launch_while_clients_are_attached(
    tmp_path, monkeypatch
):
    import codex_client_control

    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    monkeypatch.setenv("CODEX_LAUNCHER_BINARY", "/old/codex")
    host = ClientHost()
    status = asyncio.run(host.respond({"method": "status"}))
    requests = []

    def request(socket_path, message):
        requests.append(message["method"])
        if message["method"] == "status":
            return status
        raise RuntimeError(
            "Close attached Codex clients before activating the upgraded proxy"
        )

    monkeypatch.setattr(codex_client_control, "request", request)
    try:
        endpoint = codex_client_control.register_client(
            {"CODEX_HOME": str(tmp_path), "CODEX_LAUNCHER_BINARY": "/new/codex"},
            {},
        )
        assert endpoint is None
        assert requests == ["status", "shutdown"]
    finally:
        (host.directory / "startup.lock").unlink()
        host.directory.rmdir()


def test_upgrade_preserves_a_live_terminal_during_its_reconnect_gap(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    monkeypatch.setenv("CODEX_LAUNCHER_BINARY", "codex")

    async def exercise():
        host = ClientHost()
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"]
        )
        endpoint = ClientEndpoint(
            host.directory, dict(os.environ), {}, process.pid, host.expire
        )
        host.endpoints.add(endpoint)
        try:
            with pytest.raises(RuntimeError, match="Close attached Codex clients"):
                await host.respond({"method": "shutdown"})
            await endpoint.expire_when_owner_exits()
            assert endpoint in host.endpoints
            process.terminate()
            await asyncio.to_thread(process.wait, 5)
            await endpoint.expire_when_owner_exits()
            assert endpoint not in host.endpoints
            await host.respond({"method": "shutdown"})
            assert host.stopped.is_set()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            if endpoint in host.endpoints:
                await endpoint.close()
            host.directory.rmdir()

    asyncio.run(exercise())
