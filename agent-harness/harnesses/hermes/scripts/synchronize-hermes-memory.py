#!/usr/bin/env python3
import argparse
import os
import tempfile
from pathlib import Path


ENTRY_DELIMITER = "\n§\n"


def memory_entries(memory_text: str) -> list[str]:
    if not memory_text.strip():
        return []
    return [entry.strip() for entry in memory_text.split(ENTRY_DELIMITER)]


def memory_entry_key(memory_entry: str) -> str | None:
    entry_key, separator, _ = memory_entry.partition(":")
    return entry_key.strip() if separator else None


def retired_entry_prefixes(retired_entry_prefixes_path: Path | None) -> tuple[str, ...]:
    if retired_entry_prefixes_path is None:
        return ()
    return tuple(
        line.strip()
        for line in retired_entry_prefixes_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def validate_managed_entries(managed_entries: list[str]) -> set[str]:
    managed_entry_keys = [memory_entry_key(entry) for entry in managed_entries]
    if any(entry_key is None for entry_key in managed_entry_keys):
        raise ValueError(
            "every managed memory entry requires a stable key before its first colon"
        )
    if len(managed_entry_keys) != len(set(managed_entry_keys)):
        raise ValueError("managed memory entry keys must be unique")
    return {entry_key for entry_key in managed_entry_keys if entry_key is not None}


def synchronized_memory_text(
    current_memory_text: str,
    managed_memory_text: str,
    retired_prefixes: tuple[str, ...],
) -> str:
    managed_entries = memory_entries(managed_memory_text)
    managed_entry_keys = validate_managed_entries(managed_entries)
    preserved_entries = [
        entry
        for entry in memory_entries(current_memory_text)
        if memory_entry_key(entry) not in managed_entry_keys
        and not entry.startswith(retired_prefixes)
    ]
    return ENTRY_DELIMITER.join((*preserved_entries, *managed_entries))


def replace_memory_file(memory_path: Path, memory_text: str) -> None:
    if memory_path.exists() and memory_path.read_text(encoding="utf-8") == memory_text:
        return
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=memory_path.parent,
            prefix=f".{memory_path.name}.",
            delete=False,
        ) as temporary_file:
            temporary_file.write(memory_text)
            temporary_path = Path(temporary_file.name)
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, memory_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def parse_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--target", type=Path, required=True)
    argument_parser.add_argument("--source", type=Path, required=True)
    argument_parser.add_argument("--retired-entry-prefixes", type=Path)
    return argument_parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    current_memory_text = (
        arguments.target.read_text(encoding="utf-8")
        if arguments.target.exists()
        else ""
    )
    managed_memory_text = arguments.source.read_text(encoding="utf-8")
    merged_memory_text = synchronized_memory_text(
        current_memory_text,
        managed_memory_text,
        retired_entry_prefixes(arguments.retired_entry_prefixes),
    )
    replace_memory_file(arguments.target, merged_memory_text)


if __name__ == "__main__":
    main()
