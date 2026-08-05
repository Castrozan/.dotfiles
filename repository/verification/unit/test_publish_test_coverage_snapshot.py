import pytest

from ingestion_snapshot_publisher import IngestionRefusedError
from publish_test_coverage_snapshot import (
    DOTFILES_TEST_COVERAGE_SCHEMA_VERSION,
    DOTFILES_TEST_COVERAGE_TOPIC,
    build_test_coverage_payload,
)

WORKSPACE_ENVIRONMENT = {
    "GITHUB_WORKSPACE": "/home/runner/work/.dotfiles/.dotfiles",
    "GITHUB_SHA": "9a7b1f32",
}

KCOV_DOCUMENT = {
    "percent_covered": "38.62",
    "covered_lines": 61,
    "total_lines": 169,
    "command": "bats",
    "date": "2026-07-24 21:08:44",
    "percent_low": 25,
    "percent_high": 75,
    "files": [
        {
            "file": "/home/runner/work/.dotfiles/.dotfiles/home/base/security/scripts/bw-session.sh",
            "percent_covered": "100.00",
            "covered_lines": "28",
            "total_lines": "28",
        },
        {
            "file": "/home/runner/work/.dotfiles/.dotfiles/home/base/system/scripts/rebuild",
            "percent_covered": "22.40",
            "covered_lines": "28",
            "total_lines": "125",
        },
        {
            "file": "/home/runner/work/.dotfiles/.dotfiles/machine-configuration/terminal/multiplexer/tmux/scripts/tmux-restore-pane-after-toggle",
            "percent_covered": "31.25",
            "covered_lines": "5",
            "total_lines": "16",
        },
    ],
}


class TestKcovDocumentIsMappedOntoTheContractPayload:
    def test_names_the_topic_and_schema_version_the_api_serves(self):
        assert DOTFILES_TEST_COVERAGE_TOPIC == "dotfiles-test-coverage"
        assert DOTFILES_TEST_COVERAGE_SCHEMA_VERSION == 1

    def test_stamps_the_naive_kcov_date_as_the_utc_instant_it_is(self):
        payload = build_test_coverage_payload(KCOV_DOCUMENT, WORKSPACE_ENVIRONMENT)

        assert payload["recordedAt"] == "2026-07-24T21:08:44Z"

    def test_carries_the_run_totals_and_the_commit_the_run_measured(self):
        payload = build_test_coverage_payload(KCOV_DOCUMENT, WORKSPACE_ENVIRONMENT)

        assert payload["commit"] == "9a7b1f32"
        assert payload["coveredLines"] == 61
        assert payload["measurableLines"] == 169

    def test_computes_the_rate_from_the_counts_rather_than_trusting_the_printed_one(
        self,
    ):
        payload = build_test_coverage_payload(KCOV_DOCUMENT, WORKSPACE_ENVIRONMENT)

        assert payload["lineCoverageRate"] == round(61 / 169, 4)

    def test_turns_the_absolute_workspace_paths_into_repository_relative_ones(self):
        payload = build_test_coverage_payload(KCOV_DOCUMENT, WORKSPACE_ENVIRONMENT)

        assert [entry["path"] for entry in payload["files"]] == [
            "home/base/security/scripts/bw-session.sh",
            "home/base/system/scripts/rebuild",
            "machine-configuration/terminal/multiplexer/tmux/scripts/tmux-restore-pane-after-toggle",
        ]

    def test_reads_the_string_line_counts_kcov_writes_as_numbers(self):
        payload = build_test_coverage_payload(KCOV_DOCUMENT, WORKSPACE_ENVIRONMENT)
        rebuild_script = payload["files"][1]

        assert rebuild_script["coveredLines"] == 28
        assert rebuild_script["measurableLines"] == 125
        assert rebuild_script["lineCoverageRate"] == round(28 / 125, 4)

    def test_drops_a_file_kcov_found_no_measurable_line_in(self):
        document = {
            **KCOV_DOCUMENT,
            "files": [
                *KCOV_DOCUMENT["files"],
                {
                    "file": "/home/runner/work/.dotfiles/.dotfiles/home/base/empty.sh",
                    "percent_covered": "0.00",
                    "covered_lines": "0",
                    "total_lines": "0",
                },
            ],
        }

        payload = build_test_coverage_payload(document, WORKSPACE_ENVIRONMENT)

        assert len(payload["files"]) == 3

    def test_emits_no_key_the_contract_does_not_declare(self):
        payload = build_test_coverage_payload(KCOV_DOCUMENT, WORKSPACE_ENVIRONMENT)

        assert set(payload) == {
            "recordedAt",
            "commit",
            "coveredLines",
            "measurableLines",
            "lineCoverageRate",
            "files",
        }
        assert set(payload["files"][0]) == {
            "path",
            "coveredLines",
            "measurableLines",
            "lineCoverageRate",
        }


class TestUnmappablePathsAreRefusedRatherThanGuessed:
    def test_refuses_a_measured_file_outside_the_checkout(self):
        document = {
            **KCOV_DOCUMENT,
            "files": [
                {
                    "file": "/nix/store/abc/bin/some-tool",
                    "percent_covered": "50.00",
                    "covered_lines": "1",
                    "total_lines": "2",
                }
            ],
        }

        with pytest.raises(IngestionRefusedError, match="some-tool"):
            build_test_coverage_payload(document, WORKSPACE_ENVIRONMENT)

    def test_refuses_a_run_that_does_not_name_the_commit_it_measured(self):
        with pytest.raises(IngestionRefusedError, match="GITHUB_SHA"):
            build_test_coverage_payload(
                KCOV_DOCUMENT,
                {"GITHUB_WORKSPACE": "/home/runner/work/.dotfiles/.dotfiles"},
            )
