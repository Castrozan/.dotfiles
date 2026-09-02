import re
import time
from datetime import datetime, timezone

import pytest

from local_time import instant_from_stamp, local_time_line, main


@pytest.fixture
def sao_paulo_clock(monkeypatch):
    monkeypatch.setenv("TZ", "America/Sao_Paulo")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


def test_gitlab_utc_stamp_lands_three_hours_earlier(sao_paulo_clock):
    line = local_time_line(instant_from_stamp("2026-09-02T18:53:47.201Z"))
    assert line.startswith("2026-09-02 15:53:47 ")
    assert line.endswith("(Wednesday)")


def test_jira_offset_stamp_keeps_its_wall_time(sao_paulo_clock):
    line = local_time_line(instant_from_stamp("2026-09-02T15:53:46.568-0300"))
    assert line.startswith("2026-09-02 15:53:46 ")


def test_epoch_seconds_convert_like_a_utc_stamp(sao_paulo_clock):
    epoch = int(datetime(2026, 9, 2, 18, 53, 47, tzinfo=timezone.utc).timestamp())
    line = local_time_line(instant_from_stamp(str(epoch)))
    assert line.startswith("2026-09-02 15:53:47 ")


def test_iso_output_carries_the_local_offset(sao_paulo_clock, capsys):
    assert main(["--iso", "2026-09-02T18:53:47.201Z"]) == 0
    assert capsys.readouterr().out == "2026-09-02T15:53:47-03:00\n"


def test_naive_stamp_is_refused(capsys):
    assert main(["2026-09-02T18:53:47"]) == 2
    assert "no zone" in capsys.readouterr().err


def test_unparseable_stamp_is_refused(capsys):
    assert main(["yesterday"]) == 2
    assert "cannot parse 'yesterday'" in capsys.readouterr().err


def test_no_argument_prints_now(capsys):
    assert main([]) == 0
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \S+ \([A-Z][a-z]+\)\n",
        capsys.readouterr().out,
    )


def test_help_prints_usage(capsys):
    assert main(["--help"]) == 0
    assert capsys.readouterr().out.startswith("usage: local-time")
