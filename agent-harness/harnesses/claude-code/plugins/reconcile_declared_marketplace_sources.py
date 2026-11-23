import json
import pathlib
import subprocess
import sys


def read_json_object(path: pathlib.Path) -> dict | None:
    if not path.exists():
        return None
    try:
        content = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    return content if isinstance(content, dict) else None


def declared_sources_in_overlay(overlay: dict) -> dict:
    declared_marketplaces = overlay.get("extraKnownMarketplaces", {})
    if not isinstance(declared_marketplaces, dict):
        return {}
    return {
        marketplace_name: declaration["source"]
        for marketplace_name, declaration in declared_marketplaces.items()
        if isinstance(declaration, dict) and isinstance(declaration.get("source"), dict)
    }


def read_declared_marketplace_sources(overlay_paths: list[pathlib.Path]) -> dict:
    declared_sources: dict = {}
    for overlay_path in overlay_paths:
        declared_sources.update(
            declared_sources_in_overlay(read_json_object(overlay_path) or {})
        )
    return declared_sources


def rewrite_differing_sources(
    marketplace_records: dict, declared_sources: dict
) -> list[str]:
    rewritten_marketplace_names = []
    for marketplace_name, declared_source in declared_sources.items():
        record = marketplace_records.get(marketplace_name)
        if not isinstance(record, dict) or record.get("source") == declared_source:
            continue
        record["source"] = declared_source
        rewritten_marketplace_names.append(marketplace_name)
    return rewritten_marketplace_names


def write_json_atomically(path: pathlib.Path, content: dict) -> None:
    temporary_path = path.with_name(path.name + ".tmp")
    temporary_path.write_text(json.dumps(content, indent=2) + "\n")
    temporary_path.chmod(path.stat().st_mode & 0o777)
    temporary_path.replace(path)


def reconcile_file(
    path: pathlib.Path, declared_sources: dict, records_key: str | None
) -> list[str]:
    content = read_json_object(path)
    if content is None:
        return []
    marketplace_records = content.get(records_key) if records_key else content
    if not isinstance(marketplace_records, dict):
        return []
    rewritten_marketplace_names = rewrite_differing_sources(
        marketplace_records, declared_sources
    )
    if rewritten_marketplace_names:
        write_json_atomically(path, content)
    return rewritten_marketplace_names


def clone_git_directory_of(record: object) -> pathlib.Path | None:
    if not isinstance(record, dict):
        return None
    install_location = record.get("installLocation")
    if not isinstance(install_location, str) or not install_location.startswith("/"):
        return None
    clone_git_directory = pathlib.Path(install_location) / ".git"
    return clone_git_directory if clone_git_directory.is_dir() else None


def declared_git_url(declared_source: dict) -> str | None:
    if declared_source.get("source") != "git":
        return None
    declared_url = declared_source.get("url")
    return declared_url if isinstance(declared_url, str) and declared_url else None


def run_git(
    clone_git_directory: pathlib.Path, arguments: list[str]
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", f"--git-dir={clone_git_directory}", *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def point_clone_origin_at(
    clone_git_directory: pathlib.Path | None, declared_url: str | None
) -> bool:
    if clone_git_directory is None or declared_url is None:
        return False
    origin = run_git(clone_git_directory, ["config", "--get", "remote.origin.url"])
    if origin.returncode != 0 or origin.stdout.strip() == declared_url:
        return False
    run_git(
        clone_git_directory, ["remote", "set-url", "origin", declared_url]
    ).check_returncode()
    return True


def point_clone_origins_at_declared_urls(
    known_marketplaces_path: pathlib.Path, declared_sources: dict
) -> list[str]:
    marketplace_records = read_json_object(known_marketplaces_path) or {}
    return [
        marketplace_name
        for marketplace_name, declared_source in declared_sources.items()
        if point_clone_origin_at(
            clone_git_directory_of(marketplace_records.get(marketplace_name)),
            declared_git_url(declared_source),
        )
    ]


def main() -> int:
    known_marketplaces_path = pathlib.Path(sys.argv[1])
    user_settings_path = pathlib.Path(sys.argv[2])
    overlay_paths = [pathlib.Path(argument) for argument in sys.argv[3:]]
    declared_sources = read_declared_marketplace_sources(overlay_paths)
    for path, records_key in (
        (known_marketplaces_path, None),
        (user_settings_path, "extraKnownMarketplaces"),
    ):
        for marketplace_name in reconcile_file(path, declared_sources, records_key):
            print(
                f"marketplace {marketplace_name}: source moved to the declared one in {path}"
            )
    for marketplace_name in point_clone_origins_at_declared_urls(
        known_marketplaces_path, declared_sources
    ):
        print(f"marketplace {marketplace_name}: clone origin moved to the declared url")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
