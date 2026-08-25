from seanime_configuration import (
    desired_mpv_arguments,
    desired_torrentstream_settings,
    provider_user_config,
    read_prowlarr_api_key,
    required_environment_value,
)
from seanime_http import SeanimeHttpClient


def patch_setting(client, path, value):
    client.request_json(
        "PATCH",
        "/api/v1/settings/path",
        {"path": path, "value": value},
    )


def provision():
    seanime_url = required_environment_value("SEANIME_URL")
    tailnet_address = required_environment_value("SEANIME_TAILNET_ADDRESS")
    prowlarr_config_file = required_environment_value("SEANIME_PROWLARR_CONFIG_FILE")
    mpv_path = required_environment_value("SEANIME_MPV_PATH")
    client = SeanimeHttpClient(seanime_url)
    client.wait_until_ready()
    api_key = read_prowlarr_api_key(prowlarr_config_file)
    client.request_json(
        "POST",
        "/api/v1/extensions/user-config",
        provider_user_config(api_key, f"http://{tailnet_address}:9696"),
    )
    current_settings = client.request_json("GET", "/api/v1/torrentstream/settings")[
        "data"
    ]
    client.request_json(
        "PATCH",
        "/api/v1/torrentstream/settings",
        {"settings": desired_torrentstream_settings(current_settings)},
    )
    patch_setting(client, "library.torrentProvider", "prowlarr-torrent-provider")
    patch_setting(client, "mediaPlayer.defaultPlayer", "mpv")
    patch_setting(client, "mediaPlayer.mpvPath", mpv_path)
    patch_setting(client, "mediaPlayer.mpvArgs", desired_mpv_arguments())
    print("Seanime settings reconciled")


if __name__ == "__main__":
    provision()
