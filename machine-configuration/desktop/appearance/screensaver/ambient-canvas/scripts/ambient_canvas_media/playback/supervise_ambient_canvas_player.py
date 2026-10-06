import codecs
from dataclasses import dataclass
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import threading
import time

from player_diagnostics import (
    OUTPUT_TAIL_BYTES,
    create_diagnostic_logger,
    diagnostic_timestamp,
    write_player_report,
)


PLAYER_OUTPUT_CHUNK_BYTES = 8192
OUTPUT_DRAIN_TIMEOUT_SECONDS = 1


@dataclass
class PlayerOutput:
    tail: bytes = b""


def capture_player_output(output_stream, logger, captured_output):
    output_decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    with output_stream:
        while output_chunk := output_stream.read1(PLAYER_OUTPUT_CHUNK_BYTES):
            captured_output.tail = (captured_output.tail + output_chunk)[
                -OUTPUT_TAIL_BYTES:
            ]
            logger.info(
                "player_output %s", output_decoder.decode(output_chunk).rstrip("\n")
            )
    final_output = output_decoder.decode(b"", final=True)
    if final_output:
        logger.info("player_output %s", final_output)


def supervise_player(run_directory, player_arguments):
    logger = create_diagnostic_logger(
        "ambient_canvas.player", run_directory / "player.log"
    )
    started_at = time.monotonic()
    report = {
        "status": "running",
        "started_at": diagnostic_timestamp(),
        "supervisor_pid": os.getpid(),
        "arguments": player_arguments,
        "platform": platform.platform(),
    }
    write_player_report(run_directory, report)
    try:
        player_process = subprocess.Popen(
            player_arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except OSError as error:
        report.update(
            status="launch_failed", error=str(error), finished_at=diagnostic_timestamp()
        )
        write_player_report(run_directory, report)
        logger.exception("player_launch_failed arguments=%s", player_arguments)
        return 1

    report["player_pid"] = player_process.pid
    write_player_report(run_directory, report)
    logger.info(
        "player_started pid=%s arguments=%s", player_process.pid, player_arguments
    )
    captured_output = PlayerOutput()
    output_reader = threading.Thread(
        target=capture_player_output,
        args=(player_process.stdout, logger, captured_output),
        daemon=True,
    )
    output_reader.start()
    exit_code = player_process.wait()
    output_reader.join(timeout=OUTPUT_DRAIN_TIMEOUT_SECONDS)
    if output_reader.is_alive():
        logger.warning("player_output_still_open_after_exit")
    signal_name = signal.Signals(-exit_code).name if exit_code < 0 else None
    report.update(
        status="exited" if exit_code == 0 else "failed",
        finished_at=diagnostic_timestamp(),
        duration_seconds=round(time.monotonic() - started_at, 3),
        exit_code=exit_code,
        signal=signal_name,
        output_tail=captured_output.tail.decode("utf-8", errors="replace"),
    )
    write_player_report(run_directory, report)
    logger.info(
        "player_exited pid=%s exit_code=%s signal=%s",
        player_process.pid,
        exit_code,
        signal_name,
    )
    return 0


def main():
    run_directory = Path(sys.argv[1])
    return supervise_player(run_directory, sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
