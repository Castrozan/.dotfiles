import fcntl
import json
import subprocess
from contextlib import contextmanager

from shorts_store import read_document, write_document
from shorts_browser_pages.actions import owned_arguments
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
        return owned_arguments(self, self.state(), arguments)

    def navigation_page(self, state, role):
        identifier = state["pages"].get(role)
        if identifier is not None and not self.page_exists(identifier):
            del state["pages"][role]
            identifier = None
        if identifier is None:
            return self.create_page(state, role)
        return identifier

    def page_exists(self, identifier):
        return any(target["id"] == identifier for target in self.targets())

    def create_page(self, state, role):
        state["pending"] = role
        write_document(self.path, state)
        identifier = create_page(self.command[2])
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("Browser page creation returned no target ID")
        state["pages"][role] = identifier
        state["pending"] = None
        write_document(self.path, state)
        return identifier

    def select_page(self, state, identifier):
        state["current"] = identifier
        write_document(self.path, state)

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
            self.clear_pages(state)
            return
        self.close_pages(state)
        self.require_completed_allocation(state)

    def clear_pages(self, state):
        state["pages"] = {}
        state["current"] = None
        state["pending"] = None
        write_document(self.path, state)

    def close_pages(self, state):
        identifiers = {target["id"] for target in self.targets()}
        for role, identifier in list(state["pages"].items()):
            if identifier in identifiers:
                self.result(["close", identifier, "--json"])
            del state["pages"][role]
            if state["current"] == identifier:
                state["current"] = None
            write_document(self.path, state)

    def require_completed_allocation(self, state):
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
