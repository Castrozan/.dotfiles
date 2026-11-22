import json
import os
import stat

import agent_route

FAKE_A2A = """#!/bin/sh
here="$(dirname "$0")"
case "$1" in
  send) printf "%s\\n" "$@" > "$here/sent"; {send} ;;
  status) {status} ;;
esac
"""


def install_a2a(tmp_path, monkeypatch, send="echo task-7", status='cat "$here/task"'):
    executable = tmp_path / "a2a"
    executable.write_text(FAKE_A2A.format(send=send, status=status))
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(agent_route, "POLL_SECONDS", 0)
    monkeypatch.setattr(agent_route, "STILL_WORKING_SECONDS", 0.2)
    monkeypatch.setattr(agent_route, "ANSWER_DEADLINE_SECONDS", 1)


def pane_reports(tmp_path, state, output):
    (tmp_path / "task").write_text(
        json.dumps({"id": "task-7", "state": state, "output": output})
    )


def sent_arguments(tmp_path):
    return (tmp_path / "sent").read_text().splitlines()
