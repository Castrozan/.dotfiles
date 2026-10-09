import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

from staged_command import run_command

STORE_PATH_PATTERN = re.compile(r"^/nix/store/[0-9abcdfghijklmnpqrsvwxyz]{32}-[^/\s]+$")


def validate_store_path(value):
    if not isinstance(value, str) or not STORE_PATH_PATTERN.fullmatch(value):
        raise ValueError("rebuild phase did not return an immutable store path")
    return value


def local_source_directory(reference):
    source = urlsplit(reference.split("#", 1)[0])
    if source.scheme not in ("", "git+file") or source.netloc not in ("", "localhost"):
        raise ValueError("staged rebuild requires an immutable local flake")
    return Path(unquote(source.path)).resolve()


def pin_local_source(reference, phase):
    source = urlsplit(reference.split("#", 1)[0])
    directory = local_source_directory(reference)
    query = dict(parse_qsl(source.query))
    selected_revision = query.get("rev", "HEAD")
    revision = run_command(
        f"{phase}_revision",
        [
            "git",
            "-C",
            directory,
            "rev-parse",
            "--verify",
            "--end-of-options",
            f"{selected_revision}^{{commit}}",
        ],
        True,
    )
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise ValueError("source revision is not immutable")
    dirty = run_command(
        f"{phase}_state",
        ["git", "-C", directory, "status", "--porcelain=v1", "--untracked-files=no"],
        True,
    )
    if dirty:
        raise ValueError("refusing to prefetch a dirty rebuild source")
    query["rev"] = revision
    return urlunsplit(("git+file", "", quote(str(directory)), urlencode(query), ""))


def archive_source(reference, flags, phase):
    output = run_command(
        phase,
        [
            "nix",
            "--extra-experimental-features",
            "nix-command flakes",
            "flake",
            "archive",
            "--json",
            *flags,
            "--no-write-lock-file",
            "--option",
            "allow-import-from-derivation",
            "false",
            reference,
        ],
        True,
    )
    return json.loads(output)


def archived_store_paths(archive):
    paths = {validate_store_path(archive["path"])} if "path" in archive else set()
    for archived_input in archive.get("inputs", {}).values():
        paths.update(archived_store_paths(archived_input))
    return paths


def archived_input_overrides(archive, parent_input=()):
    overrides = []
    for name, archived_input in archive.get("inputs", {}).items():
        input_path = (*parent_input, name)
        if "path" in archived_input:
            overrides.extend(
                [
                    "--override-input",
                    "/".join(input_path),
                    "path:" + validate_store_path(archived_input["path"]),
                ]
            )
        overrides.extend(archived_input_overrides(archived_input, input_path))
    return overrides


def without_source_overrides(arguments):
    remaining = []
    position = 0
    while position < len(arguments):
        argument = arguments[position]
        if argument == "--override-input":
            position += 3
        elif argument == "--flake":
            position += 2
        elif argument.startswith("--override-input="):
            position += 2
        elif argument.startswith("--flake="):
            position += 1
        else:
            remaining.append(argument)
            position += 1
    return remaining


def read_prepared_request(request_path, action):
    request = json.loads(Path(request_path).read_text())
    arguments = request["arguments"]
    if not isinstance(arguments, list) or not all(
        isinstance(value, str) for value in arguments
    ):
        raise ValueError("prepared rebuild arguments are invalid")
    if not arguments or arguments[0] != action:
        raise ValueError("prepared rebuild action does not match the guarded action")
    sources = request["sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError("prepared rebuild sources are missing")
    for source in sources:
        validate_store_path(source)
    if len(arguments) < 3 or arguments[1] != "--flake":
        raise ValueError("prepared rebuild source is missing")
    required_sources = [arguments[2].split("#", 1)[0]]
    for index, argument in enumerate(arguments):
        if argument == "--override-input":
            if index + 2 >= len(arguments):
                raise ValueError("prepared rebuild input override is incomplete")
            required_sources.append(arguments[index + 2])
    for source in required_sources:
        if (
            not source.startswith("path:")
            or source.removeprefix("path:") not in sources
        ):
            raise ValueError("prepared rebuild source was not prefetched")
    return arguments, sources


def retain_source_roots(sources, directory, phase):
    run_command(
        phase,
        [
            "nix-store",
            "--realise",
            *(validate_store_path(source) for source in sources),
            "--add-root",
            Path(directory) / "sources",
            "--indirect",
        ],
        True,
    )
