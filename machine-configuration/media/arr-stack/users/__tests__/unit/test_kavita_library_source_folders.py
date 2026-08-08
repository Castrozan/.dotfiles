import io
import sys
import urllib.error
from pathlib import Path

import pytest
from kavita_test_doubles import declare_source_root, make_context, stub_kavita

ARR_USERS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_users"
)
sys.path.insert(0, str(ARR_USERS_PACKAGE_DIRECTORY_PATH))

import kavita_access_synchronization
import kavita_api_client
import kavita_library_source_folders


def test_the_manga_library_is_repointed_at_each_source_directory(monkeypatch, tmp_path):
    _, library_updates = stub_kavita(monkeypatch)
    (tmp_path / "MangaDex (EN)").mkdir()
    (tmp_path / "Weeb Central").mkdir()
    (tmp_path / "loose-file.cbz").write_text("")
    declare_source_root(monkeypatch, tmp_path)

    result = kavita_access_synchronization.synchronize_kavita_library_access(
        make_context()
    )

    assert result["repointed_libraries"] == ["Manga"]
    assert library_updates[0]["folders"] == [
        "/manga/MangaDex (EN)",
        "/manga/Weeb Central",
    ]
    assert library_updates[0]["id"] == 1
    assert library_updates[0]["fileGroupTypes"] == [1]


def test_a_library_already_pointing_at_its_sources_is_left_alone(monkeypatch, tmp_path):
    _, library_updates = stub_kavita(
        monkeypatch,
        libraries=[
            {"id": 1, "name": "Manga", "folders": ["/manga/MangaDex (EN)"], "type": 0}
        ],
    )
    (tmp_path / "MangaDex (EN)").mkdir()
    declare_source_root(monkeypatch, tmp_path)

    result = kavita_access_synchronization.synchronize_kavita_library_access(
        make_context()
    )

    assert result["repointed_libraries"] == []
    assert library_updates == []


def test_an_empty_source_root_never_blanks_the_library_folders(monkeypatch, tmp_path):
    _, library_updates = stub_kavita(monkeypatch)
    declare_source_root(monkeypatch, tmp_path)

    assert kavita_library_source_folders.resolve_source_library_folders() == []
    kavita_access_synchronization.synchronize_kavita_library_access(make_context())
    assert library_updates == []


def test_an_absent_source_root_never_blanks_the_library_folders(monkeypatch, tmp_path):
    _, library_updates = stub_kavita(monkeypatch)
    declare_source_root(monkeypatch, tmp_path / "never-mounted")

    kavita_access_synchronization.synchronize_kavita_library_access(make_context())
    assert library_updates == []


def test_a_refused_repoint_still_leaves_the_boundary_written(monkeypatch, tmp_path):
    account_updates, _ = stub_kavita(monkeypatch)
    (tmp_path / "MangaDex (EN)").mkdir()
    declare_source_root(monkeypatch, tmp_path)

    def refuse_library_update(base_url, token, library_update):
        raise urllib.error.HTTPError(
            f"{base_url}/api/Library/update", 400, "no", {}, io.BytesIO(b"")
        )

    monkeypatch.setattr(kavita_api_client, "update_library", refuse_library_update)

    with pytest.raises(urllib.error.HTTPError):
        kavita_access_synchronization.synchronize_kavita_library_access(make_context())
    assert [account_update["libraries"] for account_update in account_updates] == [
        [1, 2],
        [1],
    ]
