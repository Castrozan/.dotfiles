import argparse
import json
import os
import subprocess
import tomllib
from pathlib import Path

CODEX_EXECUTABLE = "@codex@"
MARKETPLACE_CATALOG_PATHS = (
    Path(".agents/plugins/marketplace.json"),
    Path(".claude-plugin/marketplace.json"),
)


def register_plugin(marketplace_root: Path, home: Path) -> None:
    catalog = read_marketplace_catalog(marketplace_root)
    marketplace_name = catalog["name"]
    plugin_names = catalog_plugin_names(catalog)
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

    _remove_previous_managed_marketplace(
        marketplace, marketplace_root, marketplace_name, plugin_names, run
    )
    run("marketplace", "add", "--json", "--", str(marketplace_root.resolve()))
    for plugin_name in plugin_names:
        run("add", "--json", "--", f"{plugin_name}@{marketplace_name}")


def read_marketplace_catalog(marketplace_root: Path) -> dict:
    for catalog_path in MARKETPLACE_CATALOG_PATHS:
        candidate = marketplace_root / catalog_path
        if candidate.is_file():
            return json.loads(candidate.read_text())
    raise ValueError(f"No marketplace catalog in {marketplace_root}")


def catalog_plugin_names(catalog: dict) -> list[str]:
    return [plugin["name"] for plugin in catalog["plugins"]]


def _remove_previous_managed_marketplace(
    marketplace, marketplace_root, marketplace_name, plugin_names, run
):
    if not marketplace or marketplace.get("source") == str(marketplace_root.resolve()):
        return
    previous_catalog = read_marketplace_catalog(Path(marketplace["source"]))
    if not _is_same_managed_marketplace(marketplace, previous_catalog, plugin_names):
        raise ValueError("The managed marketplace name belongs to another source")
    run("marketplace", "remove", "--json", "--", marketplace_name)


def _is_same_managed_marketplace(marketplace, previous_catalog, plugin_names):
    return (
        marketplace.get("source_type") == "local"
        and catalog_plugin_names(previous_catalog) == plugin_names
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("marketplace_root", type=Path)
    parser.add_argument("home", type=Path)
    arguments = parser.parse_args()
    register_plugin(arguments.marketplace_root, arguments.home)
