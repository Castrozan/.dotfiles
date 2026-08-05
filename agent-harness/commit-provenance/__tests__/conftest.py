import sys
from pathlib import Path

commit_provenance_directory = Path(__file__).resolve().parent.parent
repository_root_directory = commit_provenance_directory.parent.parent

for scripts_directory in (
    commit_provenance_directory / "scripts",
    repository_root_directory / "agent-harness" / "session-control",
):
    sys.path.insert(0, str(scripts_directory))
