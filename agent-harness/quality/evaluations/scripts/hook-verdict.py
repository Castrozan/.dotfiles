import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
HOOK_SCRIPT_SEARCH_ROOT = REPOSITORY_ROOT / "agent-harness" / "hooks" / "runtime"
HOOK_TIMEOUT_SECONDS = 30
BLOCKING_EXIT_CODE = 2
MESSAGE_FIELDS = ("systemMessage", "reason")
SPECIFIC_MESSAGE_FIELDS = ("additionalContext", "permissionDecisionReason")


def find_hook_script(hook_filename: str) -> Path:
    matches = sorted(HOOK_SCRIPT_SEARCH_ROOT.rglob(hook_filename))
    if not matches:
        raise SystemExit(f"hook script not found: {hook_filename}")
    return matches[0]


def hook_event_name_for_script(script_path: Path) -> str:
    event_directory = script_path.relative_to(HOOK_SCRIPT_SEARCH_ROOT).parts[0]
    return "".join(word.capitalize() for word in event_directory.split("-"))


def synthesize_hook_event(trigger: dict, hook_event_name: str) -> dict:
    return {
        "hook_event_name": hook_event_name,
        "tool_name": trigger.get("tool", ""),
        "tool_input": {key: value for key, value in trigger.items() if key != "tool"},
        "cwd": str(REPOSITORY_ROOT),
    }


def specific_output(stdout_json) -> dict:
    hook_specific_output = (
        stdout_json.get("hookSpecificOutput") if isinstance(stdout_json, dict) else None
    )
    return hook_specific_output if isinstance(hook_specific_output, dict) else {}


def stops_the_turn(stdout_json: dict) -> bool:
    return (
        stdout_json.get("continue") is False or stdout_json.get("decision") == "block"
    )


def hook_blocked(return_code: int, stdout_json) -> bool:
    if return_code == BLOCKING_EXIT_CODE:
        return True
    if not isinstance(stdout_json, dict):
        return False
    return (
        stops_the_turn(stdout_json)
        or specific_output(stdout_json).get("permissionDecision") == "deny"
    )


def join_present(parts) -> str:
    return "\n".join(part for part in parts if part)


def hook_message(stdout: str, stderr: str, stdout_json) -> str:
    if not isinstance(stdout_json, dict):
        return join_present([stderr, stdout])
    specific = specific_output(stdout_json)
    return join_present(
        [
            stderr,
            *(stdout_json.get(field) for field in MESSAGE_FIELDS),
            *(specific.get(field) for field in SPECIFIC_MESSAGE_FIELDS),
        ]
    )


def parse_json(stdout: str):
    try:
        return json.loads(stdout) if stdout.strip() else None
    except json.JSONDecodeError:
        return None


def main() -> None:
    script_path = find_hook_script(sys.argv[1])
    trigger = json.loads(sys.stdin.read() or "{}")
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        input=json.dumps(
            synthesize_hook_event(trigger, hook_event_name_for_script(script_path))
        ),
        capture_output=True,
        text=True,
        cwd=REPOSITORY_ROOT,
        timeout=HOOK_TIMEOUT_SECONDS,
    )
    stdout_json = parse_json(completed.stdout)
    verdict = (
        "BLOQUEADO" if hook_blocked(completed.returncode, stdout_json) else "LIBERADO"
    )
    print(verdict)
    print(hook_message(completed.stdout, completed.stderr, stdout_json))


main()
