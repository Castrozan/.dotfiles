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
RULESYNC_EXECUTABLE = "@rulesyncExecutable@"


def verify_generated_hooks(generated, target):
    if not generated.is_file() or not generated.stat().st_size:
        raise ValueError(f"Rulesync did not generate {target} hooks")
    content = generated.read_text()
    if target == "opencode":
        _verify_opencode_hook(content)
        return
    hooks = json.loads(content)["hooks"]
    _verify_json_hooks(hooks, target)


def _verify_opencode_hook(content):
    if 'id: "rulesync.hooks"' not in content:
        raise ValueError("Rulesync did not emit the OpenCode V2 plugin")


def _verify_json_hooks(hooks, target):
    required = {"SessionStart", "PreToolUse", "PostToolUse", "Stop"}
    required |= {
        "claudecode": {"SubagentStop", "PermissionRequest"},
        "codexcli": {"UserPromptSubmit"},
    }.get(target, set())
    if set(hooks) != required or any(not hooks[event] for event in required):
        raise ValueError(f"Rulesync changed the required {target} hook events")


def _sandboxed_child(root, name):
    child = (root / name).resolve()
    if not child.is_relative_to(root.resolve()):
        raise ValueError(f"{name} escapes the sandboxed root {root}")
    return child


def _serialized_target_configuration(source, runner, surface):
    configuration = json.loads(source.read_text())
    serialized = json.dumps(configuration)
    replacements = {"@runner@": runner, "@surface@": surface}
    for placeholder, value in replacements.items():
        serialized = serialized.replace(placeholder, json.dumps(value)[1:-1])
    return serialized


def _target_build_environment(home):
    return os.environ | {
        "HOME": str(home),
        "HOME_DIR": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_STATE_HOME": str(home / ".local/state"),
        "NO_COLOR": "1",
    }


def _materialize_target_hooks(target, surface, artifact, source, runner, state, output):
    home = _sandboxed_child(state, target)
    home.mkdir()
    inputs = _sandboxed_child(home, "source")
    inputs.mkdir()
    inputs_file = _sandboxed_child(inputs, "hooks.json")
    inputs_file.write_text(_serialized_target_configuration(source, runner, surface))
    destination = _sandboxed_child(output, target)
    subprocess.run(
        [
            RULESYNC_EXECUTABLE,
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
        env=_target_build_environment(home),
        check=True,
        timeout=30,
    )
    verify_generated_hooks(destination / artifact, target)


def build_hooks(source, output, runner, opencode_runner):
    output.mkdir()
    try:
        with tempfile.TemporaryDirectory(prefix="rulesync-hooks-") as temporary:
            state = Path(temporary)
            for target, (surface, artifact) in TARGETS.items():
                selected_runner = opencode_runner if target == "opencode" else runner
                _materialize_target_hooks(
                    target, surface, artifact, source, selected_runner, state, output
                )
    except BaseException:
        shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--opencode-runner", required=True)
    arguments = parser.parse_args()
    build_hooks(
        arguments.source,
        arguments.output,
        arguments.runner,
        arguments.opencode_runner,
    )


if __name__ == "__main__":
    main()
