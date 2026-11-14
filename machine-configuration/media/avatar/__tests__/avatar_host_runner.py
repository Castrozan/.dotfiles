from types import SimpleNamespace
from unittest.mock import Mock

import mac_wake_boundaries


def ran(monkeypatch, stdout):
    runner = Mock(return_value=SimpleNamespace(stdout=stdout.encode(), returncode=0))
    monkeypatch.setattr(mac_wake_boundaries.subprocess, "run", runner)
    return runner


def remote_command(runner):
    return runner.call_args.args[0][-1]
