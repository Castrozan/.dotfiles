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


def build_hooks(source, output, rulesync, runner, opencode_runner):
    output.mkdir()
    try:
        with tempfile.TemporaryDirectory(prefix="rulesync-hooks-") as temporary:
            state = Path(temporary)
            for target, (surface, artifact) in TARGETS.items():
                home = state / target
                home.mkdir()
                inputs = home / "source"
                inputs.mkdir()
                selected_runner = opencode_runner if target == "opencode" else runner
                configuration = json.loads(source.read_text())
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
                destination = output / target
                subprocess.run(
                    [
                        str(rulesync),
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
                generated = destination / artifact
                if not generated.is_file() or not generated.stat().st_size:
                    raise ValueError(f"Rulesync did not generate {target} hooks")
                if target != "opencode":
                    hooks = json.loads(generated.read_text())["hooks"]
                    required = {"SessionStart", "PreToolUse", "PostToolUse", "Stop"}
                    if target == "claudecode":
                        required |= {"SubagentStop", "PermissionRequest"}
                    if set(hooks) != required or any(
                        not hooks[event] for event in required
                    ):
                        raise ValueError(
                            f"Rulesync changed the required {target} hook events"
                        )
                elif 'id: "rulesync.hooks"' not in generated.read_text():
                    raise ValueError("Rulesync did not emit the OpenCode V2 plugin")
    except BaseException:
        shutil.rmtree(output)
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
