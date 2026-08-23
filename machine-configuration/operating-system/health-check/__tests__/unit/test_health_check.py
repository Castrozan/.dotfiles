from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HEALTH_CHECK_SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts" / "health_check.py"
)
PASS_THROUGH_TIMEOUT = (
    "#!/usr/bin/env bash\n"
    'printf "%s\\n" "$*" >>"$FAKE_TIMEOUT_CALL_LOG"\n'
    "shift\n"
    'exec "$@"\n'
)


def probe(category, name, body, applicable_when=None):
    return {
        "category": category,
        "name": name,
        "probe": body,
        "applicableWhen": applicable_when,
    }


@pytest.fixture
def fake_command_directory(tmp_path):
    directory = tmp_path / "fake-bin"
    directory.mkdir()
    fake_timeout = directory / "timeout"
    fake_timeout.write_text(PASS_THROUGH_TIMEOUT)
    fake_timeout.chmod(0o755)
    return directory


@pytest.fixture
def run_health_check(tmp_path, fake_command_directory):
    call_log = tmp_path / "timeout-calls.log"

    def run(probes, *arguments, probe_timeout_seconds="10"):
        definitions = tmp_path / "probes.json"
        definitions.write_text(json.dumps(probes))
        environment = dict(os.environ)
        environment["PATH"] = (
            f"{fake_command_directory}{os.pathsep}{environment['PATH']}"
        )
        environment["HEALTH_CHECK_PROBE_TIMEOUT_SECONDS"] = probe_timeout_seconds
        environment["FAKE_TIMEOUT_CALL_LOG"] = str(call_log)
        return subprocess.run(
            [sys.executable, str(HEALTH_CHECK_SCRIPT), str(definitions), *arguments],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )

    run.call_log = call_log
    return run


class TestProbeStatuses:
    def test_renders_a_symbol_and_colour_for_every_status(self, run_health_check):
        completed = run_health_check(
            [
                probe("bin", "live", "true"),
                probe("daemon", "broken", "false"),
                probe("config", "dormant", "true", "echo not scheduled; exit 1"),
            ]
        )
        assert completed.stdout.splitlines()[:3] == [
            "  \033[32m✓\033[0m [bin   ] live",
            "  \033[31m✗\033[0m [daemon] broken",
            "  \033[90m-\033[0m [config] dormant (not scheduled)",
        ]
        assert completed.returncode == 1

    def test_a_silent_applicability_check_skips_with_a_default_reason(
        self, run_health_check
    ):
        completed = run_health_check([probe("misc", "quiet", "true", "exit 3")])
        assert "[misc  ] quiet (not applicable)" in completed.stdout
        assert completed.returncode == 0

    def test_a_timed_out_applicability_check_fails_the_probe(self, run_health_check):
        completed = run_health_check(
            [probe("app", "hung gate", "true", "exit 124")], probe_timeout_seconds="3"
        )
        assert "hung gate (applicability check timed out after 3s)" in completed.stdout
        assert completed.returncode == 1

    def test_a_timed_out_probe_body_reports_the_configured_seconds(
        self, run_health_check
    ):
        completed = run_health_check(
            [probe("nix", "slow", "exit 124")], probe_timeout_seconds="7"
        )
        assert "slow (timed out after 7s)" in completed.stdout
        assert completed.returncode == 1

    def test_both_bodies_run_through_bash_under_the_configured_timeout(
        self, run_health_check
    ):
        run_health_check(
            [probe("bin", "gated", "true", "exit 0")], probe_timeout_seconds="4"
        )
        assert run_health_check.call_log.read_text().splitlines() == [
            "4 bash -c exit 0",
            "4 bash -c true",
        ]


class TestOutputModes:
    def test_json_mode_omits_reason_until_there_is_one(self, run_health_check):
        completed = run_health_check(
            [
                probe("bin", 'quoted "name"', "true"),
                probe("config", "dormant", "true", "echo weekend; exit 1"),
            ],
            "--json",
        )
        assert json.loads(completed.stdout) == [
            {"category": "bin", "name": 'quoted "name"', "status": "pass"},
            {
                "category": "config",
                "name": "dormant",
                "status": "skip",
                "reason": "weekend",
            },
        ]

    def test_summary_mode_counts_every_status_on_one_line(self, run_health_check):
        completed = run_health_check(
            [
                probe("bin", "live", "true"),
                probe("daemon", "broken", "false"),
                probe("config", "dormant", "true", "exit 1"),
            ],
            "--summary",
        )
        assert completed.stdout == "health-check: 1 pass, 1 fail, 1 skip\n"

    @pytest.mark.parametrize(
        ("probes", "expected_totals"),
        [
            ([probe("bin", "live", "true")], "1/1 passed (0 failed)"),
            (
                [probe("bin", "live", "true"), probe("misc", "off", "true", "exit 1")],
                "1/1 passed (0 failed, 1 skipped)",
            ),
        ],
    )
    def test_the_totals_line_only_mentions_skips_when_some_happened(
        self, run_health_check, probes, expected_totals
    ):
        completed = run_health_check(probes)
        assert completed.stdout.endswith(f"\n{expected_totals}\n")


class TestArgumentParsing:
    @pytest.mark.parametrize(
        "category_arguments",
        [("--category", "bin"), ("--category=bin",), ("--category=bin,nix",)],
    )
    def test_a_category_filter_keeps_only_the_named_categories(
        self, run_health_check, category_arguments
    ):
        completed = run_health_check(
            [probe("bin", "kept", "true"), probe("daemon", "dropped", "true")],
            *category_arguments,
        )
        assert "kept" in completed.stdout
        assert "dropped" not in completed.stdout

    def test_help_documents_the_active_timeout_and_exits_zero(self, run_health_check):
        completed = run_health_check([], "--help", probe_timeout_seconds="30")
        assert completed.stdout.startswith("Usage: health-check ")
        assert "Every probe is bounded at 30s" in completed.stdout
        assert completed.returncode == 0

    def test_an_unknown_argument_exits_two(self, run_health_check):
        completed = run_health_check([], "--bogus")
        assert completed.stderr == "unknown arg: --bogus\n"
        assert completed.returncode == 2
