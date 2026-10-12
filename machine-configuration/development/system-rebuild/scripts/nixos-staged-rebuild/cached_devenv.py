import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from staged_command import run_command
from staged_sources import archived_input_overrides, validate_store_path


@dataclass(frozen=True)
class CachedDevenv:
    store_path: str
    nar_hash: str
    cache_url: str
    public_key: str


def read_cached_devenv(public_archive):
    metadata = json.loads(
        run_command(
            "prefetch_devenv_metadata",
            [
                "nix",
                "--extra-experimental-features",
                "nix-command flakes",
                "eval",
                "--json",
                "--offline",
                "--no-write-lock-file",
                *archived_input_overrides(public_archive),
                f"path:{public_archive['path']}#packages.x86_64-linux.devenv.binaryCache",
            ],
            True,
        )
    )
    if not isinstance(metadata, dict):
        raise ValueError("Devenv binary-cache metadata must be an object")
    names = ("storePath", "narHash", "cacheUrl", "publicKey")
    if not all(isinstance(metadata.get(name), str) for name in names):
        raise ValueError("Devenv binary-cache metadata fields must be strings")
    cached_devenv = CachedDevenv(*(metadata[name] for name in names))
    validate_cached_devenv(cached_devenv)
    return cached_devenv


def validate_cached_devenv(cached_devenv):
    validate_store_path(cached_devenv.store_path)
    if not re.fullmatch(
        r"sha256:[0-9abcdfghijklmnpqrsvwxyz]{52}", cached_devenv.nar_hash
    ):
        raise ValueError("Devenv binary-cache NAR hash is invalid")
    cache_url = urlsplit(cached_devenv.cache_url)
    if cache_url.scheme != "https" or not cache_url.netloc:
        raise ValueError("Devenv binary cache must use HTTPS")
    if not cached_devenv.public_key:
        raise ValueError("Devenv binary cache must declare its signing key")


def prefetch_cached_devenv(public_archive, retention_path, archive_flags):
    cached_devenv = read_cached_devenv(public_archive)
    offline_flags = (
        ["--option", "substitute", "false"] if "--offline" in archive_flags else []
    )
    run_command(
        "prefetch_devenv",
        [
            "nix-store",
            "--realise",
            cached_devenv.store_path,
            "--add-root",
            retention_path,
            "--indirect",
            "--max-jobs",
            "0",
            "--option",
            "extra-substituters",
            cached_devenv.cache_url,
            "--option",
            "extra-trusted-public-keys",
            cached_devenv.public_key,
            "--option",
            "max-substitution-jobs",
            "1",
            "--option",
            "http-connections",
            "2",
            *offline_flags,
        ],
        True,
    )
    if Path(retention_path).resolve() != Path(cached_devenv.store_path):
        raise ValueError("Devenv binary cache returned a different store path")
    nar_hash = run_command(
        "prefetch_devenv_integrity",
        ["nix-store", "--query", "--hash", cached_devenv.store_path],
        True,
    )
    if nar_hash != cached_devenv.nar_hash:
        raise ValueError(
            "Devenv binary-cache NAR hash does not match the pinned package"
        )
    return cached_devenv.store_path
