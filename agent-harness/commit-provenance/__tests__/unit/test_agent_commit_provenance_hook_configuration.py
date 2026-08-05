from subprocess import CompletedProcess
from unittest.mock import patch

import record_agent_commit_provenance_trailers as hook


def configuration_output(*entries: str):
    return CompletedProcess(
        args=[], returncode=0, stdout="".join(f"{entry}\0" for entry in entries)
    )


class TestRepositoryProvenanceConfiguration:
    def test_an_unconfigured_repository_records_and_treats_hashes_as_comments(self):
        with patch.object(
            hook.subprocess, "run", return_value=configuration_output()
        ) as configuration_read:
            assert hook.repository_provenance_configuration() == (True, "#")
        assert configuration_read.call_count == 1

    def test_a_repository_can_disable_recording(self):
        with patch.object(
            hook.subprocess,
            "run",
            return_value=configuration_output("agent.provenance.enabled\nfalse"),
        ):
            provenance_is_enabled, _comment_character = (
                hook.repository_provenance_configuration()
            )
        assert provenance_is_enabled is False

    def test_a_custom_comment_character_is_honoured(self):
        with patch.object(
            hook.subprocess,
            "run",
            return_value=configuration_output("core.commentchar\n;"),
        ):
            _provenance_is_enabled, comment_character = (
                hook.repository_provenance_configuration()
            )
        assert comment_character == ";"

    def test_automatic_comment_character_falls_back_to_the_hash(self):
        with patch.object(
            hook.subprocess,
            "run",
            return_value=configuration_output("core.commentchar\nauto"),
        ):
            _provenance_is_enabled, comment_character = (
                hook.repository_provenance_configuration()
            )
        assert comment_character == "#"


class TestMessageFileCarriesAMessage:
    def test_a_template_of_comments_alone_carries_nothing(self, tmp_path):
        message_file_path = tmp_path / "COMMIT_EDITMSG"
        message_file_path.write_text("\n# Please enter a message.\n", encoding="utf-8")
        assert hook.message_file_carries_a_message(message_file_path, "#") is False

    def test_a_subject_makes_the_message_real(self, tmp_path):
        message_file_path = tmp_path / "COMMIT_EDITMSG"
        message_file_path.write_text("feat: a subject\n\n# hint\n", encoding="utf-8")
        assert hook.message_file_carries_a_message(message_file_path, "#") is True

    def test_the_configured_comment_character_decides_what_is_a_comment(self, tmp_path):
        message_file_path = tmp_path / "COMMIT_EDITMSG"
        message_file_path.write_text("; a comment\n", encoding="utf-8")
        assert hook.message_file_carries_a_message(message_file_path, ";") is False
        assert hook.message_file_carries_a_message(message_file_path, "#") is True
