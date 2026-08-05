import json
from unittest.mock import MagicMock, patch

import pytest

import verify_deployed_prohibited_words_allowlist


def test_load_machine_allowed_words_returns_none_without_a_machine_file(tmp_path):
    assert (
        verify_deployed_prohibited_words_allowlist.load_machine_allowed_words(
            tmp_path, "test"
        )
        is None
    )


def test_load_machine_allowed_words_evaluates_the_machine_file(tmp_path):
    allowed_words_file = (
        tmp_path
        / "private-configuration"
        / "machines"
        / "test"
        / "claude-prohibited-words-allowed.nix"
    )
    allowed_words_file.parent.mkdir(parents=True)
    allowed_words_file.write_text('"ignored"\n', encoding="utf-8")

    with patch(
        "verify_deployed_prohibited_words_allowlist.subprocess.run",
        return_value=MagicMock(returncode=0, stdout='["allowed","words"]'),
    ) as subprocess_run:
        allowed_words = (
            verify_deployed_prohibited_words_allowlist.load_machine_allowed_words(
                tmp_path, "test"
            )
        )

    assert allowed_words == ["allowed", "words"]
    assert subprocess_run.call_args.args[0][:5] == [
        "nix",
        "eval",
        "--impure",
        "--json",
        "--expr",
    ]


def test_load_claude_allowed_words_unquotes_an_empty_value(tmp_path):
    settings_source_file = tmp_path / "settings.json"
    settings_source_file.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "hooks": [
                                {
                                    "command": "PROHIBITED_WORDS_ALLOWED='' command dispatcher"
                                }
                            ]
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    assert (
        verify_deployed_prohibited_words_allowlist.load_claude_allowed_words(
            settings_source_file
        )
        == ""
    )


def test_load_claude_allowed_words_rejects_duplicate_assignments(tmp_path):
    settings_source_file = tmp_path / "settings.json"
    settings_source_file.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "hooks": [
                                {
                                    "command": "PROHIBITED_WORDS_ALLOWED=allowed PROHIBITED_WORDS_ALLOWED=different command dispatcher"
                                }
                            ]
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="exactly once"):
        verify_deployed_prohibited_words_allowlist.load_claude_allowed_words(
            settings_source_file
        )


def test_load_codex_allowed_words_reads_the_requirements_file(tmp_path):
    requirements_file = tmp_path / "requirements.toml"
    requirements_file.write_text(
        """
[hooks]
[[hooks.PreToolUse]]
[[hooks.PreToolUse.hooks]]
command = "PROHIBITED_WORDS_ALLOWED=allowed command dispatcher"
""",
        encoding="utf-8",
    )

    assert (
        verify_deployed_prohibited_words_allowlist.load_codex_allowed_words(
            requirements_file
        )
        == "allowed"
    )


def test_verify_deployed_allowed_words_accepts_matching_values(tmp_path):
    with patch(
        "verify_deployed_prohibited_words_allowlist.load_machine_allowed_words",
        return_value=["allowed"],
    ):
        with patch(
            "verify_deployed_prohibited_words_allowlist.load_claude_allowed_words",
            return_value="allowed",
        ) as load_claude_allowed_words:
            with patch(
                "verify_deployed_prohibited_words_allowlist.load_codex_allowed_words",
                return_value="allowed",
            ) as load_codex_allowed_words:
                verify_deployed_prohibited_words_allowlist.verify_deployed_allowed_words(
                    tmp_path,
                    "test",
                    tmp_path / "settings-source.json",
                    tmp_path / "settings.json",
                    tmp_path / "requirements.toml",
                )

    assert load_claude_allowed_words.call_count == 2
    load_codex_allowed_words.assert_called_once()


def test_verify_deployed_allowed_words_rejects_a_mismatch(tmp_path):
    with patch(
        "verify_deployed_prohibited_words_allowlist.load_machine_allowed_words",
        return_value=["allowed"],
    ):
        with patch(
            "verify_deployed_prohibited_words_allowlist.load_claude_allowed_words",
            return_value="different",
        ):
            with patch(
                "verify_deployed_prohibited_words_allowlist.load_codex_allowed_words",
                return_value="allowed",
            ):
                with pytest.raises(RuntimeError, match="does not match"):
                    verify_deployed_prohibited_words_allowlist.verify_deployed_allowed_words(
                        tmp_path,
                        "test",
                        tmp_path / "settings.json",
                        tmp_path / "settings.json",
                        tmp_path / "requirements.toml",
                    )
