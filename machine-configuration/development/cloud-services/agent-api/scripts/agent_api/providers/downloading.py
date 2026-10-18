from agent_api.contract import MAXIMUM_ARTIFACT_BYTES, CapabilityError, validate_url


class DownloadProvider:
    def preflight(self, request):
        validate_url(request.input["url"])

    def execute(self, request, directory, operation_id):
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import DownloadError

        def check_progress(progress):
            if progress.get("downloaded_bytes", 0) > MAXIMUM_ARTIFACT_BYTES:
                raise CapabilityError("artifact_too_large")

        options = {
            "noplaylist": True,
            "playlist_items": "1",
            "lazy_playlist": True,
            "extract_flat": "in_playlist",
            "quiet": True,
            "noprogress": True,
            "no_warnings": True,
            "retries": 0,
            "fragment_retries": 0,
            "extractor_retries": 0,
            "socket_timeout": min(request.timeout_seconds, 30),
            "max_filesize": MAXIMUM_ARTIFACT_BYTES,
            "concurrent_fragment_downloads": 1,
            "outtmpl": str(directory / "media.%(ext)s"),
            "progress_hooks": [check_progress],
            "format": "bestaudio/best"
            if request.input.get("audio_only")
            else "best[height<=1080]/best",
        }
        try:
            with YoutubeDL(options) as downloader:
                info = downloader.extract_info(
                    request.input["url"],
                    download=request.capability == "download.media",
                )
                if (
                    not info
                    or info.get("_type") in ("playlist", "multi_video")
                    or "entries" in info
                ):
                    raise CapabilityError("single_media_required")
                result = {
                    key: info.get(key)
                    for key in (
                        "id",
                        "title",
                        "duration",
                        "webpage_url",
                        "extractor",
                        "ext",
                    )
                }
                if request.capability == "download.media":
                    artifacts = [
                        path
                        for path in directory.glob("media.*")
                        if path.is_file() and path.suffix != ".part"
                    ]
                    if len(artifacts) != 1:
                        raise CapabilityError("download_incomplete")
                    result["artifact"] = artifacts[0].name
                return result
        except DownloadError:
            raise CapabilityError("download_failed") from None
