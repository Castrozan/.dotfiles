"""Prowlarr indexer selection for the audiobook (Usenet/torrent) category."""

AUDIOBOOK_CATEGORY_ID = 3030


def has_audiobooks(categories):
    return any(
        category.get("id") == AUDIOBOOK_CATEGORY_ID
        or has_audiobooks(category.get("subCategories", []))
        for category in categories
    )


def select_indexers(indexers):
    selected = []
    for indexer in indexers:
        categories = indexer.get("capabilities", {}).get("categories", [])
        if not indexer.get("enable") or indexer.get("protocol") != "torrent":
            continue
        if not has_audiobooks(categories):
            continue
        selected.append(
            {
                "id": indexer["id"],
                "name": indexer["name"],
                "protocol": "torrent",
                "enabled": True,
                "priority": indexer.get("priority", 25),
                "rssEnabled": False,
                "audiobookCategories": [AUDIOBOOK_CATEGORY_ID],
                "ebookCategories": [],
                "seedingTimeMinutes": 0,
                "ratioLimit": 0,
            }
        )
    if not selected:
        raise RuntimeError(
            f"No enabled torrent indexers advertise audiobook category {AUDIOBOOK_CATEGORY_ID}"
        )
    return selected
