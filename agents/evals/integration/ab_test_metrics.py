from ab_test_models import InstructionFollowingMetrics, SessionTrace


ABBREVIATION_PATTERNS = [
    "def proc(",
    "def fmt(",
    "def calc(",
    "def chk(",
    "def fn(",
    "def f(",
    "def g(",
    "def h(",
]


def extract_tool_names(
    trace: SessionTrace,
) -> list[str]:
    return [tc.tool_name for tc in trace.tool_calls]


def collect_written_content(
    trace: SessionTrace,
) -> str:
    parts = []
    for tc in trace.tool_calls:
        if tc.tool_name in ("Edit", "Write"):
            new_string = tc.tool_input.get("new_string", "")
            content = tc.tool_input.get("content", "")
            if new_string:
                parts.append(new_string)
            if content:
                parts.append(content)
    return "\n".join(parts)


def measure_instruction_following(
    trace: SessionTrace,
) -> InstructionFollowingMetrics:
    metrics = InstructionFollowingMetrics()
    tool_names = extract_tool_names(trace)
    metrics.total_tool_calls = len(tool_names)

    read_count = tool_names.count("Read")
    edit_count = tool_names.count("Edit") + tool_names.count("Write")
    glob_count = tool_names.count("Glob")
    grep_count = tool_names.count("Grep")

    if edit_count > 0 and read_count > 0:
        first_read = next(
            (i for i, name in enumerate(tool_names) if name == "Read"),
            999,
        )
        first_edit = next(
            (i for i, name in enumerate(tool_names) if name in ("Edit", "Write")),
            999,
        )
        metrics.read_before_edit = first_read < first_edit
        metrics.read_to_edit_ratio = read_count / edit_count
    elif edit_count > 0:
        metrics.read_before_edit = False
        metrics.read_to_edit_ratio = 0.0

    has_bash_find = any(
        tc.tool_name == "Bash" and "find " in tc.tool_input.get("command", "")
        for tc in trace.tool_calls
    )
    metrics.used_glob_not_find = (
        glob_count > 0 or grep_count > 0
    ) and not has_bash_find

    written_content = collect_written_content(trace)
    if written_content:
        has_comments = any(
            pattern in written_content for pattern in ("# ", "// ", "/* ")
        )
        metrics.no_comments_in_written_code = not has_comments

        has_abbreviations = any(
            pattern in written_content for pattern in ABBREVIATION_PATTERNS
        )
        metrics.used_descriptive_names = not has_abbreviations
    else:
        metrics.no_comments_in_written_code = True
        metrics.used_descriptive_names = True

    has_git_add_all = any(
        tc.tool_name == "Bash"
        and (
            "git add -A" in tc.tool_input.get("command", "")
            or "git add ." in tc.tool_input.get("command", "")
        )
        for tc in trace.tool_calls
    )
    has_git_add_specific = any(
        tc.tool_name == "Bash"
        and "git add " in tc.tool_input.get("command", "")
        and "git add -A" not in tc.tool_input.get("command", "")
        and "git add ." not in tc.tool_input.get("command", "")
        for tc in trace.tool_calls
    )
    metrics.used_specific_git_staging = (
        has_git_add_specific and not has_git_add_all
    ) or not has_git_add_all

    score = 0
    if metrics.read_before_edit:
        score += 20
    if metrics.read_to_edit_ratio >= 1.0:
        score += 15
    elif metrics.read_to_edit_ratio >= 0.5:
        score += 8
    if metrics.used_glob_not_find:
        score += 15
    if metrics.no_comments_in_written_code:
        score += 20
    if metrics.used_descriptive_names:
        score += 15
    if metrics.used_specific_git_staging:
        score += 15
    metrics.score = min(score, 100)

    return metrics
