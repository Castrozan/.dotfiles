import json

from recording import byte_range_request_handler as byte_range
import scene_video_cache as video_cache


def test_full_byte_range_resolves_to_the_whole_file():
    assert byte_range.resolve_requested_byte_range("bytes=0-", 1000) == (0, 999)


def test_open_ended_byte_range_clamps_to_the_final_byte():
    assert byte_range.resolve_requested_byte_range("bytes=900-5000", 1000) == (900, 999)


def test_suffix_byte_range_counts_back_from_the_end():
    assert byte_range.resolve_requested_byte_range("bytes=-200", 1000) == (800, 999)


def test_scene_video_directory_sits_beside_the_recorded_loop(tmp_path):
    assert video_cache.resolve_scene_video_directory(str(tmp_path)).endswith("/videos")


def test_missing_manifest_yields_no_scene_videos(tmp_path):
    assert video_cache.read_scene_video_manifest(str(tmp_path)) == []


def test_download_arguments_request_a_premuxed_format_so_ffmpeg_is_never_needed():
    arguments = video_cache.build_download_arguments(
        "https://www.youtube.com/watch?v=abc123", "/state/videos/abc123.mp4"
    )
    assert arguments[0] == "yt-dlp"
    assert "--format" in arguments
    assert (
        arguments[arguments.index("--format") + 1]
        == "18/best[height<=480][ext=mp4]/best[ext=mp4]/best"
    )
    assert arguments[arguments.index("--output") + 1] == "/state/videos/abc123.mp4"
    assert arguments[-1] == "https://www.youtube.com/watch?v=abc123"


def test_the_format_selector_falls_back_past_youtube_only_constraints():
    selector = video_cache.YT_DLP_FORMAT_SELECTOR.split("/")
    assert selector[0] == "18"
    assert selector[-1] == "best"


def test_already_cached_scene_videos_are_not_downloaded_again(tmp_path, monkeypatch):
    web_directory = tmp_path / "web"
    web_directory.mkdir()
    (web_directory / "scene-videos.json").write_text(
        json.dumps({"videos": [{"id": "cached"}, {"id": "missing"}]})
    )
    state_directory = tmp_path / "state"
    video_directory = state_directory / "videos"
    video_directory.mkdir(parents=True)
    (video_directory / "cached.mp4").write_bytes(b"already here")

    attempted_video_ids = []

    def fake_run(arguments, **ignored):
        attempted_video_ids.append(arguments[-1])
        destination = arguments[arguments.index("--output") + 1]
        with open(destination, "wb") as downloaded_file:
            downloaded_file.write(b"downloaded")

        class CompletedDownload:
            returncode = 0

        return CompletedDownload()

    monkeypatch.setattr(video_cache.subprocess, "run", fake_run)
    downloaded = video_cache.download_missing_scene_videos(
        str(web_directory), str(video_directory)
    )
    assert downloaded == ["missing"]
    assert attempted_video_ids == ["https://www.youtube.com/watch?v=missing"]


def test_a_url_backed_scene_video_caches_under_its_manifest_identifier(
    tmp_path, monkeypatch
):
    web_directory = tmp_path / "web"
    web_directory.mkdir()
    (web_directory / "scene-videos.json").write_text(
        json.dumps(
            {
                "videos": [
                    {
                        "id": "crego-the-link",
                        "url": "https://x.com/ALCrego_/status/123",
                    }
                ]
            }
        )
    )
    state_directory = tmp_path / "state"
    requested_urls = []

    def fake_run(arguments, **ignored):
        requested_urls.append(arguments[-1])
        destination = arguments[arguments.index("--output") + 1]
        with open(destination, "wb") as downloaded_file:
            downloaded_file.write(b"downloaded")

        class CompletedDownload:
            returncode = 0

        return CompletedDownload()

    monkeypatch.setattr(video_cache.subprocess, "run", fake_run)
    assert video_cache.download_missing_scene_videos(
        str(web_directory), str(state_directory / "videos")
    ) == ["crego-the-link"]
    assert requested_urls == ["https://x.com/ALCrego_/status/123"]
    assert (state_directory / "videos" / "crego-the-link.mp4").is_file()
