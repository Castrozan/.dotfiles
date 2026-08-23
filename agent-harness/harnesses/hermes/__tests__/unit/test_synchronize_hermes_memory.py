import os
import subprocess
import sys
from pathlib import Path


ENTRY_DELIMITER = "\n§\n"
MEMORY_SYNCHRONIZER_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "synchronize-hermes-memory.py"
)


def run_memory_synchronizer(target, source, retired_entry_prefixes=None):
    command = [
        sys.executable,
        str(MEMORY_SYNCHRONIZER_PATH),
        "--target",
        str(target),
        "--source",
        str(source),
    ]
    if retired_entry_prefixes is not None:
        command.extend(["--retired-entry-prefixes", str(retired_entry_prefixes)])
    subprocess.run(command, check=True)


def test_synchronizer_replaces_owned_entries_and_preserves_unknown_memory(tmp_path):
    target = tmp_path / "USER.md"
    source = tmp_path / "managed-USER.md"
    retired_entry_prefixes = tmp_path / "retired-user-entry-prefixes"
    target.write_text(
        ENTRY_DELIMITER.join(
            (
                "Identity: stale managed value",
                "Correction stance: retired managed value",
                "Custom discovery: preserve this user-created value",
            )
        ),
        encoding="utf-8",
    )
    source.write_text(
        ENTRY_DELIMITER.join(
            (
                "Identity: current managed value",
                "Writing preference: current managed preference",
            )
        ),
        encoding="utf-8",
    )
    retired_entry_prefixes.write_text("Correction stance:\n", encoding="utf-8")

    run_memory_synchronizer(target, source, retired_entry_prefixes)

    assert target.read_text(encoding="utf-8").split(ENTRY_DELIMITER) == [
        "Custom discovery: preserve this user-created value",
        "Identity: current managed value",
        "Writing preference: current managed preference",
    ]


def test_synchronizer_does_not_rewrite_an_identical_target(tmp_path):
    target = tmp_path / "MEMORY.md"
    source = tmp_path / "managed-MEMORY.md"
    source.write_text("Environment: managed value", encoding="utf-8")
    run_memory_synchronizer(target, source)
    fixed_timestamp_nanoseconds = 1_700_000_000_000_000_000
    os.utime(
        target,
        ns=(fixed_timestamp_nanoseconds, fixed_timestamp_nanoseconds),
    )

    run_memory_synchronizer(target, source)

    assert target.stat().st_mtime_ns == fixed_timestamp_nanoseconds
