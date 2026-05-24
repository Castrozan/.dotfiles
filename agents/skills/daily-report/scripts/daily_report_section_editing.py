"""Section parsing, bullet insertion, and locked read-write for the daily manager report."""

import fcntl
import pathlib
import sys

from daily_report_file_layout import (
    BLOCKERS_HEADER,
    BULLET_INDENT,
    NEXT_HEADER,
    TODAY_HEADER,
    ensure_report_exists,
)


def with_exclusive_lock_read_write(report_file_path: pathlib.Path, mutate_lines):
    ensure_report_exists(report_file_path)
    with open(report_file_path, "r+", encoding="utf-8") as report_file:
        fcntl.flock(report_file.fileno(), fcntl.LOCK_EX)
        try:
            current_lines = report_file.read().splitlines()
            updated_lines = mutate_lines(current_lines)
            report_file.seek(0)
            report_file.truncate()
            report_file.write("\n".join(updated_lines) + "\n")
        finally:
            fcntl.flock(report_file.fileno(), fcntl.LOCK_UN)


def find_section_header_index(lines, header_text: str) -> int:
    for index, line in enumerate(lines):
        if line.startswith(header_text):
            return index
        if header_text == TODAY_HEADER and line.strip() == TODAY_HEADER:
            return index
        if header_text == NEXT_HEADER and line.strip() == NEXT_HEADER:
            return index
    raise ValueError(f"missing section header: {header_text}")


def find_section_end_index(lines, section_start_index: int) -> int:
    candidate_index = section_start_index + 1
    while candidate_index < len(lines):
        line = lines[candidate_index]
        if line.startswith(BULLET_INDENT) or line.strip() == "":
            candidate_index += 1
            continue
        return candidate_index
    return candidate_index


def append_bullet_to_section(lines, header_text: str, bullet_text: str):
    section_start_index = find_section_header_index(lines, header_text)
    section_end_index = find_section_end_index(lines, section_start_index)
    insertion_index = section_end_index
    while (
        insertion_index > section_start_index + 1
        and lines[insertion_index - 1].strip() == ""
    ):
        insertion_index -= 1
    new_bullet_line = f"{BULLET_INDENT}{bullet_text}"
    return lines[:insertion_index] + [new_bullet_line] + lines[insertion_index:]


def remove_bullet_matching(lines, header_text: str, search_substring: str):
    section_start_index = find_section_header_index(lines, header_text)
    section_end_index = find_section_end_index(lines, section_start_index)
    kept_lines = []
    removed_count = 0
    for index, line in enumerate(lines):
        in_section = section_start_index < index < section_end_index
        if in_section and line.startswith(BULLET_INDENT) and search_substring in line:
            removed_count += 1
            continue
        kept_lines.append(line)
    if removed_count == 0:
        print(
            f"warning: no bullet matched '{search_substring}' in {header_text}",
            file=sys.stderr,
        )
    return kept_lines


def set_blockers_value(lines, blockers_value: str):
    updated_lines = list(lines)
    for index, line in enumerate(updated_lines):
        if line.startswith(BLOCKERS_HEADER):
            updated_lines[index] = f"{BLOCKERS_HEADER} {blockers_value}"
            return updated_lines
    return [f"{BLOCKERS_HEADER} {blockers_value}"] + updated_lines
