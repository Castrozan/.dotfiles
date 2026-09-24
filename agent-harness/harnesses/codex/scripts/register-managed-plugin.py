import argparse
import json
import os
import subprocess
import tomllib
from pathlib import Path

CODEX_EXECUTABLE = "@codex@"


def register_plugin(bundle: Path, home: Path) -> None:
    marketplace_name = "dotagents-local"
    configuration_path = home / "config.toml"
    configuration = (
        tomllib.loads(configuration_path.read_text())
        if configuration_path.exists()
        else {}
    )
    marketplace = configuration.get("marketplaces", {}).get(marketplace_name)
    environment = os.environ | {"CODEX_HOME": str(home)}

    def run(*arguments: str) -> None:
        subprocess.run(
            [CODEX_EXECUTABLE, "plugin", *arguments],
            env=environment,
            check=True,
            timeout=60,
        )

    if marketplace and marketplace.get("source") != str(bundle.resolve()):
        previous = Path(marketplace["source"]) / ".agents/plugins/marketplace.json"
        catalog = json.loads(previous.read_text())
        if marketplace.get("source_type") != "local" or [
            plugin["name"] for plugin in catalog["plugins"]
        ] != ["dotfiles"]:
            raise ValueError("The managed marketplace name belongs to another source")
        run("marketplace", "remove", "--json", "--", marketplace_name)
    run("marketplace", "add", "--json", "--", str(bundle.resolve()))
    run("add", "--json", "--", f"dotfiles@{marketplace_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("home", type=Path)
    arguments = parser.parse_args()
    register_plugin(arguments.bundle, arguments.home)
