import json
import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path


def write_hook_dispatcher_launcher(directory):
    launcher = directory / "hook-dispatcher-launcher.py"
    launcher.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\nfrom pathlib import Path\n"
        "payload = json.load(sys.stdin)\n"
        'record = Path(os.environ["OPENCODE_HOOK_RECORD"])\n'
        "records = json.loads(record.read_text()) if record.exists() else []\n"
        'records.append({"dispatcher": sys.argv[1], "payload": payload})\n'
        "record.write_text(json.dumps(records))\n"
        'responses = json.loads(os.environ["OPENCODE_HOOK_RESPONSES"])\n'
        'response = responses.get(sys.argv[1], "")\n'
        "if response: print(response if isinstance(response, str) else json.dumps(response))\n"
    )
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR)
    return launcher


def generate_hook_plugin(directory, rulesync):
    launcher = write_hook_dispatcher_launcher(directory)
    transport = Path(__file__).resolve().parents[1] / "policy-transport/dispatch.py"
    source = directory / "source"
    source.mkdir()
    dispatchers = {
        "sessionStart": "session-start-dispatcher.py",
        "preToolUse": "pre-tool-use-dispatcher.py",
        "postToolUse": "post-tool-use-dispatcher.py",
        "stop": "stop-dispatcher.py",
    }
    configuration = {
        "version": 1,
        "opencode": {"apiVersion": 2},
        "hooks": {
            event: [
                {
                    "command": shlex.join(
                        [sys.executable, str(transport), str(launcher), script]
                    ),
                    "timeout": 5,
                }
            ]
            for event, script in dispatchers.items()
        },
    }
    (source / "hooks.json").write_text(json.dumps(configuration))
    home = directory / "home"
    home.mkdir()
    output = directory / "generated"
    subprocess.run(
        [
            str(rulesync),
            "generate",
            "--input-roots",
            str(source),
            "--output-roots",
            str(output),
            "--targets",
            "opencode",
            "--features",
            "hooks",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=home,
        env=os.environ
        | {
            "HOME": str(home),
            "HOME_DIR": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
        },
    )
    return output / ".opencode/plugins/rulesync-hooks.js"
