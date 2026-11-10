import os
import stat
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExaminedEntry:
    path: str
    status: os.stat_result | None
    already_absent: bool = False

    @property
    def is_directory(self) -> bool:
        return self.status is not None and stat.S_ISDIR(self.status.st_mode)

    @property
    def is_interprocess_endpoint(self) -> bool:
        return self.status is not None and (
            stat.S_ISSOCK(self.status.st_mode) or stat.S_ISFIFO(self.status.st_mode)
        )
