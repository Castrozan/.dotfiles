import json
from pathlib import Path


class MigrationJournal:
    def __init__(self, directory, plan):
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700)
        self.index = 0
        self.result = {
            "status": "starting",
            "pane_identifier": plan.get("pane_identifier"),
            "thread_identifier": plan.get("thread_identifier"),
        }
        (self.directory / "old-processes.json").write_text(
            json.dumps(plan.get("old_processes"), indent=2) + "\n"
        )
        self.save()

    def save(self):
        text = json.dumps(self.result, indent=2) + "\n"
        with (self.directory / f"event-{self.index:04d}.json").open("x") as stream:
            stream.write(text)
        self.index += 1
        temporary = self.directory / "result.json.tmp"
        temporary.write_text(text)
        temporary.replace(self.directory / "result.json")

    def phase(self, name):
        self.result["phase"] = name
        self.save()
