from __future__ import annotations

import errno
import os
import time
from collections.abc import Sequence
from pathlib import Path

LOCK_ACQUISITION_TIMEOUT_SECONDS = 10
LOCK_RETRY_INTERVAL_SECONDS = 0.05


def process_is_alive(process_id: int) -> bool:
    try:
        os.kill(process_id, 0)
    except OSError as probe_failure:
        return probe_failure.errno == errno.EPERM
    return True


class HolderRegistry:
    def __init__(self, registry_directory: Path) -> None:
        self.registry_directory = registry_directory
        self.holders_path = registry_directory / "holders"
        self.adopted_marker_path = registry_directory / "started-outside-the-launchers"
        self.lock_path = registry_directory / "lock"

    def __enter__(self) -> HolderRegistry:
        self.registry_directory.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + LOCK_ACQUISITION_TIMEOUT_SECONDS
        while True:
            try:
                os.mkdir(self.lock_path)
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    self.discard_lock()
                    continue
                time.sleep(LOCK_RETRY_INTERVAL_SECONDS)

    def __exit__(self, *_exception_details: object) -> None:
        self.discard_lock()

    def discard_lock(self) -> None:
        try:
            os.rmdir(self.lock_path)
        except OSError:
            pass

    def live_holders(self) -> list[int]:
        try:
            recorded = self.holders_path.read_text().split()
        except OSError:
            return []

        return [
            process_id
            for process_id in (int(entry) for entry in recorded if entry.isdigit())
            if process_is_alive(process_id)
        ]

    def write_holders(self, holders: Sequence[int]) -> None:
        self.holders_path.write_text(
            "".join(f"{process_id}\n" for process_id in holders)
        )

    def mark_adopted(self) -> None:
        self.adopted_marker_path.touch()

    def clear_adoption(self) -> None:
        self.adopted_marker_path.unlink(missing_ok=True)

    def was_adopted(self) -> bool:
        return self.adopted_marker_path.exists()
