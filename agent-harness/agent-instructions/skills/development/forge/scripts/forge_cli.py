import argparse
from dataclasses import asdict
import json
from pathlib import Path
import subprocess

from forge.repository import resolve_repository
from forge.native import runs_for_revision


def main():
    parser = argparse.ArgumentParser(
        prog="git-forge",
        description="Resolve a Git repository's hosting provider and inspect its CI.",
    )
    parser.add_argument(
        "--repo", help="full Git URL or project path on the current upstream host"
    )
    parser.add_argument(
        "--provider",
        choices=["github", "gitlab"],
        help="provider for an unregistered enterprise host",
    )
    parser.add_argument(
        "--commit",
        help="list CI runs for one full commit SHA instead of repository context",
    )
    options = parser.parse_args()
    try:
        repository = resolve_repository(Path.cwd(), options.repo, options.provider)
        if options.commit:
            result = runs_for_revision(repository, options.commit)
        else:
            result = {**asdict(repository), "url": repository.url}
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(2, f"git-forge: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
