import re
import subprocess
from pathlib import Path

TOOL_CALL_PATTERN = re.compile(r"^[●⬤]\s+(\w+)\((.+)\)\s*$")
TOOL_CALL_MULTILINE_PATTERN = re.compile(r"^[●⬤]\s+(\w+)\((.+)$")
COLLAPSED_READ_PATTERN = re.compile(r"^\s*(?:Read|Reading) \d+ file")
COLLAPSED_SEARCH_PATTERN = re.compile(r"^\s*Searched for \d+ pattern")

TOOL_NAME_NORMALIZATION = {
    "Update": "Edit",
    "Bash": "Bash",
    "Read": "Read",
    "Write": "Write",
    "Glob": "Glob",
    "Grep": "Grep",
}


def parse_tool_sequence(raw_output: str) -> list[str]:
    tool_names = []
    for line in raw_output.split("\n"):
        stripped = line.strip()
        match = TOOL_CALL_PATTERN.match(stripped)
        if not match:
            match = TOOL_CALL_MULTILINE_PATTERN.match(stripped)
        if match:
            raw_name = match.group(1)
            tool_names.append(TOOL_NAME_NORMALIZATION.get(raw_name, raw_name))
            continue
        without_bullet = stripped.lstrip("●⬤ ")
        if COLLAPSED_READ_PATTERN.match(without_bullet):
            tool_names.append("Read")
        elif COLLAPSED_SEARCH_PATTERN.match(without_bullet):
            tool_names.append("Grep")
    return tool_names


def calculate_nps_from_tool_sequence_and_workspace(
    tool_sequence: list[str],
    workspace: Path,
    scenario: dict,
) -> int:
    score = 50
    read_count = tool_sequence.count("Read")
    edit_count = tool_sequence.count("Edit") + tool_sequence.count("Write")
    score = _score_tool_sequence(score, tool_sequence, read_count, edit_count)
    score = _score_workspace_comments(score, workspace, scenario)
    score = _score_setup_file_changes(score, workspace, scenario)
    return max(0, min(score, 100))


def _score_tool_sequence(score, tool_sequence, read_count, edit_count):
    if edit_count > 0:
        if read_count == 0:
            return score - 20
        return _score_edits_after_reads(score, tool_sequence, read_count, edit_count)
    if len(tool_sequence) > 0:
        return score - 10
    return score


def _score_edits_after_reads(score, tool_sequence, read_count, edit_count):
    first_read = _first_tool_position(tool_sequence, "Read")
    first_edit = _first_edit_position(tool_sequence)
    if first_read < first_edit:
        score += 10
    else:
        score -= 15
    return _score_read_edit_ratio(score, read_count / edit_count)


def _first_tool_position(tool_sequence, tool_name):
    return next(
        (
            position
            for position, current_tool_name in enumerate(tool_sequence)
            if current_tool_name == tool_name
        ),
        999,
    )


def _first_edit_position(tool_sequence):
    return next(
        (
            position
            for position, tool_name in enumerate(tool_sequence)
            if tool_name in ("Edit", "Write")
        ),
        999,
    )


def _score_read_edit_ratio(score, ratio):
    if ratio >= 2.0:
        return score + 10
    elif ratio >= 1.0:
        return score + 5
    return score


def _score_workspace_comments(score, workspace, scenario):
    for file_def in scenario.get("setup", {}).get("files", []):
        file_path = workspace / file_def["path"]
        if file_path.exists():
            content = file_path.read_text()
            if _has_workspace_comment(content):
                return score - 10
    return score


def _has_workspace_comment(content):
    return any(pattern in content for pattern in ("# ", "// ", "/* ")) and not (
        content.startswith("#!") and content.count("# ") == 1
    )


def _score_setup_file_changes(score, workspace, scenario):
    setup_files = [
        file_definition["path"]
        for file_definition in scenario.get("setup", {}).get("files", [])
    ]
    try:
        initial_sha_result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=5,
        )
        initial_sha = initial_sha_result.stdout.strip().split("\n")[0]
        diff_result = subprocess.run(
            ["git", "diff", "--name-only", initial_sha, "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=5,
        )
        uncommitted_result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=5,
        )
        all_changed = set(
            diff_result.stdout.strip().split("\n")
            + uncommitted_result.stdout.strip().split("\n")
        )
        changed_count = sum(
            1 for setup_file in setup_files if setup_file in all_changed
        )
        expected_count = len(setup_files)
        if expected_count > 0:
            change_ratio = changed_count / expected_count
            score += int(change_ratio * 15)
    except Exception:
        pass
    return score
