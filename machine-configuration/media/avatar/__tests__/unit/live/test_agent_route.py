import asyncio
import os
import stat

import agent_route
from agent_route import AgentAnswer, ask_agent, spoken_answer


def test_the_spoken_answer_is_the_agents_last_marked_line():
    output = "⏺ Bash(nproc)\n  12\n⏺ This machine has 12 cores.\n"
    assert spoken_answer(output) == (
        "This machine has 12 cores.",
        "⏺ This machine has 12 cores.",
    )


def test_output_without_a_marked_line_has_no_answer():
    assert spoken_answer("a2a: unknown agent 'wW:p00'\n") == (
        None,
        "a2a: unknown agent 'wW:p00'",
    )


def fake_a2a(tmp_path, monkeypatch, script):
    executable = tmp_path / "a2a"
    executable.write_text(f"#!/bin/sh\n{script}\n")
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")


def test_the_task_reaches_the_named_pane_and_its_answer_comes_back(
    tmp_path, monkeypatch
):
    fake_a2a(
        tmp_path,
        monkeypatch,
        'printf "%s\\n" "$@" > "$(dirname "$0")/arguments"; echo "⏺ Done, main is clean."',
    )
    answer = asyncio.run(ask_agent("wW:pQZ", "is my repo clean?"))
    arguments = (tmp_path / "arguments").read_text().splitlines()
    assert arguments[:6] == [
        "ask",
        "--sender",
        agent_route.SENDER,
        "--timeout-seconds",
        str(agent_route.TIMEOUT_SECONDS),
        "wW:pQZ",
    ]
    assert "is my repo clean?" in arguments[6]
    assert answer.text == "Done, main is clean."
    assert answer.succeeded


def test_a_refused_task_is_spoken_as_a_failure(tmp_path, monkeypatch):
    fake_a2a(tmp_path, monkeypatch, "echo 'peer is busy with task 42'; exit 1")
    answer = asyncio.run(ask_agent("wW:pQZ", "anything"))
    assert answer == AgentAnswer(
        "The agent could not finish that: peer is busy with task 42",
        answer.seconds,
        False,
    )
