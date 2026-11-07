import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
HOOK_SCRIPT_SEARCH_ROOT = REPOSITORY_ROOT / "agent-harness" / "hooks" / "runtime"


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


def hook_blocked(return_code: int, stdout_json) -> bool:
    if return_code == 2:
        return True
    if not isinstance(stdout_json, dict):
        return False
    if stdout_json.get("continue") is False or stdout_json.get("decision") == "block":
        return True
    hook_specific_output = stdout_json.get("hookSpecificOutput")
    return (
        isinstance(hook_specific_output, dict)
        and hook_specific_output.get("permissionDecision") == "deny"
    )


def hook_message(stdout: str, stderr: str, stdout_json) -> str:
    if not isinstance(stdout_json, dict):
        return "\n".join(part for part in [stderr, stdout] if part)
    hook_specific_output = stdout_json.get("hookSpecificOutput")
    specific = hook_specific_output if isinstance(hook_specific_output, dict) else {}
    parts = [
        stderr,
        stdout_json.get("systemMessage") or "",
        stdout_json.get("reason") or "",
        specific.get("additionalContext") or "",
        specific.get("permissionDecisionReason") or "",
    ]
    return "\n".join(part for part in parts if part)


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
    )
    stdout_json = parse_json(completed.stdout)
    verdict = (
        "BLOQUEADO" if hook_blocked(completed.returncode, stdout_json) else "LIBERADO"
    )
    print(verdict)
    print(hook_message(completed.stdout, completed.stderr, stdout_json))


main()
