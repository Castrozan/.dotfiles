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
        selected_indexer = _build_audiobook_indexer(indexer)
        if selected_indexer is None:
            continue
        selected.append(selected_indexer)
    if not selected:
        raise RuntimeError(
            f"No enabled torrent indexers advertise audiobook category {AUDIOBOOK_CATEGORY_ID}"
        )
    return selected


def _build_audiobook_indexer(indexer):
    categories = indexer.get("capabilities", {}).get("categories", [])
    if not indexer.get("enable") or indexer.get("protocol") != "torrent":
        return None
    if not has_audiobooks(categories):
        return None
    return {
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
