import json
import os
import sys
from pathlib import Path

DECLARED_REPOSITORY_LIST_FILE_VARIABLE = "SUWAYOMI_EXTENSION_REPOSITORIES_FILE"
GRAPHQL_URL_VARIABLE = "SUWAYOMI_GRAPHQL_URL"
MIWAYOMI_BASE_URL_VARIABLE = "MIWAYOMI_BASE_URL"
MIWAYOMI_REPOSITORY_LIST_FILE_VARIABLE = "MIWAYOMI_EXTENSION_REPOSITORIES_FILE"
MIWAYOMI_REMOVED_EXTENSION_PACKAGES_VARIABLE = "MIWAYOMI_REMOVED_EXTENSION_PACKAGES"


def graphql_url() -> str:
    declared_url = os.environ.get(GRAPHQL_URL_VARIABLE, "").strip()
    if not declared_url:
        print(f"{GRAPHQL_URL_VARIABLE} is unset", file=sys.stderr)
        raise SystemExit(1)
    return declared_url


def miwayomi_base_url() -> str:
    declared_url = os.environ.get(MIWAYOMI_BASE_URL_VARIABLE, "").strip()
    if not declared_url:
        print(f"{MIWAYOMI_BASE_URL_VARIABLE} is unset", file=sys.stderr)
        raise SystemExit(1)
    return declared_url.rstrip("/")


def removed_miwayomi_extension_packages():
    encoded_packages = os.environ.get(
        MIWAYOMI_REMOVED_EXTENSION_PACKAGES_VARIABLE, "[]"
    )
    try:
        package_names = json.loads(encoded_packages)
    except json.JSONDecodeError as error:
        print(
            f"{MIWAYOMI_REMOVED_EXTENSION_PACKAGES_VARIABLE} is not valid JSON: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error
    if not isinstance(package_names, list) or any(
        not isinstance(package_name, str) or not package_name.strip()
        for package_name in package_names
    ):
        print(
            f"{MIWAYOMI_REMOVED_EXTENSION_PACKAGES_VARIABLE} must be a JSON list of package names",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return tuple(dict.fromkeys(package_name.strip() for package_name in package_names))


def declared_repository_list_file(
    variable_name=DECLARED_REPOSITORY_LIST_FILE_VARIABLE,
) -> Path:
    declared_path = os.environ.get(variable_name, "").strip()
    if not declared_path:
        print(f"{variable_name} is unset", file=sys.stderr)
        raise SystemExit(1)
    return Path(declared_path)


def declared_repository_urls(variable_name=DECLARED_REPOSITORY_LIST_FILE_VARIABLE):
    list_file_path = declared_repository_list_file(variable_name)
    if not list_file_path.is_file():
        return None
    repository_urls = [
        entry.strip()
        for entry in json.loads(list_file_path.read_text(encoding="utf-8"))
        if entry.strip()
    ]
    if not repository_urls:
        print(
            f"{list_file_path} declares no repository, which would leave the server unable to install any extension",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return repository_urls
