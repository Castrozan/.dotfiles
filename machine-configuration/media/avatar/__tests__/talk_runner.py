import sys

import talk_cli


def run_talk(monkeypatch, directory, *arguments):
    monkeypatch.setattr(sys, "argv", ["avatar-talk", *arguments])
    monkeypatch.setattr(
        talk_cli.listener_runtime, "runtime_directory", lambda: directory
    )
    talk_cli.main()
