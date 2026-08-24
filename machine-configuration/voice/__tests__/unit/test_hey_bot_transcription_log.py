from transcription_log import TranscriptionLog

TIMESTAMPS = {
    "%Y-%m-%d %H:%M:%S": "2026-08-23 19:00:00",
    "%Y-%m-%d_%H-%M-%S": "2026-08-23_19-00-00",
}


def formatted_now(pattern):
    return TIMESTAMPS[pattern]


def build_log(directory, maximum_size_bytes=1048576):
    log = TranscriptionLog(directory, maximum_size_bytes, formatted_now)
    log.prepare_directory()
    return log


def test_the_transcription_directory_is_created_when_it_is_missing(tmp_path):
    directory = tmp_path / "transcriptions"

    build_log(directory)

    assert directory.is_dir()


def test_a_transcription_is_appended_with_its_timestamp(tmp_path):
    log = build_log(tmp_path)

    log.append("the coffee machine is running")

    assert (tmp_path / "current.log").read_text(encoding="utf-8") == (
        "[2026-08-23 19:00:00] the coffee machine is running\n"
    )


def test_an_oversized_current_log_is_rotated_to_a_timestamped_file(tmp_path):
    log = build_log(tmp_path, maximum_size_bytes=8)
    (tmp_path / "current.log").write_text(
        "an older transcription line\n", encoding="utf-8"
    )

    log.append("the coffee machine is running")

    assert (tmp_path / "2026-08-23_19-00-00.log").read_text(encoding="utf-8") == (
        "an older transcription line\n"
    )
    assert "an older" not in (tmp_path / "current.log").read_text(encoding="utf-8")


def test_recent_lines_stop_at_the_last_twenty_entries(tmp_path):
    log = build_log(tmp_path)
    for index in range(25):
        log.append(f"line {index}")

    recent = log.recent_lines().splitlines()

    assert len(recent) == 20
    assert recent[0].endswith("line 5")
    assert recent[-1].endswith("line 24")


def test_recent_lines_are_empty_before_anything_was_logged(tmp_path):
    assert build_log(tmp_path).recent_lines() == ""
