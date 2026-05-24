import sys
from pathlib import Path

from git_history_cache_file_inspection import (
    file_size_human,
    is_stale,
    line_count,
    stored_head,
)
from git_history_layer_dump import dump_layer
from git_history_repo_and_cache_paths import current_head


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
            print(
                f"Layer {layer}: {p} "
                f"({lines} lines, {size}, {status}, HEAD: {sh or 'none'})"
            )
        else:
            print(f"Layer {layer}: not dumped")


def cmd_clean(_args, root: Path, paths: dict[int, Path]) -> None:
    for p in paths.values():
        if p.exists():
            p.unlink()
    print(f"Cleaned cache for {root}", file=sys.stderr)
