from conversation_actions import DispatchCommandAction, LogTranscriptionAction
from hey_bot_daemon_fakes import build_daemon, signal_file_paths
from signal_files import SignalFiles


def test_a_chunk_is_processed_while_the_next_one_records(tmp_path):
    harness = build_daemon(
        tmp_path,
        transcriptions=["the coffee machine is running"],
        stop_after_sleeps=2,
    )

    harness.daemon.run()

    assert harness.transcriber.transcribed_chunks == [harness.capture.created_chunks[0]]
    assert harness.capture.recordings[0].waited is True
    assert LogTranscriptionAction("the coffee machine is running") in (
        harness.actions.performed
    )


def test_every_processed_chunk_file_is_removed(tmp_path):
    harness = build_daemon(
        tmp_path, transcriptions=["one two three"], stop_after_sleeps=3
    )

    harness.daemon.run()

    assert [chunk for chunk in harness.capture.created_chunks if chunk.exists()] == []


def test_the_recording_still_running_at_shutdown_is_stopped(tmp_path):
    harness = build_daemon(tmp_path, stop_after_sleeps=1)

    harness.daemon.run()

    assert harness.capture.recordings[-1].terminated is True


def test_a_chunk_below_the_energy_threshold_is_never_transcribed(tmp_path):
    harness = build_daemon(tmp_path, chunk_has_audio=False, stop_after_sleeps=2)

    harness.daemon.run()

    assert harness.transcriber.transcribed_chunks == []
    assert harness.actions.performed == []


def test_shutdown_waits_for_a_command_the_gateway_is_still_answering(tmp_path):
    harness = build_daemon(tmp_path, stop_after_sleeps=1)

    harness.daemon.run()

    assert harness.background_commands.waited_for_completion is True


def test_a_dispatched_command_reaches_the_background_runner(tmp_path):
    harness = build_daemon(
        tmp_path,
        transcriptions=[
            "hey clever what is the weather",
            "in florianopolis today",
            "",
            "",
            "",
        ],
        stop_after_sleeps=6,
    )

    harness.daemon.run()

    assert DispatchCommandAction(
        "hey clever what is the weather in florianopolis today"
    ) in (harness.actions.performed)


def test_a_restarted_daemon_clears_the_signals_the_previous_run_left(tmp_path):
    paths = signal_file_paths(tmp_path)
    paths.followup_flag.touch()
    paths.wait_context.write_text("a stale command\n", encoding="utf-8")
    harness = build_daemon(tmp_path, signal_files=SignalFiles(paths))

    harness.daemon.run()

    assert not paths.followup_flag.exists()
    assert not paths.wait_context.exists()


def test_the_listening_announcement_names_the_keyword_pattern(tmp_path):
    harness = build_daemon(tmp_path)

    harness.daemon.run()

    assert harness.console.lines == [
        "hey-bot: listening for keywords matching: clever|jarvis"
    ]
