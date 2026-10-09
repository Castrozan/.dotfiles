import json
import subprocess
import sys
from pathlib import Path

from staged_command import command_failure_status
from staged_native import parse_native_options
from staged_sources import (
    archive_source,
    archived_input_overrides,
    archived_store_paths,
    local_source_directory,
    pin_local_source,
    retain_source_roots,
    without_source_overrides,
)


def prepare_rebuild_sources(request_path, public_directory, arguments):
    options = parse_native_options(arguments)
    if len(arguments) < 3 or arguments[1] != "--flake":
        raise ValueError("rebuild source must remain the machine-local entrypoint")
    public_reference = str(Path(public_directory)) + "?submodules=1"
    for name, reference in options.input_overrides:
        if name == "dotfiles":
            public_reference = reference
    public_directory = local_source_directory(public_reference)
    public_reference = pin_local_source(public_reference, "public")
    public_archive = archive_source(
        public_reference, options.archive_flags, "prefetch_public"
    )
    sources = archived_store_paths(public_archive)
    public_retention = Path(request_path).parent / "prefetch-public"
    public_retention.mkdir()
    retain_source_roots(sorted(sources), public_retention, "prefetch_public_retention")
    root_reference, configuration_name = options.flake_reference.split("#", 1)
    root_directory = local_source_directory(root_reference)
    root_reference = pin_local_source(root_reference, "entrypoint")
    if root_directory == Path(public_directory).resolve():
        root_archive = public_archive
        immutable_override = []
    else:
        immutable_override = [
            "--override-input",
            "dotfiles",
            "path:" + public_archive["path"],
        ]
        root_archive = archive_source(
            root_reference,
            [*options.archive_flags, *immutable_override],
            "prefetch_private",
        )
    sources.update(archived_store_paths(root_archive))
    retain_source_roots(
        sorted(sources), Path(request_path).parent, "prefetch_retention"
    )
    prepared_arguments = [
        options.action,
        "--flake",
        f"path:{root_archive['path']}#{configuration_name}",
        *without_source_overrides(arguments[3:]),
        *archived_input_overrides(root_archive),
    ]
    Path(request_path).write_text(
        json.dumps({"arguments": prepared_arguments, "sources": sorted(sources)})
    )


def main():
    try:
        prepare_rebuild_sources(sys.argv[1], sys.argv[2], sys.argv[3:])
        return 0
    except subprocess.CalledProcessError as error:
        return command_failure_status(error)
    except (OSError, ValueError, KeyError) as error:
        print(f"error: rebuild source preparation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
