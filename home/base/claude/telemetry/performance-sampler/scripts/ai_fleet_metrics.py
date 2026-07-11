from command_runner import run_command_capturing_stdout
from process_table_parsers import command_first_token_basename, sum_process_cpu_percent

FLEET_BUCKET_COMMAND_SUBSTRINGS = [
    ("claude_cli", "/bin/claude "),
    ("chrome_devtools_mcp", "chrome-devtools-mcp"),
    ("figma_mcp", "figma-developer-mcp"),
    ("browser_use_mcp", "browser-use --mcp"),
    ("a2a_mcp", "a2a-mcp-server"),
    ("codex_cli", "/bin/codex "),
]

FLEET_BUCKET_EXECUTABLE_BASENAMES = {"opencode": "opencode"}

CLAUDE_COMMAND_MARKER = "/bin/claude "
AGENT_SESSION_FLAGS = ("--agent-name", "--name")
CHROME_DEVTOOLS_MCP_COMMAND_MARKER = "chrome-devtools-mcp"


def classify_fleet_bucket(command_text: str):
    for bucket_name, command_substring in FLEET_BUCKET_COMMAND_SUBSTRINGS:
        if command_substring in command_text:
            return bucket_name
    return FLEET_BUCKET_EXECUTABLE_BASENAMES.get(
        command_first_token_basename(command_text)
    )


def parse_fleet_process_table(ps_output: str) -> dict:
    process_count_by_bucket = {}
    rss_kilobytes_by_bucket = {}
    for line in ps_output.splitlines():
        line_parts = line.strip().split(None, 2)
        if len(line_parts) < 3:
            continue
        try:
            process_rss_kilobytes = int(line_parts[1])
        except ValueError:
            continue
        bucket_name = classify_fleet_bucket(line_parts[2])
        if bucket_name is None:
            continue
        process_count_by_bucket[bucket_name] = (
            process_count_by_bucket.get(bucket_name, 0) + 1
        )
        rss_kilobytes_by_bucket[bucket_name] = (
            rss_kilobytes_by_bucket.get(bucket_name, 0) + process_rss_kilobytes
        )
    return {"counts": process_count_by_bucket, "rss_kilobytes": rss_kilobytes_by_bucket}


def parse_claude_fanout(ps_output: str) -> dict:
    claude_session_pids = set()
    parent_pids = []
    for line in ps_output.splitlines():
        line_parts = line.strip().split(None, 2)
        if len(line_parts) < 3:
            continue
        process_pid, parent_pid, command_text = line_parts
        if CLAUDE_COMMAND_MARKER in command_text:
            claude_session_pids.add(process_pid)
        parent_pids.append(parent_pid)
    children_count_by_session = {}
    for parent_pid in parent_pids:
        if parent_pid in claude_session_pids:
            children_count_by_session[parent_pid] = (
                children_count_by_session.get(parent_pid, 0) + 1
            )
    if not children_count_by_session:
        return {"sessions": 0, "mean": 0.0, "max": 0}
    children_counts = list(children_count_by_session.values())
    return {
        "sessions": len(children_counts),
        "mean": round(sum(children_counts) / len(children_counts), 1),
        "max": max(children_counts),
    }


def parse_claude_session_kinds(ps_output: str) -> dict:
    agent_session_count = 0
    interactive_session_count = 0
    for line in ps_output.splitlines():
        command_text = line.strip()
        if CLAUDE_COMMAND_MARKER not in command_text:
            continue
        command_tokens = command_text.split()
        if any(flag in command_tokens for flag in AGENT_SESSION_FLAGS):
            agent_session_count += 1
        else:
            interactive_session_count += 1
    return {"agents": agent_session_count, "interactive": interactive_session_count}


def collect_fleet_process_buckets() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "pid=,rss=,command="])
    parsed_fleet = parse_fleet_process_table(ps_output)
    fleet_records = []
    total_process_count = 0
    total_rss_kilobytes = 0
    for bucket_name, process_count in parsed_fleet["counts"].items():
        rss_kilobytes = parsed_fleet["rss_kilobytes"][bucket_name]
        total_process_count += process_count
        total_rss_kilobytes += rss_kilobytes
        fleet_records.append(
            {
                "metric": "fleet_process_count",
                "value": process_count,
                "labels": {"bucket": bucket_name},
            }
        )
        fleet_records.append(
            {
                "metric": "fleet_rss_megabytes",
                "value": round(rss_kilobytes / 1024, 1),
                "labels": {"bucket": bucket_name},
            }
        )
    fleet_records.append(
        {
            "metric": "fleet_process_count",
            "value": total_process_count,
            "labels": {"bucket": "total"},
        }
    )
    fleet_records.append(
        {
            "metric": "fleet_rss_megabytes",
            "value": round(total_rss_kilobytes / 1024, 1),
            "labels": {"bucket": "total"},
        }
    )
    return fleet_records


def collect_claude_fanout() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "pid=,ppid=,command="])
    fanout = parse_claude_fanout(ps_output)
    return [
        {"metric": "mcp_fanout_sessions", "value": fanout["sessions"], "labels": {}},
        {"metric": "mcp_fanout_children_mean", "value": fanout["mean"], "labels": {}},
        {"metric": "mcp_fanout_children_max", "value": fanout["max"], "labels": {}},
    ]


def collect_chrome_devtools_mcp_cpu() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "pcpu=,command="])
    aggregate_cpu_percent = sum_process_cpu_percent(
        ps_output,
        lambda command_text: CHROME_DEVTOOLS_MCP_COMMAND_MARKER in command_text,
    )
    return [
        {
            "metric": "chrome_devtools_mcp_cpu_percent",
            "value": aggregate_cpu_percent,
            "labels": {},
        }
    ]


def collect_claude_session_kinds() -> list:
    ps_output = run_command_capturing_stdout(["ps", "-axo", "command="])
    session_kinds = parse_claude_session_kinds(ps_output)
    return [
        {
            "metric": "claude_sessions",
            "value": session_kinds["agents"],
            "labels": {"kind": "agent"},
        },
        {
            "metric": "claude_sessions",
            "value": session_kinds["interactive"],
            "labels": {"kind": "interactive"},
        },
    ]


metric_collectors = [
    ("ai_fleet.process_buckets", collect_fleet_process_buckets),
    ("ai_fleet.claude_fanout", collect_claude_fanout),
    ("ai_fleet.chrome_devtools_mcp_cpu", collect_chrome_devtools_mcp_cpu),
    ("ai_fleet.claude_session_kinds", collect_claude_session_kinds),
]
