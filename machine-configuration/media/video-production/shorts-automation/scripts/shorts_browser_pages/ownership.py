import fcntl
import json
import subprocess
from contextlib import contextmanager
from urllib.parse import urlparse

from shorts_store import read_document, write_document
from shorts_browser_pages.arguments import positional_tab_arguments, tab_arguments
from shorts_browser_pages.transport import create_page


class BrowserPages:
    def __init__(self, root, run_id, command, instance_id):
        self.root = root
        self.run_id = run_id
        self.command = command
        self.instance_id = instance_id
        self.path = root / "browser-pages.json"

    @contextmanager
    def lock(self):
        with (self.root / "browser-pages.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def result(self, arguments):
        result = subprocess.run(
            [*self.command, *arguments],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return json.loads(result.stdout)

    def targets(self):
        return self.result(["tab", "--json"])["tabs"]

    def begin(self):
        with self.lock():
            if self.path.exists():
                self.cleanup_state(read_document(self.path))
            write_document(
                self.path,
                {
                    "run_id": self.run_id,
                    "instance_id": self.instance_id,
                    "finished": False,
                    "pages": {},
                    "current": None,
                    "pending": None,
                },
            )

    def state(self):
        state = read_document(self.path)
        if state["run_id"] != self.run_id or state["instance_id"] != self.instance_id:
            raise ValueError("Browser pages must be owned by this production run")
        if state["finished"]:
            raise ValueError("This browser run is finished")
        if state["pending"] is not None:
            raise ValueError("Browser page creation is ambiguous; cleanup is required")
        return state

    def require_owned(self, state, identifier):
        if identifier not in state["pages"].values():
            raise ValueError("Browser actions require a tab owned by this run")
        return identifier

    def arguments(self, arguments):
        state = self.state()
        if arguments[0] == "health":
            return arguments
        remaining, identifier = tab_arguments(arguments)
        if identifier is not None:
            self.require_owned(state, identifier)
        if arguments[0] in ("tab", "close", "handoff", "handoff-status", "resume"):
            positional = positional_tab_arguments(remaining)
            identifier = self.require_owned(
                state, positional.identifier or identifier or state["current"]
            )
            if positional.command == ["tab"]:
                state["current"] = identifier
                write_document(self.path, state)
            return [*positional.command, identifier, *positional.options]
        if arguments[0] == "nav":
            if len(remaining) < 2 or remaining[1].startswith("-"):
                raise ValueError("Use nav URL to navigate a run-owned page")
            remaining = [
                value
                for value in remaining
                if value != "--new-tab" and not value.startswith("--new-tab=")
            ]
            role = (
                "publisher"
                if urlparse(remaining[1]).hostname == "studio.youtube.com"
                else "research"
            )
            if identifier is None:
                identifier = state["pages"].get(role)
                if identifier is not None and identifier not in {
                    target["id"] for target in self.targets()
                }:
                    del state["pages"][role]
                    identifier = None
                if identifier is None:
                    state["pending"] = role
                    write_document(self.path, state)
                    identifier = create_page(self.command[2])
                    if not isinstance(identifier, str) or not identifier:
                        raise ValueError("Browser page creation returned no target ID")
                    state["pages"][role] = identifier
                    state["pending"] = None
        else:
            identifier = identifier or state["current"]
            if identifier is None:
                raise ValueError("Navigate before using a run-owned browser tab")
            self.require_owned(state, identifier)
        state["current"] = identifier
        write_document(self.path, state)
        position = remaining.index("--") if "--" in remaining else len(remaining)
        return [*remaining[:position], "--tab", identifier, *remaining[position:]]

    def tabs(self):
        state = self.state()
        identifiers = set(state["pages"].values())
        return {
            "tabs": [target for target in self.targets() if target["id"] in identifiers]
        }

    def forget(self, identifier):
        state = self.state()
        state["pages"] = {
            role: target
            for role, target in state["pages"].items()
            if target != identifier
        }
        if state["current"] == identifier:
            state["current"] = next(iter(state["pages"].values()), None)
        write_document(self.path, state)

    def cleanup_state(self, state):
        state["finished"] = True
        write_document(self.path, state)
        if not state["pages"] and state["pending"] is None:
            return
        if state["instance_id"] != self.instance_id:
            state["pages"] = {}
            state["current"] = None
            state["pending"] = None
            write_document(self.path, state)
            return
        identifiers = {target["id"] for target in self.targets()}
        for role, identifier in list(state["pages"].items()):
            if identifier in identifiers:
                self.result(["close", identifier, "--json"])
            del state["pages"][role]
            if state["current"] == identifier:
                state["current"] = None
            write_document(self.path, state)
        if state["pending"] is not None:
            raise ValueError(
                "Browser page creation is ambiguous; inspect the dedicated profile before starting another run"
            )

    def cleanup(self):
        with self.lock():
            if not self.path.exists():
                return
            state = read_document(self.path)
            if state["run_id"] != self.run_id:
                raise ValueError("Browser pages must be owned by this production run")
            self.cleanup_state(state)
