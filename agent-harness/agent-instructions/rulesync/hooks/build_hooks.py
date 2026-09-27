import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


TARGETS = {
    "claudecode": ("claude", ".claude/settings.json"),
    "codexcli": ("codex", ".codex/hooks.json"),
    "opencode": ("opencode", ".opencode/plugins/rulesync-hooks.js"),
}

ALLOWED_EVENTS = {
    "claudecode": {
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
        "Stop",
        "SubagentStop",
        "PermissionRequest",
    },
    "codexcli": {"SessionStart", "PreToolUse", "PostToolUse", "Stop"},
}


def confined_path(candidate, label):
    path = Path(candidate)
    text = os.fspath(path)
    if not os.path.isabs(text) or ".." in path.parts:
        raise ValueError(f"{label} must be an absolute path without traversal segments")
    return path


def verify_generated_hooks(target, artifact):
    if target == "opencode":
        if 'id: "rulesync.hooks"' not in artifact.read_text():
            raise ValueError("Rulesync did not emit the OpenCode V2 plugin")
        return
    hook_events = json.loads(artifact.read_text())["hooks"]
    expected_events = ALLOWED_EVENTS[target]
    if set(hook_events) != expected_events or any(
        not hook_events[event] for event in expected_events
    ):
        raise ValueError(f"Rulesync changed the required {target} hook events")


def build_hooks(source, output, rulesync, runner, opencode_runner):
    source_path = confined_path(source, "source")
    output_path = confined_path(output, "output")
    rulesync_path = confined_path(rulesync, "rulesync")
    output_path.mkdir()
    try:
        with tempfile.TemporaryDirectory(prefix="rulesync-hooks-") as temporary:
            state = Path(temporary)
            for target, (surface, artifact_path) in TARGETS.items():
                home = state / target
                home.mkdir()
                inputs = home / "source"
                inputs.mkdir()
                selected_runner = opencode_runner if target == "opencode" else runner
                configuration = json.loads(source_path.read_text())
                serialized = json.dumps(configuration)
                replacements = {"@runner@": selected_runner, "@surface@": surface}
                for placeholder, value in replacements.items():
                    serialized = serialized.replace(
                        placeholder, json.dumps(value)[1:-1]
                    )
                (inputs / "hooks.json").write_text(serialized)
                environment = os.environ | {
                    "HOME": str(home),
                    "HOME_DIR": str(home),
                    "XDG_CONFIG_HOME": str(home / ".config"),
                    "XDG_CACHE_HOME": str(home / ".cache"),
                    "XDG_STATE_HOME": str(home / ".local/state"),
                    "NO_COLOR": "1",
                }
                destination = output_path / target
                subprocess.run(
                    [
                        str(rulesync_path),
                        "generate",
                        "--input-roots",
                        str(inputs),
                        "--output-roots",
                        str(destination),
                        "--targets",
                        target,
                        "--features",
                        "hooks",
                    ],
                    cwd=home,
                    env=environment,
                    check=True,
                    timeout=30,
                )
                generated = destination / artifact_path
                if not generated.is_file() or not generated.stat().st_size:
                    raise ValueError(f"Rulesync did not generate {target} hooks")
                verify_generated_hooks(target, generated)
    except BaseException:
        shutil.rmtree(output_path)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rulesync", required=True, type=Path)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--opencode-runner", required=True)
    arguments = parser.parse_args()
    build_hooks(
        arguments.source,
        arguments.output,
        arguments.rulesync,
        arguments.runner,
        arguments.opencode_runner,
    )


if __name__ == "__main__":
    main()
