import collections
import dataclasses
import json
import time
from pathlib import Path

from turn_cost import turn_from_usage

PROJECTS_ROOT = Path.home() / ".claude" / "projects"


@dataclasses.dataclass
class Session:
    project: str
    model: str = ""
    turns: list = dataclasses.field(default_factory=list)
    compactions: int = 0
    tool_text_bytes: collections.Counter = dataclasses.field(
        default_factory=collections.Counter
    )
    tool_image_bytes: collections.Counter = dataclasses.field(
        default_factory=collections.Counter
    )
    tool_calls: collections.Counter = dataclasses.field(
        default_factory=collections.Counter
    )
    reads_total: int = 0
    reads_repeated: int = 0

    @property
    def weighted_cost(self):
        return sum(turn.weighted_cost for turn in self.turns)


@dataclasses.dataclass
class PendingToolCalls:
    names: dict = dataclasses.field(default_factory=dict)
    read_paths: dict = dataclasses.field(default_factory=dict)
    reads_seen: collections.Counter = dataclasses.field(
        default_factory=collections.Counter
    )
    recorded_results: set = dataclasses.field(default_factory=set)


def measure_content_block(block):
    if not isinstance(block, dict):
        return 0, 0
    if block.get("type") == "image":
        return 0, len(json.dumps(block))
    return len(block.get("text", "")), 0


def measure_tool_result(content):
    if isinstance(content, str):
        return len(content), 0
    if not isinstance(content, list):
        return 0, 0
    text_bytes = image_bytes = 0
    for block in content:
        block_text_bytes, block_image_bytes = measure_content_block(block)
        text_bytes += block_text_bytes
        image_bytes += block_image_bytes
    return text_bytes, image_bytes


def remember_tool_use(block, pending):
    pending.names[block["id"]] = block["name"]
    if block["name"] == "Read":
        pending.read_paths[block["id"]] = block["input"].get("file_path")


def record_tool_result(session, block, pending):
    tool_use_id = block.get("tool_use_id")
    if tool_use_id in pending.recorded_results:
        return
    pending.recorded_results.add(tool_use_id)
    tool = pending.names.get(tool_use_id, "unknown")
    text_bytes, image_bytes = measure_tool_result(block.get("content"))
    session.tool_text_bytes[tool] += text_bytes
    session.tool_image_bytes[tool] += image_bytes
    session.tool_calls[tool] += 1
    if tool != "Read":
        return
    file_path = pending.read_paths.get(tool_use_id)
    session.reads_total += 1
    session.reads_repeated += pending.reads_seen[file_path] > 0
    pending.reads_seen[file_path] += 1


def read_lines(path):
    with path.open(errors="replace") as handle:
        yield from handle


def read_json_records(path, session):
    for line in read_lines(path):
        session.compactions += '"compact_boundary"' in line
        try:
            yield json.loads(line)
        except ValueError:
            continue


def message_content_blocks(message):
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


def record_message_usage(session, record, message, usage_by_message_id):
    if not message.get("usage"):
        return
    message_id = message.get("id") or record.get("uuid")
    usage_by_message_id[message_id] = message["usage"]
    session.model = message.get("model") or session.model


def remember_tool_uses(blocks, pending):
    for block in blocks:
        if block.get("type") == "tool_use":
            remember_tool_use(block, pending)


def record_tool_results(session, blocks, pending):
    for block in blocks:
        if block.get("type") == "tool_result":
            record_tool_result(session, block, pending)


def apply_record(session, pending, usage_by_message_id, record):
    message = record.get("message")
    if not isinstance(message, dict):
        return
    blocks = message_content_blocks(message)
    if record.get("type") == "assistant":
        record_message_usage(session, record, message, usage_by_message_id)
        remember_tool_uses(blocks, pending)
    elif record.get("type") == "user":
        record_tool_results(session, blocks, pending)


def parse_session(path):
    session = Session(project=path.parent.name)
    pending = PendingToolCalls()
    usage_by_message_id = {}
    for record in read_json_records(path, session):
        apply_record(session, pending, usage_by_message_id, record)
    session.turns = [turn_from_usage(usage) for usage in usage_by_message_id.values()]
    return session


def load_sessions(days):
    cutoff = time.time() - days * 86400
    paths = [
        path
        for path in PROJECTS_ROOT.glob("*/*.jsonl")
        if path.stat().st_mtime >= cutoff
    ]
    sessions = (parse_session(path) for path in paths)
    return [session for session in sessions if session.turns]
