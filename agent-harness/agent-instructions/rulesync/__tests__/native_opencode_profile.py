import json
import os
import signal
import subprocess
import time


def run_native(executable, environment, workspace, name, *arguments):
    with subprocess.Popen(
        [str(executable), "--pure", "debug", "agent", name, *arguments],
        cwd=workspace,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    ) as process:
        try:
            output, errors = process.communicate(timeout=30)
            return subprocess.CompletedProcess(
                process.args, process.returncode, output, errors
            )
        finally:
            for termination in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(process.pid, termination)
                except ProcessLookupError:
                    break
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    process.poll()
                    try:
                        os.killpg(process.pid, 0)
                    except ProcessLookupError:
                        break
                    time.sleep(0.05)
                else:
                    continue
                break
            process.wait(timeout=2)
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                pass
            else:
                raise RuntimeError("Native OpenCode left its process group running")


def prepare_profile(root, sources, ambient_names=()):
    workspace = root / "workspace"
    configuration = root / "configuration"
    global_configuration = root / "config/opencode"
    for directory in (
        root / "home",
        workspace,
        configuration / "agents",
        global_configuration,
    ):
        directory.mkdir(parents=True)
    for source in sources.glob("*.md"):
        (configuration / "agents" / source.name).symlink_to(source.resolve())
    settings = {
        "$schema": "https://opencode.ai/config.json",
        "model": "acceptance/fixture",
        "enabled_providers": ["acceptance"],
        "provider": {
            "acceptance": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "Acceptance",
                "options": {"baseURL": "http://127.0.0.1:1/v1"},
                "models": {
                    "fixture": {
                        "name": "Acceptance",
                        "limit": {"context": 8192, "output": 1024},
                    }
                },
            }
        },
        "permission": {"*": "allow"},
        "mcp": {},
        "plugin": [],
        "lsp": False,
        "formatter": False,
    }
    (global_configuration / "opencode.json").write_text(json.dumps(settings))
    directories = [configuration, global_configuration]
    if ambient_names:
        ambient_configuration = root / "home/.opencode"
        (ambient_configuration / "agents").mkdir(parents=True)
        for name in ambient_names:
            (ambient_configuration / "agents" / f"{name}.md").write_text(
                f"---\nname: {name}\nmode: subagent\ndescription: Ambient control\n"
                "permission:\n  '*': allow\n---\nAMBIENT_ONLY_AGENT\n"
            )
        directories.append(ambient_configuration)
    for directory in directories:
        (directory / ".gitignore").write_text("node_modules\n")
        directory.chmod(0o555)
        assert not os.access(directory, os.W_OK), (
            "Native acceptance must run as non-root"
        )
    environment = {
        "PATH": os.environ["PATH"],
        "HOME": str(root / "home"),
        "XDG_CONFIG_HOME": str(root / "config"),
        "XDG_CACHE_HOME": str(root / "cache"),
        "XDG_DATA_HOME": str(root / "data"),
        "XDG_STATE_HOME": str(root / "state"),
        "OPENCODE_CONFIG_DIR": str(configuration),
        "OPENCODE_DISABLE_PROJECT_CONFIG": "true",
        "OPENCODE_DISABLE_CLAUDE_CODE": "true",
        "OPENCODE_DISABLE_MODELS_FETCH": "true",
        "OPENCODE_DISABLE_AUTOUPDATE": "true",
        "OPENCODE_EXPERIMENTAL_DISABLE_FILEWATCHER": "true",
        "NO_COLOR": "1",
        "NPM_CONFIG_OFFLINE": "true",
    }
    return environment, workspace
