from agent_api.contract import CapabilityError
from agent_api.providers.downloading import DownloadProvider
from agent_api.providers.fal import FalProvider
from agent_api.providers.firecrawl import FirecrawlProvider
from agent_api.providers.media import MediaProvider
from agent_api.providers.monid import MonidProvider
from agent_api.providers.processing import ProcessingProvider
from agent_api.providers.web import WebProvider

PROVIDER_TYPES = {
    "trafilatura": WebProvider,
    "http": WebProvider,
    "yt-dlp": DownloadProvider,
    "ffmpeg": ProcessingProvider,
    "whisper-cpp": ProcessingProvider,
    "pandoc": ProcessingProvider,
    "media": MediaProvider,
    "monid": MonidProvider,
    "fal": FalProvider,
    "firecrawl": FirecrawlProvider,
}


def create_provider(provider_name):
    try:
        return PROVIDER_TYPES[provider_name]()
    except KeyError:
        raise CapabilityError("unsupported_provider") from None
