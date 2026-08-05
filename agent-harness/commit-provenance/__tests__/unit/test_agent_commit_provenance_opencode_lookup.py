import sqlite3
from pathlib import Path
from unittest.mock import patch

from agent_commit_provenance.opencode_session_lookup import (
    opencode_session_identifier_for_process,
)

STEWARD_DIRECTORY = "/Users/someone/clawde/steward"


def session_database_holding(tmp_path, sessions):
    session_database = tmp_path / "opencode.db"
    connection = sqlite3.connect(session_database)
    connection.execute(
        "create table session (id text, directory text, time_updated int)"
    )
    connection.executemany("insert into session values (?, ?, ?)", sessions)
    connection.commit()
    connection.close()
    return session_database


class TestOpencodeSessionIdentifierForProcess:
    def test_reads_the_session_the_harness_is_working_in(self, tmp_path):
        session_database = session_database_holding(
            tmp_path,
            [
                ("ses_older", STEWARD_DIRECTORY, 1785812411272),
                ("ses_current", STEWARD_DIRECTORY, 1785887179190),
                ("ses_other_agent", "/Users/someone/clawde/coates-pm", 1785887179999),
            ],
        )
        with patch(
            "agent_commit_provenance.opencode_session_lookup.working_directory_of_process",
            return_value=Path(STEWARD_DIRECTORY),
        ):
            assert (
                opencode_session_identifier_for_process(4242, session_database)
                == "ses_current"
            )

    def test_a_directory_with_no_session_resolves_to_nothing(self, tmp_path):
        session_database = session_database_holding(
            tmp_path, [("ses_current", STEWARD_DIRECTORY, 1785887179190)]
        )
        with patch(
            "agent_commit_provenance.opencode_session_lookup.working_directory_of_process",
            return_value=Path("/Users/someone/elsewhere"),
        ):
            assert (
                opencode_session_identifier_for_process(4242, session_database) is None
            )

    def test_a_missing_database_resolves_to_nothing(self, tmp_path):
        assert (
            opencode_session_identifier_for_process(4242, tmp_path / "absent.db")
            is None
        )

    def test_an_unreadable_schema_resolves_to_nothing(self, tmp_path):
        session_database = tmp_path / "opencode.db"
        connection = sqlite3.connect(session_database)
        connection.execute("create table unrelated (id text)")
        connection.commit()
        connection.close()
        with patch(
            "agent_commit_provenance.opencode_session_lookup.working_directory_of_process",
            return_value=Path(STEWARD_DIRECTORY),
        ):
            assert (
                opencode_session_identifier_for_process(4242, session_database) is None
            )

    def test_a_process_without_a_readable_directory_resolves_to_nothing(self, tmp_path):
        session_database = session_database_holding(
            tmp_path, [("ses_current", STEWARD_DIRECTORY, 1785887179190)]
        )
        with patch(
            "agent_commit_provenance.opencode_session_lookup.working_directory_of_process",
            return_value=None,
        ):
            assert (
                opencode_session_identifier_for_process(4242, session_database) is None
            )
