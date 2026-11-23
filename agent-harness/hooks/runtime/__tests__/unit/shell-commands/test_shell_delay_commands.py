import shlex

import pytest
import shell_delay_durations as durations
from shell_delay_commands import delays_in_shell_text


def delay_summary(shell_text):
    return [
        (delay.seconds, None if delay.loop is None else delay.loop.polls)
        for delay in delays_in_shell_text(shell_text)
    ]


@pytest.mark.parametrize(
    ("duration_words", "seconds"),
    [(["5"], 5.0), ([".25"], 0.25), (["1m"], 60.0), (["1", "2s"], 3.0), (["$D"], None)],
)
def test_sleep_durations_add_up_and_unknown_ones_stay_unknown(duration_words, seconds):
    assert durations.sleep_seconds(duration_words) == seconds


@pytest.mark.parametrize(
    "shell_text", ["sleep infinity", "sleep inf &", "sleep --help", "sleep"]
)
def test_a_keep_alive_or_help_sleep_is_not_a_delay(shell_text):
    assert delays_in_shell_text(shell_text) == []


@pytest.mark.parametrize(
    ("shell_text", "summary"),
    [
        ("sleep 30; gh run list", [(30.0, None)]),
        ("until test -f x; do sleep 2; done", [(2.0, True)]),
        ("while sleep 0.5; do date; done", [(0.5, True)]),
        ("for i in $(seq 1 9); do sleep 0.2; done", [(0.2, True)]),
        ("for i in {1..9}; do sleep 0.2; done", [(0.2, True)]),
        ("for p in a b; do sleep 0.2; done", [(0.2, False)]),
        ("for p in a b; do check && break; sleep 0.2; done", [(0.2, True)]),
        ("for p in a b; do :; done; sleep 0.2", [(0.2, None)]),
        ("watch -n 5 gh run list", [(5.0, True)]),
        ("timeout 60 bash -c 'until test -f x; do sleep 1; done'", [(1.0, True)]),
        ("until test -f x; do bash -c 'sleep 4'; done", [(4.0, True)]),
        ("nohup env A=1 sleep 9 &", [(9.0, None)]),
    ],
)
def test_each_delay_knows_its_duration_and_whether_a_loop_polls_with_it(
    shell_text, summary
):
    assert delay_summary(shell_text) == summary


@pytest.mark.parametrize(
    ("program_text", "summary"),
    [
        ("import time;time.sleep(8)", [(8.0, None)]),
        ("import time\ntime.sleep(0.3)", [(0.3, None)]),
        ("from time import sleep; sleep(n)", [(None, None)]),
        ("import time; press(); time.sleep(2); release()", []),
        ("import json; print(json.dumps({}))", []),
    ],
)
def test_only_a_python_program_that_does_nothing_but_sleep_is_a_delay(
    program_text, summary
):
    assert delay_summary(f"python3 -c {shlex.quote(program_text)}") == summary
