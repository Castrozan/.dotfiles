import sys
from pathlib import Path

import pytest

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import jellyfin_library_declaration

LIVE_LIBRARIES = [
    {"Name": "Movies", "ItemId": "movies-id"},
    {"Name": "TV", "ItemId": "tv-id"},
    {"Name": "Movies (Private)", "ItemId": "movies-private-id"},
]


def test_public_libraries_resolve_in_declaration_order():
    assert jellyfin_library_declaration.resolve_public_library_ids(LIVE_LIBRARIES) == [
        "movies-id",
        "tv-id",
    ]


def test_private_library_is_never_resolved_as_public():
    assert (
        "movies-private-id"
        not in jellyfin_library_declaration.resolve_public_library_ids(LIVE_LIBRARIES)
    )


def test_resolve_refuses_an_empty_library_listing():
    with pytest.raises(ValueError, match="missing from Jellyfin"):
        jellyfin_library_declaration.resolve_public_library_ids([])


def test_resolve_refuses_a_partial_library_listing():
    with pytest.raises(ValueError, match="TV"):
        jellyfin_library_declaration.resolve_public_library_ids(
            [{"Name": "Movies", "ItemId": "movies-id"}]
        )


def test_resolve_refuses_a_library_with_a_blank_id():
    with pytest.raises(ValueError, match="Movies"):
        jellyfin_library_declaration.resolve_public_library_ids(
            [{"Name": "Movies", "ItemId": ""}, {"Name": "TV", "ItemId": "tv-id"}]
        )


def test_an_undeclared_library_counts_as_private():
    private_names = jellyfin_library_declaration.private_library_names_present(
        LIVE_LIBRARIES + [{"Name": "Home Videos", "ItemId": "home-id"}]
    )
    assert private_names == ["Movies (Private)", "Home Videos"]


def test_every_declared_private_library_lives_under_a_private_path():
    for declaration in jellyfin_library_declaration.PRIVATE_LIBRARY_DECLARATIONS:
        assert declaration["container_path"].endswith("-private")


def test_declared_libraries_have_unique_names_and_paths():
    declarations = jellyfin_library_declaration.ALL_LIBRARY_DECLARATIONS
    names = [declaration["name"] for declaration in declarations]
    paths = [declaration["container_path"] for declaration in declarations]
    assert len(set(names)) == len(names)
    assert len(set(paths)) == len(paths)
