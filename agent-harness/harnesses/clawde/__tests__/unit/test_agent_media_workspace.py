import json
import os
import time
from datetime import date

import pytest

from agent_media_workspace import (
    RETENTION_DAYS,
    USAGE_FILE_NAME,
    MediaRequestRefused,
    claim_daily_allowance,
    flatten_prompt,
    read_api_key,
    resolve_media_directory,
    write_media_file,
)

TODAY = date(2026, 8, 15)


def test_media_lands_in_the_workspace_that_asked_for_it(media_agent_workspace):
    assert resolve_media_directory(media_agent_workspace) == media_agent_workspace / "media"


def test_a_directory_outside_the_agent_tree_owns_no_media(tmp_path, media_agent_workspace):
    with pytest.raises(MediaRequestRefused, match="only an agent workspace"):
        resolve_media_directory(tmp_path)


def test_an_api_key_is_read_from_the_secrets_directory(media_secrets_directory):
    (media_secrets_directory / "gemini-api-key").write_text("  key-value\n", encoding="utf-8")

    assert read_api_key("gemini-api-key") == "key-value"


def test_a_machine_without_the_key_refuses_in_plain_language(media_secrets_directory):
    with pytest.raises(MediaRequestRefused, match="holds no gemini-api-key"):
        read_api_key("gemini-api-key")


def test_a_prompt_is_flattened_to_one_line():
    assert flatten_prompt("  gato   a\njato ", 40) == "gato a jato"


def test_an_empty_prompt_is_refused():
    with pytest.raises(MediaRequestRefused, match="empty prompt"):
        flatten_prompt("   \n ", 40)


def test_an_oversized_prompt_is_refused():
    with pytest.raises(MediaRequestRefused, match="keep it under 10"):
        flatten_prompt("x" * 11, 10)


def test_each_use_counts_against_the_day(media_agent_workspace):
    media_directory = media_agent_workspace / "media"

    assert claim_daily_allowance(media_directory, "image", 3, TODAY) == 1
    assert claim_daily_allowance(media_directory, "image", 3, TODAY) == 2
    assert json.loads(
        (media_directory / USAGE_FILE_NAME).read_text(encoding="utf-8")
    ) == {"2026-08-15": {"image": 2}}


def test_a_spent_day_is_refused_until_tomorrow(media_agent_workspace):
    media_directory = media_agent_workspace / "media"
    claim_daily_allowance(media_directory, "voice", 1, TODAY)

    with pytest.raises(MediaRequestRefused, match="budget is spent"):
        claim_daily_allowance(media_directory, "voice", 1, TODAY)

    assert claim_daily_allowance(media_directory, "voice", 1, date(2026, 8, 16)) == 1


def test_budgets_are_counted_per_kind(media_agent_workspace):
    media_directory = media_agent_workspace / "media"
    claim_daily_allowance(media_directory, "image", 1, TODAY)

    assert claim_daily_allowance(media_directory, "voice", 1, TODAY) == 1


def test_a_corrupt_usage_file_does_not_block_the_day(media_agent_workspace):
    media_directory = media_agent_workspace / "media"
    media_directory.mkdir()
    (media_directory / USAGE_FILE_NAME).write_text("not json", encoding="utf-8")

    assert claim_daily_allowance(media_directory, "image", 2, TODAY) == 1


def test_writing_media_prunes_what_discord_already_holds(media_agent_workspace):
    media_directory = media_agent_workspace / "media"
    media_directory.mkdir()
    stale = media_directory / "image-old.png"
    stale.write_bytes(b"old")
    expired_at = time.time() - (RETENTION_DAYS + 1) * 86400
    os.utime(stale, (expired_at, expired_at))

    fresh = write_media_file(media_directory, "image", ".png", b"new")

    assert fresh.read_bytes() == b"new"
    assert not stale.exists()


def test_the_usage_record_survives_pruning(media_agent_workspace):
    media_directory = media_agent_workspace / "media"
    claim_daily_allowance(media_directory, "image", 2, TODAY)
    usage_file = media_directory / USAGE_FILE_NAME
    expired_at = time.time() - (RETENTION_DAYS + 1) * 86400
    os.utime(usage_file, (expired_at, expired_at))

    write_media_file(media_directory, "image", ".png", b"new")

    assert usage_file.exists()
