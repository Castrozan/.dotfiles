import json
import os
import pathlib
import sys
import time
import tomllib

import tomli_w


legacy_profile_names = ("fast", "deep", "web")
runtime_preserved_value_names = ("model",)
runtime_preserved_section_names = ("projects", "marketplaces", "plugins")
secret_file_wait_seconds = 10
secret_file_retry_seconds = 0.1
codex_config_path = pathlib.Path(
    os.environ.get("CODEX_CONFIG", "~/.codex/config.toml")
).expanduser()
nix_source_path = pathlib.Path(
    os.environ.get("NIX_SOURCE", "~/.codex/config.toml.nix-source")
).expanduser()


def read_required_toml_document(document_path: pathlib.Path) -> dict:
    with document_path.open("rb") as document_stream:
        return tomllib.load(document_stream)


def read_optional_toml_document(document_path: pathlib.Path) -> dict | None:
    try:
        return read_required_toml_document(document_path)
    except FileNotFoundError:
        return {}
    except (tomllib.TOMLDecodeError, OSError) as error:
        print(
            f"WARNING: {document_path} is not readable TOML, leaving it untouched: {error}",
            file=sys.stderr,
        )
        return None


def merge_runtime_preserved_configuration(
    nix_source: dict, current_config: dict
) -> dict:
    merged_config = dict(nix_source)
    for value_name in runtime_preserved_value_names:
        if value_name in current_config:
            merged_config[value_name] = current_config[value_name]
    for section_name in runtime_preserved_section_names:
        current_section = current_config.get(section_name)
        source_section = nix_source.get(section_name)
        if not isinstance(current_section, dict):
            continue
        if isinstance(source_section, dict):
            merged_config[section_name] = current_section | source_section
        elif section_name not in nix_source:
            merged_config[section_name] = current_section
    return merged_config


def trusted_project_parent_directories() -> tuple[pathlib.Path, ...]:
    configured_parent_directories = (
        pathlib.Path(parent_directory).expanduser()
        for parent_directory in os.environ.get(
            "CODEX_TRUSTED_PROJECT_PARENT_DIRECTORIES", ""
        ).splitlines()
        if parent_directory
    )
    return tuple(dict.fromkeys(configured_parent_directories))


def declarative_project_paths(nix_source: dict) -> set[str]:
    projects = nix_source.get("projects", {})
    return set(projects) if isinstance(projects, dict) else set()


def add_trusted_project_directories(
    config_data: dict, source_project_paths: set[str]
) -> None:
    projects = config_data.setdefault("projects", {})
    if not isinstance(projects, dict):
        projects = {}
        config_data["projects"] = projects
    for parent_directory in trusted_project_parent_directories():
        try:
            child_directories = sorted(
                child_directory
                for child_directory in parent_directory.iterdir()
                if child_directory.is_dir()
            )
        except OSError:
            continue
        for child_directory in child_directories:
            child_directory_path = str(child_directory)
            if child_directory.name.startswith("."):
                if child_directory_path not in source_project_paths and projects.get(
                    child_directory_path
                ) == {"trust_level": "trusted"}:
                    projects.pop(child_directory_path)
                continue
            projects.setdefault(child_directory_path, {"trust_level": "trusted"})


def read_secret_file(secret_file_path: str) -> str:
    deadline = time.monotonic() + secret_file_wait_seconds
    secret_path = pathlib.Path(secret_file_path).expanduser()
    while True:
        try:
            secret_value = secret_path.read_text("utf-8").strip()
            if secret_value:
                return secret_value
        except OSError:
            pass
        remaining_seconds = deadline - time.monotonic()
        if remaining_seconds <= 0:
            return ""
        time.sleep(min(secret_file_retry_seconds, remaining_seconds))


def inject_mcp_server_bearer_token_files(config_data: dict) -> None:
    raw_token_files = os.environ.get("CODEX_MCP_SERVER_BEARER_TOKEN_FILES", "")
    if not raw_token_files:
        return
    server_name_to_token_file = json.loads(raw_token_files)
    mcp_servers = config_data.get("mcp_servers")
    if not isinstance(mcp_servers, dict):
        return
    for server_name, token_file in server_name_to_token_file.items():
        server_definition = mcp_servers.get(server_name)
        if not isinstance(server_definition, dict):
            continue
        token = read_secret_file(token_file)
        if not token:
            mcp_servers.pop(server_name, None)
            continue
        server_definition.setdefault("http_headers", {})["Authorization"] = (
            f"Bearer {token}"
        )


def build_seeded_config_content() -> bytes | None:
    nix_source = read_required_toml_document(nix_source_path)
    current_config = read_optional_toml_document(codex_config_path)
    if current_config is None:
        return None
    merged_config = merge_runtime_preserved_configuration(nix_source, current_config)
    add_trusted_project_directories(
        merged_config, declarative_project_paths(nix_source)
    )
    inject_mcp_server_bearer_token_files(merged_config)
    return tomli_w.dumps(merged_config).encode()


def replace_live_config_with_seeded_content() -> None:
    seeded_content = build_seeded_config_content()
    if seeded_content is None:
        return
    if codex_config_path.exists() and codex_config_path.read_bytes() == seeded_content:
        codex_config_path.chmod(0o600)
        return

    codex_config_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_config_path = codex_config_path.with_name(
        f".{codex_config_path.name}.tmp"
    )
    try:
        temporary_config_path.write_bytes(seeded_content)
        temporary_config_path.chmod(0o600)
        temporary_config_path.replace(codex_config_path)
    finally:
        temporary_config_path.unlink(missing_ok=True)


def remove_legacy_generated_profiles() -> None:
    for profile_name in legacy_profile_names:
        profile_path = codex_config_path.parent / f"{profile_name}.config.toml"
        profile_path.unlink(missing_ok=True)


def main() -> int:
    if not nix_source_path.is_file():
        return 0
    replace_live_config_with_seeded_content()
    remove_legacy_generated_profiles()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
