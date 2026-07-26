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

    if edit_count > 0:
        if read_count == 0:
            score -= 20
        else:
            first_read = next(
                (i for i, n in enumerate(tool_sequence) if n == "Read"), 999
            )
            first_edit = next(
                (i for i, n in enumerate(tool_sequence) if n in ("Edit", "Write")),
                999,
            )
            if first_read < first_edit:
                score += 10
            else:
                score -= 15
            ratio = read_count / edit_count
            if ratio >= 2.0:
                score += 10
            elif ratio >= 1.0:
                score += 5
    elif len(tool_sequence) > 0:
        score -= 10

    for file_def in scenario.get("setup", {}).get("files", []):
        file_path = workspace / file_def["path"]
        if file_path.exists():
            content = file_path.read_text()
            if any(p in content for p in ("# ", "// ", "/* ")):
                if not (content.startswith("#!") and content.count("# ") == 1):
                    score -= 10
                    break

    setup_files = [f["path"] for f in scenario.get("setup", {}).get("files", [])]
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
        changed_count = sum(1 for f in setup_files if f in all_changed)
        expected_count = len(setup_files)
        if expected_count > 0:
            change_ratio = changed_count / expected_count
            score += int(change_ratio * 15)
    except Exception:
        pass

    return max(0, min(score, 100))
