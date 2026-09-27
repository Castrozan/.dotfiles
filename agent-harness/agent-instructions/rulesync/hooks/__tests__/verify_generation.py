import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def build(builder, source, output, rulesync, directory):
    return subprocess.run(
        [
            sys.executable,
            str(builder),
            str(source),
            str(output),
            "--rulesync",
            str(rulesync),
            "--runner",
            "fixture-runner",
            "--opencode-runner",
            "fixture-opencode-runner",
        ],
        capture_output=True,
        text=True,
        timeout=100,
        cwd=directory,
        env=os.environ | {"HOME": str(directory), "HOME_DIR": str(directory)},
    )


def main():
    builder, canonical, rulesync = (
        Path(argument).resolve() for argument in sys.argv[1:]
    )
    with tempfile.TemporaryDirectory(prefix="rulesync-hook-contract-") as temporary:
        directory = Path(temporary)
        marker = directory / "unrelated"
        marker.write_text("preserve")
        output = directory / "valid"
        result = build(builder, canonical, output, rulesync, directory)
        assert result.returncode == 0, result.stderr
        for target, artifact, surface in (
            ("claudecode", ".claude/settings.json", "claude"),
            ("codexcli", ".codex/hooks.json", "codex"),
            ("opencode", ".opencode/plugins/rulesync-hooks.js", "opencode"),
        ):
            text = (output / target / artifact).read_text()
            assert f"--surface={surface}" in text, target
            assert "@runner@" not in text and "@surface@" not in text, target
            assert "PROHIBITED_WORDS_ALLOWED=" in text, target
            if target == "opencode":
                assert "fixture-opencode-runner" in text
                assert 'id: "rulesync.hooks"' in text
            else:
                assert "fixture-runner" in text
                assert "fixture-opencode-runner" not in text
        configuration = json.loads(canonical.read_text())
        for name, change in (
            ("v1", {"apiVersion": 1}),
            (
                "unsupported",
                {
                    "apiVersion": 2,
                    "hooks": {"permissionRequest": [{"command": "true"}]},
                },
            ),
        ):
            malformed = directory / f"{name}.json"
            malformed.write_text(json.dumps(configuration | {"opencode": change}))
            rejected = directory / name
            result = build(builder, malformed, rejected, rulesync, directory)
            assert result.returncode != 0, name
            assert not rejected.exists(), f"Partial output retained: {name}"
        assert marker.read_text() == "preserve"
        assert not (directory / ".claude").exists()
        assert not (directory / ".codex").exists()
        assert not (directory / ".opencode").exists()
    print(
        "Verified three hook targets, native surfaces, V1 rejection, unsupported-event rejection and isolated cleanup"
    )


if __name__ == "__main__":
    main()
