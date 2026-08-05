from qbittorrent_api_client import (
    build_authenticated_opener,
    read_preferences,
    write_preferences,
)

SEEDING_STOP_PREFERENCES = (
    "max_ratio_enabled",
    "max_seeding_time_enabled",
    "max_inactive_seeding_time_enabled",
)
UNLIMITED_ACTIVE_TORRENT_PREFERENCES = ("max_active_torrents", "max_active_uploads")


def assert_desired_preferences_never_stop_seeding(desired_preferences):
    enabled_stops = [
        name
        for name in SEEDING_STOP_PREFERENCES
        if desired_preferences.get(name) is True
    ]
    if enabled_stops:
        raise ValueError(
            "refusing to declare qbittorrent preferences that stop seeding on a "
            f"limit ({', '.join(enabled_stops)}); a private tracker counts a torrent "
            "that stopped seeding as a hit and run and issues a permanent warning"
        )
    capped = [
        name
        for name in UNLIMITED_ACTIVE_TORRENT_PREFERENCES
        if desired_preferences.get(name, -1) >= 0
    ]
    if capped:
        raise ValueError(
            "refusing to declare a finite active-torrent cap "
            f"({', '.join(capped)}); torrents past the cap sit queued rather than "
            "seeding, which reads to a private tracker exactly like never seeding"
        )


def preferences_needing_change(live_preferences, desired_preferences):
    return {
        name: desired_value
        for name, desired_value in desired_preferences.items()
        if live_preferences.get(name) != desired_value
    }


def provision_qbittorrent_preferences(
    base_url, username, password, desired_preferences, dry_run
):
    if not desired_preferences:
        return "skipped: nothing declared"
    if not password:
        return "skipped: no web ui password available"
    assert_desired_preferences_never_stop_seeding(desired_preferences)
    opener = build_authenticated_opener(base_url, username, password)
    changed_preferences = preferences_needing_change(
        read_preferences(opener, base_url), desired_preferences
    )
    if not changed_preferences:
        return "already matching"
    if dry_run:
        return f"would set {sorted(changed_preferences)}"
    write_preferences(opener, base_url, changed_preferences)
    return f"set {sorted(changed_preferences)}"
