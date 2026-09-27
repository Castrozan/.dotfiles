import base64
import json
import os
import re
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from contextlib import contextmanager


class NativeOpenCodeServer:
    def __init__(self, base_url, password, directory):
        self.base_url = base_url
        self.authorization = (
            "Basic " + base64.b64encode(f"opencode:{password}".encode()).decode()
        )
        self.directory = str(directory)

    def request(self, path, payload=None, method=None, location=False):
        if location:
            path += "?" + urllib.parse.urlencode(
                {"location[directory]": self.directory}
            )
        request = urllib.request.Request(
            self.base_url + path,
            data=None if payload is None else json.dumps(payload).encode(),
            method=method,
            headers={
                "Authorization": self.authorization,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                content = response.read()
        except urllib.error.HTTPError as failure:
            raise AssertionError(
                f"{path}: HTTP {failure.code}: {failure.read().decode()}"
            ) from failure
        return json.loads(content) if content else None

    def ready(self):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            plugins = self.request("/api/plugin", location=True)["data"]
            failures = [item for item in plugins if item["state"]["status"] == "error"]
            assert not failures, failures
            if plugins and all(item["state"]["status"] == "active" for item in plugins):
                return
            time.sleep(0.1)
        raise AssertionError(f"OpenCode plugins did not settle: {plugins}")


@contextmanager
def native_server(executable, environment, workspace):
    password = uuid.uuid4().hex
    with tempfile.TemporaryFile(mode="w+") as log:
        process = subprocess.Popen(
            [str(executable), "serve", "--hostname", "127.0.0.1", "--port", "0"],
            cwd=workspace,
            env=environment | {"OPENCODE_PASSWORD": password},
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
        try:
            deadline = time.monotonic() + 20
            address = None
            while time.monotonic() < deadline:
                log.seek(0)
                output = log.read()
                address = re.search(
                    r"server listening on (http://127\.0\.0\.1:\d+)", output
                )
                if address:
                    break
                assert process.poll() is None, output
                time.sleep(0.05)
            assert address, f"OpenCode server did not start: {output}"
            server = NativeOpenCodeServer(address.group(1), password, workspace)
            server.ready()
            yield server
        finally:
            for termination in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(process.pid, termination)
                except ProcessLookupError:
                    break
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    continue
                try:
                    os.killpg(process.pid, 0)
                except ProcessLookupError:
                    break
            process.wait(timeout=3)
