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

    _remove_previous_managed_marketplace(marketplace, bundle, marketplace_name, run)
    run("marketplace", "add", "--json", "--", str(bundle.resolve()))
    run("add", "--json", "--", f"dotfiles@{marketplace_name}")


def _remove_previous_managed_marketplace(marketplace, bundle, marketplace_name, run):
    if not marketplace or marketplace.get("source") == str(bundle.resolve()):
        return
    previous = Path(marketplace["source"]) / ".agents/plugins/marketplace.json"
    catalog = json.loads(previous.read_text())
    if not _is_dotfiles_marketplace(marketplace, catalog):
        raise ValueError("The managed marketplace name belongs to another source")
    run("marketplace", "remove", "--json", "--", marketplace_name)


def _is_dotfiles_marketplace(marketplace, catalog):
    return marketplace.get("source_type") == "local" and [
        plugin["name"] for plugin in catalog["plugins"]
    ] == ["dotfiles"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("home", type=Path)
    arguments = parser.parse_args()
    register_plugin(arguments.bundle, arguments.home)
