import asyncio
import os
import subprocess
import sys

import pytest

from codex_client_endpoint import ClientEndpoint
from codex_client_host import ClientHost


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
