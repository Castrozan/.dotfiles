from codex_client_context import ContextConflict
from codex_client_configuration import ThreadPreparation, thread_configuration


class ClientProtocol:
    def __init__(self, context, configuration, environment):
        self.context = context
        self.configuration = configuration
        self.environment = environment
        self.pending = {}
        self.threads = set()
        self.ephemeral_threads = set()
        self.working_directory = environment.get("PWD")

    def request(self, message, preparation=None):
        preparation = preparation or ThreadPreparation({})
        method = message.get("method")
        parameters = message.get("params") or {}
        if preparation.working_directory:
            parameters = {**parameters, "cwd": preparation.working_directory}
            message = {**message, "params": parameters}
        identifier = parameters.get("threadId")
        claimed = False
        if method in {"thread/start", "thread/resume", "thread/fork"}:
            if preparation.reuse_loaded:
                message = {
                    **message,
                    "params": {
                        name: value
                        for name, value in parameters.items()
                        if name
                        not in {"config", "baseInstructions", "developerInstructions"}
                    },
                }
            elif not parameters.get("ephemeral", False):
                message = {
                    **message,
                    "params": thread_configuration(
                        parameters,
                        self.configuration,
                        self.environment,
                        preparation.configuration,
                    ),
                }
            if method == "thread/resume":
                claimed = identifier not in self.threads
                self.context.claim(identifier)
            self.pending[message["id"]] = (method, identifier, claimed)
        elif method == "thread/unsubscribe":
            self.pending[message["id"]] = (method, identifier, False)
        elif (
            method
            in {
                "turn/start",
                "turn/steer",
                "turn/interrupt",
                "thread/compact/start",
                "thread/shellCommand",
            }
            and identifier not in self.threads | self.ephemeral_threads
        ):
            raise ContextConflict(
                "Attach this thread before sending a turn or command."
            )
        return message

    def response(self, message):
        if "method" in message or message.get("id") not in self.pending:
            return message
        method, identifier, claimed = self.pending.pop(message["id"])
        if "error" in message:
            if claimed:
                self.context.release(identifier)
            return message
        if method == "thread/unsubscribe":
            self.threads.discard(identifier)
            self.context.release(identifier)
            return message
        thread = message.get("result", {}).get("thread")
        if thread and thread.get("ephemeral", False):
            self.ephemeral_threads.add(thread["id"])
        if thread and not thread.get("ephemeral", False):
            try:
                self.context.claim(thread["id"])
            except ContextConflict as error:
                return failure(message["id"], str(error))
            self.threads.add(thread["id"])
            self.working_directory = thread.get("cwd", self.working_directory)
        return message

    def close(self):
        self.context.close()


def failure(identifier, message):
    return {"id": identifier, "error": {"code": -32000, "message": message}}
