import argparse
import re
import sys
from datetime import date
from pathlib import Path

from clawde_workspace_paths import agents_directory

MEMORY_DIRECTORY_NAME = "memory"
INDEX_FILE_NAME = "MEMORY.md"
TOPIC_TYPES = ("user", "feedback", "project", "reference")
TOPIC_KEY_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9._-]{0,63}\Z")
AUTHOR_PATTERN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9 ._-]{0,63}\Z")
INDEX_SUMMARY_LENGTH = 140
FACT_LINE_PREFIX = "- "
INDEX_HEADER = (
    "# Memory index\n"
    "\n"
    "One line per topic file, rebuilt from this directory on every write.\n"
    "Nothing here loads automatically, so read the topic file you need before\n"
    "you rely on a callback. Append through clawde-agent-memory-append.\n"
    "\n"
)


class MemoryWriteRefused(Exception):
    pass


def parse_command_line_arguments(argv):
    parser = argparse.ArgumentParser(
        prog="clawde-agent-memory-append",
        description="Append one durable fact to this agent's own memory directory.",
    )
    parser.add_argument("--type", dest="topic_type", required=True, choices=TOPIC_TYPES)
    parser.add_argument("--key", dest="topic_key", required=True)
    parser.add_argument("--fact", dest="fact", required=True)
    parser.add_argument("--author", dest="author", required=True)
    return parser.parse_args(argv)


def resolve_memory_directory(working_directory):
    workspace = Path(working_directory).resolve()
    if workspace.parent != agents_directory():
        raise MemoryWriteRefused(
            f"refusing to write memory from {workspace}: "
            f"only an agent workspace directly under {agents_directory()} owns a memory directory"
        )
    return workspace / MEMORY_DIRECTORY_NAME


def validate_topic_key(topic_key):
    if not TOPIC_KEY_PATTERN.fullmatch(topic_key):
        raise MemoryWriteRefused(
            f"refusing topic key {topic_key!r}: expected lowercase letters, digits, dot, dash or underscore"
        )
    return topic_key


def validate_author(author):
    if not AUTHOR_PATTERN.fullmatch(author):
        raise MemoryWriteRefused(
            f"refusing author {author!r}: expected a discord id or a plain handle"
        )
    return author


def flatten_fact(fact):
    flattened = " ".join(fact.split())
    if not flattened:
        raise MemoryWriteRefused("refusing an empty fact")
    return flattened


def topic_file_name(topic_type, topic_key):
    return f"{topic_type}-{topic_key}.md"


def format_fact_line(author, fact, written_on):
    return f"{FACT_LINE_PREFIX}{written_on.isoformat()} ({author}): {fact}"


def append_fact_line(topic_file, topic_type, topic_key, fact_line):
    if topic_file.exists():
        existing = topic_file.read_text(encoding="utf-8").rstrip("\n")
        topic_file.write_text(f"{existing}\n{fact_line}\n", encoding="utf-8")
        return
    heading = f"# {topic_type}-{topic_key}"
    topic_file.write_text(f"{heading}\n\n{fact_line}\n", encoding="utf-8")


def newest_fact_of(topic_file):
    fact_lines = [
        line.strip()
        for line in topic_file.read_text(encoding="utf-8").splitlines()
        if line.startswith(FACT_LINE_PREFIX)
    ]
    if not fact_lines:
        return ""
    newest = fact_lines[-1][len(FACT_LINE_PREFIX) :]
    if len(newest) <= INDEX_SUMMARY_LENGTH:
        return newest
    return f"{newest[:INDEX_SUMMARY_LENGTH]}..."


def index_entry_of(topic_file):
    topic_type, _, topic_key = topic_file.stem.partition("-")
    return f"{FACT_LINE_PREFIX}[{topic_type}/{topic_key}]({topic_file.name}): {newest_fact_of(topic_file)}"


def rebuild_index(memory_directory):
    topic_files = sorted(
        path for path in memory_directory.glob("*.md") if path.name != INDEX_FILE_NAME
    )
    entries = "".join(f"{index_entry_of(path)}\n" for path in topic_files)
    (memory_directory / INDEX_FILE_NAME).write_text(
        f"{INDEX_HEADER}{entries}", encoding="utf-8"
    )


def append_agent_memory_fact(
    working_directory, topic_type, topic_key, fact, author, written_on
):
    memory_directory = resolve_memory_directory(working_directory)
    memory_directory.mkdir(parents=True, exist_ok=True)
    topic_file = memory_directory / topic_file_name(
        topic_type, validate_topic_key(topic_key)
    )
    append_fact_line(
        topic_file,
        topic_type,
        topic_key,
        format_fact_line(validate_author(author), flatten_fact(fact), written_on),
    )
    rebuild_index(memory_directory)
    return topic_file


def main(argv=None):
    arguments = parse_command_line_arguments(sys.argv[1:] if argv is None else argv)
    try:
        topic_file = append_agent_memory_fact(
            Path.cwd(),
            arguments.topic_type,
            arguments.topic_key,
            arguments.fact,
            arguments.author,
            date.today(),
        )
    except MemoryWriteRefused as refusal:
        print(str(refusal), file=sys.stderr)
        return 1
    print(f"appended to {topic_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
