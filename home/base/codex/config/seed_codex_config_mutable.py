import os
import pathlib
import sys
import tomllib

import tomli_w


legacy_profile_names = ("fast", "deep", "web")
runtime_preserved_section_names = ("projects", "marketplaces", "plugins")
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


def merge_runtime_preserved_sections(nix_source: dict, current_config: dict) -> dict:
    merged_config = dict(nix_source)
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


def add_trusted_project_directories(config_data: dict) -> None:
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
            if child_directory.name.startswith("."):
                if projects.get(str(child_directory)) == {"trust_level": "trusted"}:
                    projects.pop(str(child_directory))
                continue
            projects.setdefault(str(child_directory), {"trust_level": "trusted"})


def build_seeded_config_content() -> bytes | None:
    nix_source = read_required_toml_document(nix_source_path)
    current_config = read_optional_toml_document(codex_config_path)
    if current_config is None:
        return None
    merged_config = merge_runtime_preserved_sections(nix_source, current_config)
    add_trusted_project_directories(merged_config)
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
