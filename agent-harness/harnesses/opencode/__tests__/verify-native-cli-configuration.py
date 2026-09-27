import json
import subprocess
import sys
import tempfile
from pathlib import Path

from native_opencode_profile import prepare_profile
from native_opencode_server import native_server


def verify_cli_configuration(executable, settings, agents):
    declared = json.loads(settings.read_text())
    with tempfile.TemporaryDirectory(prefix="opencode-native-cli-") as temporary:
        root = Path(temporary)
        environment, workspace = prepare_profile(root, agents)
        configuration = Path(environment["OPENCODE_CONFIG_DIR"])
        configuration.chmod(0o755)
        plugin = configuration / "native-cli-acceptance"
        plugin.mkdir()
        (plugin / "tui.js").write_text(
            'export default { id: "native.cli.acceptance", setup() {} };\n'
        )
        configured = declared | {"plugins": ["./native-cli-acceptance"]}
        cli_settings = configuration / "cli.json"
        with native_server(executable, environment, workspace) as server:
            info = server.request("/api/info")
            registration = root / "state/opencode/service.json"
            registration.parent.mkdir(parents=True, exist_ok=True)
            registration.write_text(
                json.dumps(
                    {
                        "url": server.base_url,
                        "pid": info["pid"],
                        "version": info["version"],
                        "password": server.password,
                    }
                )
            )
            registration.chmod(0o600)
            for valid in (True, False):
                document = configured if valid else configured | {"theme": "kanagawa"}
                cli_settings.write_text(json.dumps(document))
                result = subprocess.run(
                    [str(executable), "plugin", "list"],
                    cwd=workspace,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                assert result.returncode == 0, result.stderr
                assert (str(plugin) in result.stdout) is valid, result.stdout
                assert json.loads(cli_settings.read_text()) == document


if __name__ == "__main__":
    verify_cli_configuration(sys.argv[1], *map(Path, sys.argv[2:]))
