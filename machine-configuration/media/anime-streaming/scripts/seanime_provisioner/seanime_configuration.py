import os
import xml.etree.ElementTree as element_tree


def required_environment_value(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def read_prowlarr_api_key(config_file):
    api_key = element_tree.parse(config_file).getroot().findtext("ApiKey", "").strip()
    if not api_key:
        raise RuntimeError("Prowlarr API key is missing")
    return api_key


def desired_torrentstream_settings(current, tailnet_address):
    return current | {
        "enabled": True,
        "autoSelect": True,
        "downloadDir": "",
        "addToLibrary": False,
        "torrentClientHost": tailnet_address,
        "streamingServerHost": "127.0.0.1",
        "includeInLibrary": False,
        "streamUrlAddress": "",
        "preloadNextStream": False,
    }


def provider_user_config(api_key, prowlarr_base_url):
    return {
        "id": "prowlarr-torrent-provider",
        "version": 1,
        "values": {
            "prowlarrBaseUrl": prowlarr_base_url,
            "prowlarrApiKey": api_key,
            "resultLimit": "50",
        },
    }
