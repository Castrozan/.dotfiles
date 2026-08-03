#!/usr/bin/env python3
"""git-history: dump git log layers to /tmp for fast text search.

Portable - works on any git repo. Uses repo root path as cache key.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from git_history_cache_file_inspection import (  # noqa: E402, F401
    file_size_human,
    is_stale,
    line_count,
    stored_head,
)
from git_history_layer_dump import dump_layer  # noqa: E402, F401
from git_history_repo_and_cache_paths import (  # noqa: E402, F401
    cache_paths,
    current_head,
    git_root,
)
from git_history_subcommand_handlers import (  # noqa: E402, F401
    cmd_clean,
    cmd_dump,
    cmd_info,
    cmd_path,
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-history",
        description="Dump git log layers to /tmp for fast text search.",
    )
    parser.add_argument("--repo", help="Path to repo (default: current git root)")

    sub = parser.add_subparsers(dest="command")

    dump_p = sub.add_parser("dump", help="Dump git log to /tmp")
    dump_p.add_argument(
        "--layer",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Layer to dump",
    )
    dump_p.add_argument("--force", action="store_true", help="Re-dump even if fresh")

    path_p = sub.add_parser("path", help="Print cache file path")
    path_p.add_argument(
        "--layer",
        type=int,
        default=1,
        choices=[1, 2],
        help="Layer path",
    )

    sub.add_parser("info", help="Show cache status")
    sub.add_parser("clean", help="Remove cached files")

    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()
    if not args.command:
        args.command = "dump"
        args.layer = 1
        args.force = False

    root = git_root(args.repo)
    paths = cache_paths(root)

    commands = {
        "dump": cmd_dump,
        "path": cmd_path,
        "info": cmd_info,
        "clean": cmd_clean,
    }
    commands[args.command](args, root, paths)


if __name__ == "__main__":
    main()
