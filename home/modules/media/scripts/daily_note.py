import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

MAX_DAYS_BACK = 5
TODO_SECTION_MARKER = "## TODO"
LAST_NOTES_HEADER = "## Last Daily Notes with unchecked tasks"

UNCHECKED_TODO_PATTERN = re.compile(r"^\s*-\s*\[\s*\]\s+")
CHECKED_TODO_PATTERN = re.compile(r"^\s*-\s*\[\s*[xX]\s*\]\s+")
TODO_CONTENT_PATTERN = re.compile(r"^\s*-\s*\[\s*[xX ]?\s*\]\s*")


def get_daily_note_file_name(date_string: str) -> str:
    return f"{date_string}-daily-note.md"


def validate_obsidian_home_is_set() -> str:
    obsidian_home = os.environ.get("OBSIDIAN_HOME", "")
    if not obsidian_home:
        print("Error: OBSIDIAN_HOME is not defined.", file=sys.stderr)
        raise SystemExit(1)
    return obsidian_home


def get_past_dates(days_back: int) -> list[str]:
    today = datetime.now()
    return [
        (today - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(1, days_back + 1)
    ]


def is_unchecked_todo(line: str) -> bool:
    return bool(UNCHECKED_TODO_PATTERN.match(line))


def is_checked_todo(line: str) -> bool:
    return bool(CHECKED_TODO_PATTERN.match(line))


def normalize_todo_content(line: str) -> str:
    return TODO_CONTENT_PATTERN.sub("", line).strip()


def extract_unchecked_todos_from_todo_section(file_path: Path) -> list[str]:
    unchecked_todos = []
    in_todo_section = False

    for line in file_path.read_text().splitlines():
        if line.startswith("## TODO"):
            in_todo_section = True
            continue
        if in_todo_section and line.startswith("## "):
            break
        if in_todo_section and is_unchecked_todo(line):
            unchecked_todos.append(line)

    return unchecked_todos


def is_todo_checked_in_later_notes(
    normalized_content: str,
    current_index: int,
    past_dates: list[str],
    obsidian_home: str,
) -> bool:
    for i in range(current_index):
        date = past_dates[i]
        filepath = Path(obsidian_home) / "daily-note" / get_daily_note_file_name(date)
        if not filepath.is_file():
            continue

        in_todo_section = False
        for line in filepath.read_text().splitlines():
            if line.startswith("## TODO"):
                in_todo_section = True
                continue
            if in_todo_section and line.startswith("## "):
                break
            if in_todo_section and is_checked_todo(line):
                if normalize_todo_content(line) == normalized_content:
                    return True

    return False


def build_unchecked_todos_from_past_notes(
    past_dates: list[str], obsidian_home: str
) -> str:
    sections = []

    for idx, date in enumerate(past_dates):
        filename = get_daily_note_file_name(date)
        filepath = Path(obsidian_home) / "daily-note" / filename

        if not filepath.is_file():
            continue

        todos = extract_unchecked_todos_from_todo_section(filepath)
        filtered_todos = [
            todo
            for todo in todos
            if not is_todo_checked_in_later_notes(
                normalize_todo_content(todo), idx, past_dates, obsidian_home
            )
        ]

        if filtered_todos:
            section_lines = [f"\n### {filename}\n"]
            section_lines.extend(filtered_todos)
            sections.append("\n".join(section_lines))

    return "\n".join(sections)


def create_new_daily_note(
    date_string: str, filename: str, fullpath: Path, obsidian_home: str
) -> None:
    past_dates = get_past_dates(MAX_DAYS_BACK)
    unchecked_todos_text = build_unchecked_todos_from_past_notes(
        past_dates, obsidian_home
    )

    content_lines = [
        f"# {date_string} Daily Note",
        f"### {filename}",
        "",
        TODO_SECTION_MARKER,
        "",
        "",
        "",
        LAST_NOTES_HEADER,
    ]

    if unchecked_todos_text:
        content_lines.append(unchecked_todos_text)

    fullpath.parent.mkdir(parents=True, exist_ok=True)
    fullpath.write_text("\n".join(content_lines) + "\n")


def open_daily_note_in_editor(fullpath: Path, obsidian_home: str) -> None:
    editor = os.environ.get("EDITOR", "vim")

    if editor in ("code", "cursor"):
        subprocess.Popen(
            [editor, obsidian_home, "-g", str(fullpath)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.Popen(
            [editor, str(fullpath)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main() -> None:
    obsidian_home = validate_obsidian_home_is_set()

    today = datetime.now().strftime("%Y-%m-%d")
    filename = get_daily_note_file_name(today)
    fullpath = Path(obsidian_home) / "daily-note" / filename

    if not fullpath.is_file():
        create_new_daily_note(today, filename, fullpath, obsidian_home)

    open_daily_note_in_editor(fullpath, obsidian_home)


if __name__ == "__main__":
    main()
