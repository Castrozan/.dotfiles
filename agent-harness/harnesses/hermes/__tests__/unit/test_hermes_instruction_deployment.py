import os
import subprocess
from pathlib import Path


HERMES_DIRECTORY = Path(__file__).resolve().parents[2]


def test_launch_preserves_plugin_assets_and_uses_the_pinned_runtime(tmp_path):
    home = tmp_path / "custom-hermes-home"
    binary = tmp_path / "runtime/bin/hermes"
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/usr/bin/env bash\nexit 0\n")
    binary.chmod(0o755)
    source = tmp_path / "source.md"
    source.write_text("### Evidence\n\nRead.\n")
    environment = {
        **os.environ,
        "HERMES_HOME": str(home),
        "HERMES_AGENT_BINARY": str(binary),
        "HERMES_AGENT_RUNTIME_PATH": os.environ["PATH"],
        "HERMES_AGENT_CONFIG_TEMPLATE": str(source),
        "HERMES_AGENT_SOUL": str(source),
    }
    environment.pop("HERMES_AGENT_LAUNCH_SEEDED", None)
    installed = (
        home / "plugins/dotfiles/skills/wellput/references/interactive-communication.md"
    )
    installed.parent.mkdir(parents=True)
    installed.write_text("Preserved package asset.")
    for content in ("### Evidence\n\nRead.\n", "### Evidence\n\nVerify.\n"):
        source.write_text(content)
        subprocess.run(
            ["bash", str(HERMES_DIRECTORY / "scripts/hermes-launch")],
            env=environment,
            check=True,
        )
        assert installed.read_text() == "Preserved package asset."
        assert not (home / "skills/wellput").exists()
        assert (home / "SOUL.md").read_text() == content
