from fnmatch import fnmatchcase
from pathlib import Path
import re

import yaml

REPOSITORY = Path(__file__).resolve().parents[5]
WORKFLOW = REPOSITORY / ".github/workflows/nix-binary-cache.yml"


def nix_files_imported_by(entry_file):
    pending = [entry_file]
    imported = set()
    while pending:
        current = pending.pop()
        if current in imported:
            continue
        imported.add(current)
        for relative in re.findall(
            r"import\s+(\.{1,2}/[^\s;)]+\.nix)", current.read_text()
        ):
            pending.append((current.parent / relative).resolve())
    return imported


def test_every_test_environment_source_triggers_a_cache_publish():
    trigger_paths = yaml.safe_load(WORKFLOW.read_text())[True]["push"]["paths"]
    environment_sources = nix_files_imported_by(
        REPOSITORY
        / "machine-configuration/development/testing/test-suite-environment.nix"
    )
    untriggered = sorted(
        str(source.relative_to(REPOSITORY))
        for source in environment_sources
        if not any(
            fnmatchcase(str(source.relative_to(REPOSITORY)), pattern)
            for pattern in trigger_paths
        )
    )
    assert untriggered == []
