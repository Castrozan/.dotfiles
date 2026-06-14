import os
import selectors
import signal
import subprocess
import threading
import time

from .base import AgentBackend, BackendObservation

READ_CHUNK_SIZE_BYTES = 4096


class SubprocessAgentBackend(AgentBackend):
    def __init__(self, command_argv: list[str]) -> None:
        self._command_argv = command_argv
        self._process: subprocess.Popen | None = None
        self._output_buffer_lock = threading.Lock()
        self._unread_output_buffer = ""
        self._last_activity_at_epoch_seconds = time.time()
        self._reader_thread: threading.Thread | None = None
        self._reader_should_stop = threading.Event()

    def start(self) -> None:
        self._process = subprocess.Popen(
            self._command_argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            text=False,
        )
        self._last_activity_at_epoch_seconds = time.time()
        self._reader_thread = threading.Thread(
            target=self._continuously_drain_subprocess_output_into_buffer,
            daemon=True,
        )
        self._reader_thread.start()

    def send_input_text(self, text: str) -> None:
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("subprocess backend not started")
        self._process.stdin.write(text.encode("utf-8"))
        self._process.stdin.flush()
        self._last_activity_at_epoch_seconds = time.time()

    def observe(self) -> BackendObservation:
        with self._output_buffer_lock:
            output_since_last_call = self._unread_output_buffer
            self._unread_output_buffer = ""
        process_is_alive = self._is_process_alive()
        return BackendObservation(
            raw_output_since_last_call=output_since_last_call,
            is_alive=process_is_alive,
            last_activity_at_epoch_seconds=self._last_activity_at_epoch_seconds,
            exit_code=self._exit_code_when_process_has_exited(process_is_alive),
        )

    def _exit_code_when_process_has_exited(self, process_is_alive: bool) -> int | None:
        if process_is_alive or self._process is None:
            return None
        return self._process.returncode

    def cancel_gracefully(self) -> None:
        if self._process is None or self._process.poll() is not None:
            return
        self._process.send_signal(signal.SIGINT)

    def stop(self) -> None:
        self._reader_should_stop.set()
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        if self._reader_thread is not None:
            self._reader_thread.join(timeout=2)

    def _is_process_alive(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def _continuously_drain_subprocess_output_into_buffer(self) -> None:
        if self._process is None or self._process.stdout is None:
            return
        selector = selectors.DefaultSelector()
        selector.register(self._process.stdout, selectors.EVENT_READ)
        while not self._reader_should_stop.is_set():
            if not self._is_process_alive():
                self._drain_remaining_output_after_exit()
                return
            ready_events = selector.select(timeout=0.2)
            if not ready_events:
                continue
            try:
                raw_chunk_bytes = os.read(
                    self._process.stdout.fileno(), READ_CHUNK_SIZE_BYTES
                )
            except OSError:
                return
            if not raw_chunk_bytes:
                self._drain_remaining_output_after_exit()
                return
            decoded_chunk = raw_chunk_bytes.decode("utf-8", errors="replace")
            with self._output_buffer_lock:
                self._unread_output_buffer += decoded_chunk
            self._last_activity_at_epoch_seconds = time.time()

    def _drain_remaining_output_after_exit(self) -> None:
        if self._process is None or self._process.stdout is None:
            return
        try:
            remaining_bytes = self._process.stdout.read()
        except (OSError, ValueError):
            return
        if not remaining_bytes:
            return
        decoded_remaining = remaining_bytes.decode("utf-8", errors="replace")
        with self._output_buffer_lock:
            self._unread_output_buffer += decoded_remaining
        self._last_activity_at_epoch_seconds = time.time()
