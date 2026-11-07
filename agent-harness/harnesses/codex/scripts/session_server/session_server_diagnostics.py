from contextlib import suppress
import os
from pathlib import Path
import selectors
import threading
import time


MAXIMUM_SESSION_DIAGNOSTIC_BYTES = 2 * 1024 * 1024
MAXIMUM_STARTUP_DIAGNOSTIC_BYTES = 4096
DIAGNOSTIC_FILE_BYTES = MAXIMUM_SESSION_DIAGNOSTIC_BYTES // 2
DIAGNOSTIC_READ_BYTES = 64 * 1024


class SessionServerDiagnostics:
    def __init__(self, directory: Path):
        self.current_path = directory / "server-stderr.log"
        self.previous_path = directory / "server-stderr.previous.log"
        self._output = self.current_path.open("wb", buffering=0)
        self._output_bytes = 0
        self._closed = False
        self._capture_thread = None
        self._descriptors = []
        self._storage_available = True
        self._shutdown_deadline = None
        try:
            self._stderr_reader, self.stderr_descriptor = os.pipe()
            self._descriptors.extend((self._stderr_reader, self.stderr_descriptor))
            self._shutdown_reader, self._shutdown_writer = os.pipe()
            self._descriptors.extend((self._shutdown_reader, self._shutdown_writer))
        except OSError:
            self.close()
            raise

    def __enter__(self):
        capture_thread = threading.Thread(target=self._capture, daemon=True)
        try:
            capture_thread.start()
        except RuntimeError:
            self.close()
            raise
        self._capture_thread = capture_thread
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.close()

    def close_stderr_descriptor(self) -> None:
        if self.stderr_descriptor in self._descriptors:
            os.close(self.stderr_descriptor)
            self._descriptors.remove(self.stderr_descriptor)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._capture_thread is not None:
            self.close_stderr_descriptor()
            os.write(self._shutdown_writer, b"\0")
            self._capture_thread.join()
        for descriptor in self._descriptors:
            os.close(descriptor)
        self._descriptors.clear()
        with suppress(OSError):
            self._output.close()

    def startup_failure_details(self) -> str:
        diagnostic_bytes = bytearray()
        for path in (self.previous_path, self.current_path):
            if not path.exists():
                continue
            with path.open("rb") as source:
                source.seek(
                    max(0, path.stat().st_size - MAXIMUM_STARTUP_DIAGNOSTIC_BYTES)
                )
                diagnostic_bytes.extend(source.read(MAXIMUM_STARTUP_DIAGNOSTIC_BYTES))
        text = diagnostic_bytes[-MAXIMUM_STARTUP_DIAGNOSTIC_BYTES:].decode(
            "utf-8", errors="ignore"
        )
        return "".join(
            character
            for character in text
            if character.isprintable() or character in "\n\t"
        ).strip()

    def _append(self, output: bytes) -> None:
        offset = 0
        while offset < len(output):
            if self._output_bytes == DIAGNOSTIC_FILE_BYTES:
                self._output.close()
                self.current_path.replace(self.previous_path)
                self._output = self.current_path.open("wb", buffering=0)
                self._output_bytes = 0
            byte_count = min(
                DIAGNOSTIC_FILE_BYTES - self._output_bytes, len(output) - offset
            )
            written_bytes = self._output.write(output[offset : offset + byte_count])
            if not written_bytes:
                raise OSError("Codex diagnostic output could not be written")
            self._output_bytes += written_bytes
            offset += written_bytes

    def _capture(self) -> None:
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self._stderr_reader, selectors.EVENT_READ)
                selector.register(self._shutdown_reader, selectors.EVENT_READ)
                self._pump_until_shutdown(selector)
        except OSError:
            return

    def _pump_until_shutdown(self, selector: selectors.BaseSelector) -> None:
        while self._shutdown_window_is_open():
            events = selector.select(self._selection_timeout_seconds())
            if not events:
                return
            for key, _ in events:
                if not self._handle_ready_descriptor(selector, key.fd):
                    return

    def _shutdown_window_is_open(self) -> bool:
        return (
            self._shutdown_deadline is None
            or time.monotonic() < self._shutdown_deadline
        )

    def _selection_timeout_seconds(self):
        return None if self._shutdown_deadline is None else 0

    def _handle_ready_descriptor(
        self, selector: selectors.BaseSelector, descriptor: int
    ) -> bool:
        if descriptor == self._shutdown_reader:
            os.read(self._shutdown_reader, 1)
            selector.unregister(self._shutdown_reader)
            self._shutdown_deadline = time.monotonic() + 1.0
            return True
        output = os.read(self._stderr_reader, DIAGNOSTIC_READ_BYTES)
        if not output:
            return False
        if self._storage_available:
            self._store_output(output)
        return True

    def _store_output(self, output: bytes) -> None:
        try:
            self._append(output)
        except OSError:
            self._storage_available = False
