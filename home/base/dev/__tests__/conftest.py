import sys
from pathlib import Path

development_module_directory = Path(__file__).resolve().parent.parent
repository_root_directory = development_module_directory.parent.parent.parent

for scripts_directory in (
    development_module_directory / "scripts",
    development_module_directory / "agent-commit-provenance" / "scripts",
    repository_root_directory / "agents" / "scripts",
):
    sys.path.insert(0, str(scripts_directory))
