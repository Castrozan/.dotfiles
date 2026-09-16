import time
from pathlib import Path


def stored_head(path: Path) -> str:
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        first_line = f.readline().decode(errors="replace").strip()
    if first_line.startswith("# HEAD: "):
        return first_line[8:]
    return ""


def is_stale(path: Path, head: str) -> bool:
    if not path.exists():
        return True
    if stored_head(path) != head:
        return True
    age = time.time() - path.stat().st_mtime
    return age > 3600


def file_size_human(path: Path) -> str:
    size = path.stat().st_size
    for unit in ("B", "K", "M", "G"):
        if size < 1024:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}T"


def line_count(path: Path) -> int:
    with open(path, "rb") as f:
        return sum(1 for _ in f)
