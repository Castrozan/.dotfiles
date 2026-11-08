import importlib.util
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "avatar_audio", Path(__file__).resolve().parents[3] / "scripts/audio.py"
)
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)


class Pulse:
    def __init__(self):
        self.modules = [{"index": 1, "name": "unrelated", "argument": "keep"}]
        self.sinks = []
        self.sources = [{"name": "synthetic-human.monitor"}]
        self.calls = []
        self.next_identifier = 100
        self.failure = None
        self.default_source = "synthetic-human.monitor"

    def items(self, kind):
        return getattr(self, kind)

    def call(self, *arguments):
        self.calls.append(arguments)
        if self.failure == arguments[0]:
            raise RuntimeError("injected Pulse failure")
        if arguments[0] == "get-default-source":
            return self.default_source
        if arguments[0] == "load-module":
            identifier = self.next_identifier
            self.next_identifier += 1
            self.modules.append(
                {
                    "index": identifier,
                    "name": arguments[1],
                    "argument": " ".join(arguments[2:]),
                }
            )
            for argument in arguments[2:]:
                if argument.startswith("sink_name="):
                    self.sinks.append(
                        {"name": argument.split("=", 1)[1], "owner": identifier}
                    )
                if argument.startswith("source_name="):
                    self.sources.append(
                        {"name": argument.split("=", 1)[1], "owner": identifier}
                    )
            return str(identifier)
        if arguments[0] == "unload-module":
            identifier = int(arguments[1])
            self.modules = [
                item for item in self.modules if item["index"] != identifier
            ]
            self.sinks = [
                item for item in self.sinks if item.get("owner") != identifier
            ]
            self.sources = [
                item for item in self.sources if item.get("owner") != identifier
            ]
        return ""
