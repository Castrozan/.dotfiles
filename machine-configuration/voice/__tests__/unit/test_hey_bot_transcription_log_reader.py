import os

from hey_bot_boundary_fakes import RecordingConsole
from hey_bot.transcription_log_reader import TranscriptionLogReader


def write_log_file(directory, name, contents, modified_at):
    log_file = directory / name
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text(contents, encoding="utf-8")
    os.utime(log_file, (modified_at, modified_at))
    return log_file


def read_transcription_logs(directory, follow=False):
    console = RecordingConsole()
    followed = []
    exit_code = TranscriptionLogReader(
        directory, console, follow_log_file=followed.append
    ).run(follow)
    return exit_code, console, followed


def test_an_empty_transcription_directory_is_reported_instead_of_dying(tmp_path):
    exit_code, console, _followed = read_transcription_logs(tmp_path)

    assert exit_code == 1
    assert console.lines == [f"No transcription logs found in {tmp_path}"]


def test_a_missing_transcription_directory_is_reported_the_same_way(tmp_path):
    missing_directory = tmp_path / "never-created"

    exit_code, console, _followed = read_transcription_logs(missing_directory)

    assert exit_code == 1
    assert console.lines == [f"No transcription logs found in {missing_directory}"]


def test_files_that_are_not_transcription_logs_are_ignored(tmp_path):
    write_log_file(tmp_path, "notes.txt", "not a log\n", 1_760_000_000)

    exit_code, console, _followed = read_transcription_logs(tmp_path)

    assert exit_code == 1
    assert console.lines == [f"No transcription logs found in {tmp_path}"]


def test_the_newest_log_is_printed(tmp_path):
    write_log_file(tmp_path, "2026-08-20_10-00-00.log", "the older\n", 1_760_000_000)
    write_log_file(tmp_path, "current.log", "the newest\n", 1_770_000_000)

    exit_code, console, _followed = read_transcription_logs(tmp_path)

    assert exit_code == 0
    assert console.written_text == ["the newest\n"]


def test_only_the_top_level_of_the_transcription_directory_is_read(tmp_path):
    write_log_file(
        tmp_path, "archive/2026-08-22_10-00-00.log", "the archived\n", 1_780_000_000
    )
    write_log_file(tmp_path, "current.log", "the newest\n", 1_770_000_000)

    exit_code, console, _followed = read_transcription_logs(tmp_path)

    assert exit_code == 0
    assert console.written_text == ["the newest\n"]


def test_the_newest_log_is_followed_when_asked(tmp_path):
    newest = write_log_file(tmp_path, "current.log", "the newest\n", 1_770_000_000)

    exit_code, console, followed = read_transcription_logs(tmp_path, follow=True)

    assert exit_code == 0
    assert followed == [newest]
    assert console.written_text == []
