import json
import subprocess

import pytest

import ccusage_daily_reader
from ccusage_daily_reader import CcusageCollectionError, read_ccusage_daily_summary

EXPECTED_COMMAND = (
    "ccusage",
    "claude",
    "daily",
    "--json",
    "--breakdown",
    "--offline",
    "--timezone",
    "UTC",
)

CANONICAL_EXPORT = {
    "daily": [
        {
            "date": "2026-06-17",
            "modelBreakdowns": [
                {
                    "modelName": "claude-opus-4-8",
                    "inputTokens": 1,
                    "outputTokens": 2,
                    "cacheReadTokens": 3,
                    "cacheCreationTokens": 4,
                    "cost": 0.5,
                }
            ],
        }
    ]
}


def completed(stdout="", returncode=0):
    return subprocess.CompletedProcess(
        args=EXPECTED_COMMAND, returncode=returncode, stdout=stdout, stderr=""
    )


def stub_ccusage_run(monkeypatch, outcome):
    recorded_calls = []

    def fake_run(command, **keyword_arguments):
        recorded_calls.append((command, keyword_arguments))
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    monkeypatch.setattr(ccusage_daily_reader.subprocess, "run", fake_run)
    return recorded_calls


class TestReadCcusageDailySummary:
    def test_runs_exact_offline_utc_daily_export_with_sixty_second_timeout(
        self, monkeypatch
    ):
        recorded_calls = stub_ccusage_run(
            monkeypatch, completed(json.dumps(CANONICAL_EXPORT))
        )
        read_ccusage_daily_summary()
        [(command, keyword_arguments)] = recorded_calls
        assert command == EXPECTED_COMMAND
        assert "--since" not in command
        assert keyword_arguments["timeout"] == 60

    def test_valid_export_returns_the_summary_of_its_daily_entries(self, monkeypatch):
        stub_ccusage_run(monkeypatch, completed(json.dumps(CANONICAL_EXPORT)))
        summary = read_ccusage_daily_summary()
        assert summary["stats_last_computed_date"] == "2026-06-17"
        assert summary["model_usage_totals"]["claude-opus-4-8"]["cost_usd"] == 0.5

    def test_empty_export_returns_none(self, monkeypatch):
        stub_ccusage_run(monkeypatch, completed(json.dumps({"daily": []})))
        assert read_ccusage_daily_summary() is None

    @pytest.mark.parametrize(
        ("outcome", "message"),
        [
            pytest.param(
                FileNotFoundError("ccusage"),
                "could not be started",
                id="missing-executable",
            ),
            pytest.param(
                PermissionError("ccusage"), "could not be started", id="not-executable"
            ),
            pytest.param(
                subprocess.TimeoutExpired(cmd="ccusage", timeout=60),
                "timed out after 60 seconds",
                id="timeout",
            ),
            pytest.param(
                completed(returncode=1), "exited with status 1", id="nonzero-exit"
            ),
            pytest.param(
                completed(stdout="{not json"), "not valid JSON", id="malformed-json"
            ),
            pytest.param(completed(stdout="[]"), "invalid", id="wrong-document-shape"),
            pytest.param(
                completed(stdout=json.dumps({"daily": [{"date": "2026-6-1"}]})),
                "invalid",
                id="invalid-daily-entry",
            ),
        ],
    )
    def test_every_failure_is_an_explicit_collection_error_not_a_default(
        self, monkeypatch, outcome, message
    ):
        stub_ccusage_run(monkeypatch, outcome)
        with pytest.raises(CcusageCollectionError, match=message):
            read_ccusage_daily_summary()

    def test_collection_error_is_a_runtime_error(self):
        assert issubclass(CcusageCollectionError, RuntimeError)
