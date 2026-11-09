from __future__ import annotations

import hashlib
import os
import plistlib
import re
import xml.parsers.expat
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

FINDER_BUNDLE_PATH = Path("/System/Library/CoreServices/Finder.app")
FILE_NAME_SAFE_IDENTIFIER = re.compile(r"[A-Za-z0-9._-]+")
SOFT_HYPHEN = "­"


@dataclass(frozen=True)
class InstalledApplication:
    bundle_path: Path
    identifier: str
    display_name: str
    search_keywords: tuple[str, ...]
    icon_source_path: Path | None


def application_search_roots(home_directory: Path) -> list[Path]:
    return [
        Path("/Applications"),
        Path("/System/Applications"),
        Path("/System/Library/CoreServices/Applications"),
        home_directory / "Applications",
    ]


def sorted_directory_children(directory: Path) -> list[Path]:
    try:
        return sorted(directory.iterdir())
    except OSError:
        return []


def is_application_bundle(path: Path) -> bool:
    return path.name.endswith(".app")


def bundle_and_embedded_applications(bundle_path: Path) -> Iterator[Path]:
    yield bundle_path
    embedded_directory = bundle_path / "Contents" / "Applications"
    yield from filter(
        is_application_bundle, sorted_directory_children(embedded_directory)
    )


def discover_application_bundle_paths(search_roots: Iterable[Path]) -> Iterator[Path]:
    for search_root in search_roots:
        for child in sorted_directory_children(search_root):
            if is_application_bundle(child):
                yield from bundle_and_embedded_applications(child)
                continue
            for grandchild in filter(
                is_application_bundle, sorted_directory_children(child)
            ):
                yield from bundle_and_embedded_applications(grandchild)
    yield from bundle_and_embedded_applications(FINDER_BUNDLE_PATH)


def read_bundle_information(bundle_path: Path) -> dict | None:
    try:
        with (bundle_path / "Contents" / "Info.plist").open("rb") as information_file:
            information = plistlib.load(information_file)
    except (OSError, ValueError, xml.parsers.expat.ExpatError):
        return None
    return information if isinstance(information, dict) else None


def application_identifier(bundle_path: Path, information: dict) -> str | None:
    bundle_identifier = information.get("CFBundleIdentifier")
    if isinstance(bundle_identifier, str) and bundle_identifier:
        return bundle_identifier
    executable_name = information.get("CFBundleExecutable")
    if not isinstance(executable_name, str) or not executable_name:
        return None
    if not os.access(bundle_path / "Contents" / "MacOS" / executable_name, os.X_OK):
        return None
    resolved_path_digest = hashlib.sha256(
        str(bundle_path.resolve()).encode()
    ).hexdigest()
    return f"path-{resolved_path_digest[:16]}"


def application_display_name(bundle_path: Path) -> str:
    return bundle_path.name.removesuffix(".app").replace(SOFT_HYPHEN, "")


def application_search_keywords(
    display_name: str, information: dict
) -> tuple[str, ...]:
    candidates = (
        information.get(key)
        for key in ("CFBundleDisplayName", "CFBundleName", "CFBundleExecutable")
    )
    distinct_keywords = dict.fromkeys(
        candidate
        for candidate in candidates
        if isinstance(candidate, str) and candidate and candidate != display_name
    )
    return tuple(distinct_keywords)


def application_icon_source_path(bundle_path: Path, information: dict) -> Path | None:
    for key in ("CFBundleIconFile", "CFBundleIconName"):
        icon_name = information.get(key)
        if not isinstance(icon_name, str) or not icon_name:
            continue
        icon_path = (
            bundle_path
            / "Contents"
            / "Resources"
            / f"{icon_name.removesuffix('.icns')}.icns"
        )
        if icon_path.is_file():
            return icon_path
    return None


def read_installed_application(bundle_path: Path) -> InstalledApplication | None:
    information = read_bundle_information(bundle_path)
    if information is None:
        return None
    identifier = application_identifier(bundle_path, information)
    if identifier is None or not FILE_NAME_SAFE_IDENTIFIER.fullmatch(identifier):
        return None
    display_name = application_display_name(bundle_path)
    if not display_name.isprintable():
        return None
    return InstalledApplication(
        bundle_path=bundle_path,
        identifier=identifier,
        display_name=display_name,
        search_keywords=application_search_keywords(display_name, information),
        icon_source_path=application_icon_source_path(bundle_path, information),
    )


def installed_applications_by_identifier(
    bundle_paths: Iterable[Path],
) -> dict[str, InstalledApplication]:
    applications: dict[str, InstalledApplication] = {}
    for bundle_path in bundle_paths:
        application = read_installed_application(bundle_path)
        if application is not None:
            applications.setdefault(application.identifier, application)
    return applications
