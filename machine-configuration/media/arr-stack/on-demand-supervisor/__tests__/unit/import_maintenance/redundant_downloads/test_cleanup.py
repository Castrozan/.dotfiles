import copy

import pytest

import import_repair.redundant_downloads.cleanup as cleanup


def test_completed_pack_is_removed_only_after_all_library_files_are_verified(
    monkeypatch, completed_pack, run_cleanup
):
    removed, calls = run_cleanup()
    assert removed
    assert calls[-1][0] == "DELETE"
    assert len(calls) == 7
    assert all(timeout == 5 for _, _, timeout in calls)


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "downloading"),
        ("trackedDownloadState", "importPending"),
        ("sizeleft", 1),
        ("id", None),
        ("downloadId", "unknown"),
        ("seriesId", None),
        ("outputPath", "/data/torrents"),
        ("outputPath", "/data/torrents/../media/tv/series"),
        ("outputPath", "/data/media/tv/series"),
        ("statusMessages", [{"messages": ["Title mismatch"]}]),
    ],
)
def test_incomplete_unknown_or_unrelated_queue_items_are_untouched(
    monkeypatch, completed_pack, run_cleanup, field, value
):
    completed_pack[0][field] = value
    removed, calls = run_cleanup()
    assert not removed
    assert calls == []


@pytest.mark.parametrize(
    "mutation",
    [
        lambda values: values[1].clear(),
        lambda values: values[1][0].update(rejections=[]),
        lambda values: values[1][0]["rejections"].append({"reason": "Unknown series"}),
        lambda values: values[1][0].update(downloadId="b" * 40),
        lambda values: values[1][0].update(downloadId=None),
        lambda values: values[1][0].update(series={"id": 99}),
        lambda values: values[1][0].update(episodes=[]),
        lambda values: values[1][0]["episodes"][0].update(hasFile=False),
        lambda values: values[1][0]["episodes"][0].update(episodeFileId=0),
        lambda values: values[1][0].update(path="/data/torrents/elsewhere/file.mkv"),
        lambda values: values[1][0].update(
            path="/data/torrents/Solo.Leveling.S02/sub/file.mkv"
        ),
        lambda values: values[2][0].update(hasFile=False),
        lambda values: values[2][0].update(episodeFileId=999),
        lambda values: values[3][0].update(path="/data/torrents/library.mkv"),
        lambda values: values[3][0].update(size=0),
        lambda values: values[4]["/data/media/tv/Solo Leveling/Season 2/"][
            "files"
        ].pop(),
        lambda values: values[4]["/data/media/tv/Solo Leveling/Season 2/"]["files"][
            0
        ].update(size=1),
        lambda values: values[4][values[0]["outputPath"] + "/"]["files"].append(
            {
                "path": values[0]["outputPath"] + "/unknown.mkv",
                "size": 1,
                "type": "file",
            }
        ),
        lambda values: values[4][values[0]["outputPath"] + "/"]["directories"].append(
            {"path": "/unknown"}
        ),
        lambda values: values[1].extend(copy.deepcopy(values[1]) * 16),
    ],
)
def test_partial_mixed_stale_or_unverified_packs_are_preserved(
    monkeypatch, completed_pack, run_cleanup, mutation
):
    mutation(completed_pack)
    removed, calls = run_cleanup()
    assert not removed
    assert not any(method == "DELETE" for method, _, _ in calls)


def test_dry_run_validates_without_deleting(monkeypatch, completed_pack, run_cleanup):
    removed, calls = run_cleanup(dry_run=True)
    assert not removed
    assert not any(method == "DELETE" for method, _, _ in calls)


def test_transport_failure_preserves_download(monkeypatch, completed_pack, run_cleanup):
    monkeypatch.setattr(
        cleanup, "http_request", lambda *args, **kwargs: (503, "offline")
    )
    with pytest.raises(ValueError, match="503"):
        cleanup.remove_redundant_download(
            "http://sonarr", "key", completed_pack[0], False
        )


def test_sweep_deduplicates_and_bounds_work(monkeypatch, completed_pack, run_cleanup):
    record = completed_pack[0]
    records = [record] * 13 + [
        dict(record, downloadId=f"{number:040x}") for number in range(5)
    ]
    monkeypatch.setattr(cleanup, "read_arr_api_key_from_config_xml", lambda path: "key")
    monkeypatch.setattr(cleanup, "queued_records", lambda *args: records)
    selected = []
    monkeypatch.setattr(
        cleanup,
        "remove_redundant_download",
        lambda base, key, value, dry: selected.append(value["downloadId"]) or True,
    )
    cleanup.maybe_cleanup_redundant_downloads(
        {"sonarr_url": "url", "sonarr_config_file": "xml"}, 0, False
    )
    assert len(selected) == len(set(selected)) == 2


def test_private_library_files_are_verified(completed_pack, run_cleanup):
    for file in completed_pack[3]:
        file["path"] = file["path"].replace("/media/tv/", "/media/tv-private/")
    directories = completed_pack[4]
    original = "/data/media/tv/Solo Leveling/Season 2/"
    contents = directories.pop(original)
    for file in contents["files"]:
        file["path"] = file["path"].replace("/media/tv/", "/media/tv-private/")
    directories[original.replace("/media/tv/", "/media/tv-private/")] = contents
    removed, calls = run_cleanup()
    assert removed
    assert calls[-1][0] == "DELETE"


def test_single_episode_removal_preserves_neighboring_downloads(
    completed_pack, run_cleanup
):
    record, candidates, _, _, _ = completed_pack
    record["outputPath"] = candidates[0]["path"]
    del candidates[1:]
    removed, calls = run_cleanup()
    assert removed
    assert calls[-1][0] == "DELETE"
