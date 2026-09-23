import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def build(source, output, targets, success=True):
    process = subprocess.run(
        [
            "agent-plugin-build",
            str(source),
            "--output",
            str(output),
            *[argument for target in targets for argument in ("--target", target)],
        ],
        capture_output=True,
        text=True,
        timeout=70,
        check=False,
    )
    assert (process.returncode == 0) == success, process.stdout + process.stderr
    return process


def snapshot(directory):
    return {
        str(path.relative_to(directory)): (
            str(path.readlink())
            if path.is_symlink()
            else hashlib.sha256(path.read_bytes()).hexdigest()
        )
        for path in directory.rglob("*")
        if path.is_file() or path.is_symlink()
    }


def verify_contract(fixture):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary).resolve()
        source = Path(shutil.copytree(fixture, root / "source"))
        subprocess.run(["chmod", "-R", "u+w", str(source)], check=True, timeout=5)
        output = root / "bundle"
        targets = ("claude", "codex", "opencode")
        build(source, output, targets)
        first = snapshot(output)
        build(source, output, targets, success=False)
        assert snapshot(output) == first
        shutil.rmtree(output)
        build(source, output, targets)
        assert snapshot(output) == first
        shutil.rmtree(output)

        build(source, output, ("pi",), success=False)
        assert not output.exists()
        (source / "mcp.json").unlink()
        build(source, output, ("pi",))
        assert (output / ".agents/skills/distribution-probe/SKILL.md").is_file()
        shutil.rmtree(output)

        manifest_path = source / "plugin.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["extensions"] = {"com.example.client": {"hooks": "./hooks.json"}}
        manifest_path.write_text(json.dumps(manifest))
        build(source, output, targets, success=False)
        assert not output.exists()
        manifest.pop("extensions")
        manifest_path.write_text(json.dumps(manifest))
        (source / "mcp.json").write_text('{"mcpServers":{"broken":{"type":"invalid"}}}')
        build(source, output, targets, success=False)
        assert not output.exists()
    print("Reproducibility, collisions, Pi scope and failed-build cleanup verified")


if __name__ == "__main__":
    verify_contract(Path(sys.argv[1]))
