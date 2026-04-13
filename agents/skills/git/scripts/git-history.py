#!/usr/bin/env python3
"""git-history: dump git log layers to /tmp for fast text search.

Portable — works on any git repo. Uses repo root path as cache key.
"""

import argparse
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path


def git_root(repo: str | None = None) -> Path:
    cmd = ["git", "rev-parse", "--show-toplevel"]
    if repo:
        cmd = ["git", "-C", repo, "rev-parse", "--show-toplevel"]
    try:
        return Path(subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip())
    except subprocess.CalledProcessError:
        target = repo or "current directory"
        print(f"error: not a git repo: {target}", file=sys.stderr)
        sys.exit(1)


def cache_paths(root: Path) -> dict[int, Path]:
    repo_hash = hashlib.md5(str(root).encode()).hexdigest()[:12]
    name = root.name
    return {
        1: Path(f"/tmp/gitlog-{name}-{repo_hash}-L1.txt"),
        2: Path(f"/tmp/gitlog-{name}-{repo_hash}-L2.txt"),
    }


def current_head(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return "unknown"


def stored_head(path: Path) -> str:
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        first_line = f.readline().decode(errors="replace").strip()
    if first_line.startswith("# HEAD: "):
        return first_line[8:]
    return ""


def is_stale(path: Path, head: str) -> bool:
    if not path.exists():
        return True
    if stored_head(path) != head:
        return True
    age = time.time() - path.stat().st_mtime
    return age > 3600


def file_size_human(path: Path) -> str:
    size = path.stat().st_size
    for unit in ("B", "K", "M", "G"):
        if size < 1024:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}T"


def line_count(path: Path) -> int:
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def dump_layer(root: Path, layer: int, paths: dict[int, Path], force: bool) -> None:
    path = paths[layer]
    head = current_head(root)

    if not force and not is_stale(path, head):
        lines = line_count(path)
        print(f"{path} ({lines} lines, fresh)", file=sys.stderr)
        return

    git_base = ["git", "-C", str(root)]

    if layer == 1:
        print("Dumping layer 1: titles + file paths...", file=sys.stderr)
        git_cmd = git_base + ["log", "--all", "--format=%h %s%n%b", "--name-only"]
        layer_desc = "1 (titles + file paths)"
    else:
        print("Dumping layer 2: full patches...", file=sys.stderr)
        git_cmd = git_base + ["log", "--all", "-p", "--format=%h %s"]
        layer_desc = "2 (full patches)"

    header = (
        f"# HEAD: {head}\n"
        f"# Repo: {root}\n"
        f"# Layer: {layer_desc}\n"
        f"# Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}\n\n"
    )
    result = subprocess.run(git_cmd, capture_output=True)
    if result.returncode != 0:
        print(f"error: git log failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(1)
    with open(path, "wb") as f:
        f.write(header.encode())
        f.write(result.stdout)

    lines = line_count(path)
    size = file_size_human(path)
    print(f"{path} ({lines} lines, {size})", file=sys.stderr)


def cmd_dump(args, root: Path, paths: dict[int, Path]) -> None:
    layers = [1, 2] if args.layer == 3 else [args.layer]
    for layer in layers:
        dump_layer(root, layer, paths, args.force)


def cmd_path(args, _root: Path, paths: dict[int, Path]) -> None:
    layer = args.layer if args.layer in (1, 2) else 1
    print(paths[layer])


def cmd_info(_args, root: Path, paths: dict[int, Path]) -> None:
    head = current_head(root)
    print(f"Repo: {root}")
    print(f"HEAD: {head}")
    print()
    for layer in (1, 2):
        p = paths[layer]
        if p.exists():
            lines = line_count(p)
            size = file_size_human(p)
            sh = stored_head(p)
            status = "stale" if is_stale(p, head) else "fresh"
            print(f"Layer {layer}: {p} ({lines} lines, {size}, {status}, HEAD: {sh or 'none'})")
        else:
            print(f"Layer {layer}: not dumped")


def cmd_clean(_args, _root: Path, paths: dict[int, Path]) -> None:
    for p in paths.values():
        if p.exists():
            p.unlink()
    print(f"Cleaned cache for {_root}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="git-history",
        description="Dump git log layers to /tmp for fast text search.",
    )
    parser.add_argument("--repo", help="Path to repo (default: current git root)")

    sub = parser.add_subparsers(dest="command")

    dump_p = sub.add_parser("dump", help="Dump git log to /tmp")
    dump_p.add_argument("--layer", type=int, default=1, choices=[1, 2, 3], help="Layer to dump")
    dump_p.add_argument("--force", action="store_true", help="Re-dump even if fresh")

    path_p = sub.add_parser("path", help="Print cache file path")
    path_p.add_argument("--layer", type=int, default=1, choices=[1, 2], help="Layer path")

    sub.add_parser("info", help="Show cache status")
    sub.add_parser("clean", help="Remove cached files")

    args = parser.parse_args()
    if not args.command:
        args.command = "dump"
        args.layer = 1
        args.force = False

    root = git_root(args.repo)
    paths = cache_paths(root)

    commands = {"dump": cmd_dump, "path": cmd_path, "info": cmd_info, "clean": cmd_clean}
    commands[args.command](args, root, paths)


if __name__ == "__main__":
    main()
