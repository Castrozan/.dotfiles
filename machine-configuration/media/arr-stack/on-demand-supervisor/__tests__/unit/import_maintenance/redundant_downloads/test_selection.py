import pytest

import import_repair.redundant_downloads.cleanup as cleanup
from import_repair.redundant_downloads.selection import read_cursor, select_downloads


@pytest.fixture
def queued_packs(completed_pack):
    return [dict(completed_pack[0], downloadId=f"{number:040x}") for number in range(5)]


def test_cursor_advances_after_selected_downloads_leave_queue(tmp_path, queued_packs):
    cursor = tmp_path / "cursor"
    remaining = queued_packs
    for expected in ([0, 1], [2, 3], [4]):
        selected = select_downloads(remaining, cursor, False)
        assert [int(record["downloadId"], 16) for record in selected] == expected
        remaining = [record for record in remaining if record not in selected]
    assert select_downloads(remaining, cursor, False) == []


@pytest.mark.parametrize("existing_cursor", [False, True])
def test_dry_run_preserves_cursor(tmp_path, queued_packs, existing_cursor):
    cursor = tmp_path / "cursor"
    if existing_cursor:
        cursor.write_text(queued_packs[1]["downloadId"])
    assert len(select_downloads(queued_packs, cursor, True)) == 2
    assert cursor.exists() == existing_cursor
    if existing_cursor:
        assert cursor.read_text() == queued_packs[1]["downloadId"]


@pytest.mark.parametrize("value", ["", "broken", "f" * 100])
def test_invalid_cursor_recovers(tmp_path, queued_packs, value):
    cursor = tmp_path / "cursor"
    cursor.write_text(value)
    selected = select_downloads(queued_packs, cursor, False)
    assert selected == queued_packs[:2]
    assert cursor.read_text().strip() == queued_packs[1]["downloadId"]


@pytest.mark.parametrize("length", [40, 64])
def test_cursor_accepts_native_torrent_identities(tmp_path, length):
    cursor = tmp_path / "cursor"
    cursor.write_text("A" * length + "\n")
    assert read_cursor(cursor) == "a" * length


def test_unavailable_cursor_preserves_downloads(monkeypatch, tmp_path, queued_packs):
    monkeypatch.setattr(cleanup, "read_arr_api_key_from_config_xml", lambda path: "key")
    monkeypatch.setattr(cleanup, "queued_records", lambda *args: queued_packs)
    selected = []
    monkeypatch.setattr(
        cleanup,
        "remove_redundant_download",
        lambda *args: selected.append(args),
    )
    cleanup.maybe_cleanup_redundant_downloads(
        {
            "sonarr_url": "url",
            "sonarr_config_file": "xml",
            "state_file_path": str(tmp_path / "missing" / "last-active"),
        },
        False,
    )
    assert selected == []
