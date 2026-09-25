import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def build(source, output, targets, success=True, data_root=None):
    process = subprocess.run(
        [
            "agent-plugin-build",
            str(source),
            "--output",
            str(output),
            *[argument for target in targets for argument in ("--target", target)],
            *(["--opencode-data-root", str(data_root)] if data_root else []),
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
        data_root = root / "state"
        targets = ("claude", "codex", "opencode")
        missing_state = build(source, output, targets, success=False)
        assert "--opencode-data-root" in missing_state.stderr
        assert not output.exists()
        build(source, output, targets, data_root=data_root)
        first = snapshot(output)
        build(source, output, targets, success=False, data_root=data_root)
        assert snapshot(output) == first
        shutil.rmtree(output)
        build(source, output, targets, data_root=data_root)
        assert snapshot(output) == first
        shutil.rmtree(output)

        destination = root / "destination"
        destination.mkdir()
        alias = root / "alias"
        alias.symlink_to(destination, target_is_directory=True)
        aliased_output = alias / "bundle"
        mcp_path = source / "mcp.json"
        original_mcp = mcp_path.read_bytes()
        mcp = json.loads(original_mcp)
        mcp["mcpServers"]["distribution-probe"]["cwd"] = "${PLUGIN_DATA}"
        mcp_path.write_text(json.dumps(mcp))
        build(source, aliased_output, targets, data_root=data_root)
        configuration = json.loads(
            (aliased_output / ".opencode/opencode.jsonc").read_text()
        )
        server = configuration["mcp"]["plugin.distribution-probe.distribution-probe"]
        assert server["environment"]["PLUGIN_DATA"] == str(
            data_root / "distribution-probe"
        )
        assert server["cwd"] == server["environment"]["PLUGIN_DATA"]
        mcp_path.write_bytes(original_mcp)
        shutil.rmtree(aliased_output)

        manifest_path = source / "plugin.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["extensions"] = {"com.example.client": {"hooks": "./hooks.json"}}
        manifest_path.write_text(json.dumps(manifest))
        extension = source / "com.example.client"
        extension.mkdir()
        (extension / "hooks.json").write_text('{"hooks":{}}')
        (source / "unknown-artifact.bin").write_bytes(bytes(range(256)))
        original = snapshot(source)
        for selected in ((), ("pi", "hermes"), targets):
            build(source, output, selected, data_root=data_root)
            delivered = snapshot(output / "plugin")
            assert all(delivered[path] == content for path, content in original.items())
            for target in {"pi", "hermes"} & set(selected):
                assert (output / f".{target}/plugins/distribution-probe").resolve() == (
                    output / "plugin"
                ).resolve()
            assert not (output / ".agents/skills/distribution-probe").exists()
            shutil.rmtree(output)

        native = source / ".claude-plugin"
        native.mkdir()
        authored = '{"name":"distribution-probe","hooks":"./com.openai/hooks.json"}'
        (native / "plugin.json").write_text(authored)
        build(source, output, targets, data_root=data_root)
        assert (output / "plugin/.claude-plugin/plugin.json").read_text() == authored
        shutil.rmtree(output)

        (source / "mcp.json").write_text('{"mcpServers":{"broken":{"type":"invalid"}}}')
        build(source, output, targets, data_root=data_root)
        assert (output / "plugin/mcp.json").read_bytes() == (
            source / "mcp.json"
        ).read_bytes()
        assert (output / "dotagents-doctor.log").is_file()
    print(
        "Complete packages, loader directories, reproducibility and failure cleanup verified"
    )


if __name__ == "__main__":
    verify_contract(Path(sys.argv[1]))
