import json

from orchestration_test_support import (
    heartbeat_text,
    run_orchestrator,
    valid_card_document,
)

ORCHESTRATOR = "orchestrator-session"
RELEASED_PANE = "worker-pane"
REPORT = {
    "goal": "retire hey-bot into the avatar",
    "state": "done",
    "done_when": "hey-bot is gone",
    "doing": "wake word ported",
    "next": "nothing",
}


class ReleaseScenario:
    def __init__(self, monkeypatch, tmp_path, notifications, capsys):
        self.monkeypatch = monkeypatch
        self.cards = tmp_path / "cards"
        self.reports = tmp_path / "reports"
        self.notifications = notifications
        self.capsys = capsys

    def run(self, location, *arguments, **options):
        return run_orchestrator(self.monkeypatch, location, *arguments, **options)

    def handover(self, *flags):
        arguments = [RELEASED_PANE, "--for", ORCHESTRATOR]
        arguments += ["--heartbeats-dir", str(self.reports), *flags]
        return self.run(self.cards, *arguments, command="handover")

    def file_heartbeat(self, **overrides):
        document = heartbeat_text(**{**REPORT, **overrides})
        arguments = ["file", "--to", ORCHESTRATOR]
        return self.run(
            self.reports, *arguments, stdin_text=document, command="heartbeat"
        )

    def file_card(self):
        document = json.dumps(valid_card_document())
        return self.run(self.cards, "file", "--to", ORCHESTRATOR, stdin_text=document)

    def round_output(self):
        self.capsys.readouterr()
        arguments = ["--for", ORCHESTRATOR, "--heartbeats-dir", str(self.reports)]
        assert self.run(self.cards, *arguments, command="round") == 0
        return self.capsys.readouterr().out

    def errors(self):
        return self.capsys.readouterr().err


def records(directory):
    return [json.loads(path.read_text()) for path in sorted(directory.glob("*.json"))]
