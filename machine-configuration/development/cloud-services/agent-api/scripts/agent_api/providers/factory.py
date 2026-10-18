from agent_api.providers.cloud import CloudProvider
from agent_api.providers.downloading import DownloadProvider
from agent_api.providers.media import MediaProvider
from agent_api.providers.processing import ProcessingProvider
from agent_api.providers.web import WebProvider


def create_provider(provider_name):
    if provider_name in ("trafilatura", "http"):
        return WebProvider()
    if provider_name == "yt-dlp":
        return DownloadProvider()
    if provider_name in ("ffmpeg", "whisper-cpp", "pandoc"):
        return ProcessingProvider()
    if provider_name == "media":
        return MediaProvider()
    return CloudProvider()
