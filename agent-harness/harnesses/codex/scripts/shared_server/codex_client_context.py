import fcntl
import json
import os
import re


SESSION_VARIABLES = (
    "HERDR_ENV",
    "HERDR_PANE_ID",
    "HERDR_TAB_ID",
    "HERDR_WORKSPACE_ID",
    "HERDR_SOCKET_PATH",
    "AGENT_INTERACTIVE_PREFERENCES_PATH",
    "CLAWDE_AGENT_NAME",
    "CLAWDE_AGENTS_DIRECTORY",
)


class ContextConflict(RuntimeError):
    pass


def context_directory():
    return os.path.join(
        os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex")), "client-context"
    )


def normalized_identifier(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}", identifier
    ):
        raise ValueError("Codex thread identifiers must be UUIDs")
    return identifier.lower()


def read_context(directory, identifier):
    try:
        identifier = normalized_identifier(identifier)
        with open(os.path.join(directory, f"{identifier}.lock"), "rb") as ownership:
            try:
                fcntl.flock(ownership, fcntl.LOCK_SH | fcntl.LOCK_NB)
                return None
            except BlockingIOError:
                owner = ownership.read().decode("ascii")
                if not owner:
                    return None
                with open(os.path.join(directory, f"{identifier}.json")) as source:
                    context = json.load(source)
                ownership.seek(0)
                if (
                    context.get("owner") != owner
                    or ownership.read().decode("ascii") != owner
                ):
                    return None
                environment = {
                    name: value
                    for name, value in context.get("environment", {}).items()
                    if name in SESSION_VARIABLES and isinstance(value, str)
                }
                instructions = context.get("developer_instructions")
                return {
                    "environment": environment,
                    "developer_instructions": instructions
                    if isinstance(instructions, str)
                    else "",
                }
    except (OSError, ValueError, TypeError, AttributeError):
        return None


class ClientContext:
    def __init__(self, directory, environment, configuration=None):
        import hashlib

        self.directory = directory
        self.environment = {
            name: environment[name] for name in SESSION_VARIABLES if name in environment
        }
        self.ownerships = {}
        self.owner = os.urandom(16).hex()
        self.instructions = (configuration or {}).get("developer_instructions", "")
        self.fingerprint = hashlib.sha256(
            json.dumps([environment, configuration], sort_keys=True).encode()
        ).hexdigest()
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)

    def reserve(self, identifier):
        identifier = normalized_identifier(identifier)
        if identifier in self.ownerships:
            return False
        descriptor = os.open(
            self.directory / f"{identifier}.lock", os.O_RDWR | os.O_CREAT, 0o600
        )
        ownership = os.fdopen(descriptor, "w")
        try:
            fcntl.flock(ownership, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            ownership.close()
            raise ContextConflict(
                "This thread is attached to another Codex client. Close that attachment before resuming here."
            ) from error
        self.ownerships[identifier] = ownership
        ownership.truncate(0)
        ownership.flush()
        return True

    def matches_configuration(self, identifier):
        try:
            identifier = normalized_identifier(identifier)
            saved = json.loads((self.directory / f"{identifier}.json").read_text())
            return saved.get("fingerprint") == self.fingerprint
        except (OSError, ValueError, AttributeError):
            return False

    def claim(self, identifier):
        import tempfile

        identifier = normalized_identifier(identifier)
        acquired = self.reserve(identifier)
        temporary = None
        try:
            descriptor, temporary = tempfile.mkstemp(dir=self.directory)
            with os.fdopen(descriptor, "w") as output:
                json.dump(
                    {
                        "environment": self.environment,
                        "fingerprint": self.fingerprint,
                        "developer_instructions": self.instructions,
                        "owner": self.owner,
                    },
                    output,
                )
            os.replace(temporary, self.directory / f"{identifier}.json")
            ownership = self.ownerships[identifier]
            ownership.seek(0)
            ownership.write(self.owner)
            ownership.truncate()
            ownership.flush()
        except BaseException:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
            if acquired:
                self.release(identifier)
            raise
        return acquired

    def release(self, identifier):
        identifier = normalized_identifier(identifier)
        ownership = self.ownerships.pop(identifier, None)
        if ownership is None:
            return
        ownership.truncate(0)
        ownership.flush()
        ownership.close()

    def close(self):
        for identifier in list(self.ownerships):
            self.release(identifier)


def restore_hook_context(payload):
    if os.environ.get("DOTFILES_CODEX_SHARED_SERVER") != "1":
        return
    context = read_context(context_directory(), payload.get("session_id")) or {}
    for name in (*SESSION_VARIABLES, "CODEX_THREAD_ID"):
        os.environ.pop(name, None)
    os.environ.update(context.get("environment", {}))
    return context.get("developer_instructions", "")
