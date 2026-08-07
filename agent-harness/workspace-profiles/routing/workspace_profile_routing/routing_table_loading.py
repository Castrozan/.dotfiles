import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkspaceProfileRoute:
    name: str
    directory_prefixes: tuple[str, ...]
    git_remote_patterns: tuple[str, ...]


def parse_routing_table(
    routing_table_document: str,
) -> tuple[WorkspaceProfileRoute, ...]:
    declared_profiles = json.loads(routing_table_document).get("profiles", [])
    return tuple(
        WorkspaceProfileRoute(
            name=declared_profile["name"],
            directory_prefixes=tuple(declared_profile.get("directoryPrefixes", ())),
            git_remote_patterns=tuple(declared_profile.get("gitRemotePatterns", ())),
        )
        for declared_profile in declared_profiles
    )


def load_routing_table(
    routing_table_path: Path | None,
) -> tuple[WorkspaceProfileRoute, ...]:
    if routing_table_path is None or not routing_table_path.is_file():
        return ()
    return parse_routing_table(routing_table_path.read_text(encoding="utf-8"))
