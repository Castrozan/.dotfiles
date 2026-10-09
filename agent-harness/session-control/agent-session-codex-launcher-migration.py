import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

from agent_session.codex_launcher_migration import migrate
from agent_session.codex_migration_contract import require


class MigrationCommands:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.index = 0

    def run(self, label, arguments, timeout=5.0):
        index = self.index
        self.index += 1
        record = {"label": label, "arguments": arguments, "status": "running"}
        started = time.monotonic()
        (self.directory / f"command-{index:04d}-started.json").write_text(
            json.dumps(record, indent=2) + "\n"
        )
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        limits = {"stdout": 262144, "stderr": 8192}
        process = None
        try:
            process = subprocess.Popen(
                arguments,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            deadline = started + min(30.0, timeout)
            self._collect_output(process, deadline, buffers, limits, label)
            record["status"] = process.returncode
            require(
                process.returncode == 0,
                label + " returned status " + str(process.returncode),
            )
            return buffers["stdout"].decode()
        except Exception as error:
            record.update(
                status="failed", error=type(error).__name__ + ": " + str(error)
            )
            raise
        finally:
            self._close_process(process)
            record.update(
                elapsed_seconds=time.monotonic() - started,
                stdout_bytes=len(buffers["stdout"]),
                stderr_bytes=len(buffers["stderr"]),
                stdout=buffers["stdout"].decode(errors="replace"),
                stderr=buffers["stderr"].decode(errors="replace"),
            )
            (self.directory / f"command-{index:04d}-finished.json").write_text(
                json.dumps(record, indent=2) + "\n"
            )

    @staticmethod
    def _collect_output(process, deadline, buffers, limits, label):
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(label + " exceeded bounded command deadline")
                for key, _ in selector.select(min(0.1, remaining)):
                    MigrationCommands._read_output_block(
                        selector, key, buffers, limits, label
                    )
            process.wait(timeout=max(0.001, deadline - time.monotonic()))

    @staticmethod
    def _read_output_block(selector, key, buffers, limits, label):
        block = os.read(key.fileobj.fileno(), 65536)
        if not block:
            selector.unregister(key.fileobj)
            return
        require(
            len(buffers[key.data]) + len(block) <= limits[key.data],
            label + " exceeded bounded " + key.data,
        )
        buffers[key.data].extend(block)

    @staticmethod
    def _close_process(process):
        if process is None:
            return
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdout.close()
        process.stderr.close()

    def herdr(self, label, arguments, deadline=None):
        timeout = 3.0 if deadline is None else min(3.0, deadline - time.monotonic())
        require(timeout > 0, "Herdr readiness deadline expired")
        return json.loads(self.run(label, ["herdr", *arguments], timeout))["result"]

    def send(self, pane_identifier, message):
        directory = json.loads(self.run("a2a list", ["a2a", "list", "--json"]))
        matches = [
            entry
            for entry in directory.values()
            if isinstance(entry, dict) and entry.get("paneId") == pane_identifier
        ]
        require(
            len(matches) == 1 and matches[0].get("harness") == "codex",
            "a2a target is not unique Codex pane",
        )
        response = self.run(
            "a2a send", ["a2a", "send", matches[0]["name"], message], 10.0
        )
        require(bool(response.strip()), "a2a did not acknowledge continuation")
        return {"target": matches[0]["name"], "task_identifier": response.strip()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("attempt", type=Path)
    arguments = parser.parse_args()
    plan = json.loads(arguments.manifest.read_text())
    result = migrate(plan, MigrationCommands(arguments.attempt), arguments.attempt)
    print(json.dumps({"status": result["status"], "attempt": str(arguments.attempt)}))
    return 0 if result["status"] == "continuation-submitted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
