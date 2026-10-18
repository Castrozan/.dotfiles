import json
import subprocess
import sys
from pathlib import Path


def export_plugin_fixture(fixture_directory):
    owner = Path(__file__).resolve().parents[1]
    instructions = owner.parent
    harness = instructions.parent
    sources = {
        "skill": instructions / "skills/writing/humanize",
        "rules": harness / "hooks/runtime/common/human_facing_reply",
        "guard": harness / "hooks/runtime/stop/end_of_turn_format_guard_handler.py",
        "renderer": harness
        / "quality/evaluations/instructions/reply_format_instructions.py",
        "tests": harness / "hooks/runtime/__tests__/unit/replies",
        "support": harness
        / "hooks/runtime/__tests__/support/human_facing_reply_test_support.py",
        "assets": owner / "assets",
        "portableTests": owner / "__tests__/integration",
        "verifier": owner / "__tests__/portable/verify_plugin.py",
    }
    formatter = fixture_directory / "formatter"
    formatter.mkdir()
    (formatter / "instructions").symlink_to(
        harness / "quality/evaluations/instructions", target_is_directory=True
    )
    sources["instructionFormatter"] = formatter
    manifest = fixture_directory / "sources.json"
    manifest.write_text(json.dumps({name: str(path) for name, path in sources.items()}))
    plugin = fixture_directory / "plugin"
    subprocess.run(
        [sys.executable, owner / "scripts/export_plugin.py", manifest, plugin],
        check=True,
        timeout=10,
    )
    return plugin
