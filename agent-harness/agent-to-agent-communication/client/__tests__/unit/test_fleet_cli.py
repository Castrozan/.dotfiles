import json
import sys
import pytest
from a2a_cli.fleet import operations
from a2a_cli.fleet.cli import command_fleet
from a2a_cli.fleet.registry import Registry
from a2a_cli.__main__ import build_argument_parser
from fleet_test_support import inventory


def test_remote_quoting_and_security_options():
    argv = operations.command_argv(
        {"transport": "confirmed-peer"},
        ["a2a", "send", "w1:p1", "literal $(touch /tmp/nope) ' text"],
    )
    assert argv[-2] == "confirmed-peer"
    assert "StrictHostKeyChecking=yes" in argv
    assert "ClearAllForwardings=yes" in argv
    import shlex

    assert shlex.split(argv[-1])[-1] == "literal $(touch /tmp/nope) ' text"


def test_transport_bounds_real_local_child_output_and_time():
    assert (
        operations.run(
            {"transport": "local"}, [sys.executable, "-c", "print('ok')"], timeout=2
        ).strip()
        == "ok"
    )
    with pytest.raises(operations.ObservationError):
        operations.run(
            {"transport": "local"},
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout=0.05,
        )
    with pytest.raises(operations.ObservationError, match="failed"):
        operations.run(
            {"transport": "local"},
            [sys.executable, "-c", "print('x'*3000000)"],
            timeout=2,
        )


def test_cli_cached_status_bypasses_a2a_discovery(tmp_path, capsys, monkeypatch):
    from a2a_cli import __main__

    def forbidden(*args, **kwargs):
        raise AssertionError("cached status must not perform discovery")

    monkeypatch.setattr(__main__, "read_agent_directory", forbidden)
    monkeypatch.setattr(
        sys, "argv", ["a2a", "fleet", "--db", str(tmp_path / "db"), "status"]
    )
    assert __main__.main() == 0
    assert json.loads(capsys.readouterr().out)["agents"] == []


def test_cli_ingest_marks_cached_and_is_quiet(tmp_path, capsys):
    db = tmp_path / "db"
    parser = build_argument_parser()
    assert (
        command_fleet(
            parser.parse_args(
                [
                    "fleet",
                    "--db",
                    str(db),
                    "confirm-host",
                    "test-host",
                    "--transport",
                    "local",
                    "--evidence",
                    "fixture:confirmed",
                ]
            )
        )
        == 0
    )
    directory, snapshot = inventory()
    source = tmp_path / "metadata.json"
    source.write_text(
        json.dumps(
            {
                "a2a": directory,
                "herdr": snapshot,
                "observed_at": 999,
                "evidence": "fixture:import",
            }
        )
    )
    assert (
        command_fleet(
            parser.parse_args(
                ["fleet", "--db", str(db), "ingest", "test-host", str(source)]
            )
        )
        == 0
    )
    assert capsys.readouterr().out == ""
    r = Registry(db)
    try:
        assert r.status()["agents"][0]["source"] == "cached"
    finally:
        r.close()
