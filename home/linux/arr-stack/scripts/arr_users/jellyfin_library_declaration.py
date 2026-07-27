PUBLIC_LIBRARY_DECLARATIONS = [
    {
        "name": "Movies",
        "collection_type": "movies",
        "container_path": "/media/movies",
    },
    {
        "name": "TV",
        "collection_type": "tvshows",
        "container_path": "/media/tv",
    },
]

PRIVATE_LIBRARY_DECLARATIONS = [
    {
        "name": "Movies (Private)",
        "collection_type": "movies",
        "container_path": "/media/movies-private",
    },
    {
        "name": "TV (Private)",
        "collection_type": "tvshows",
        "container_path": "/media/tv-private",
    },
]

ALL_LIBRARY_DECLARATIONS = PUBLIC_LIBRARY_DECLARATIONS + PRIVATE_LIBRARY_DECLARATIONS


def public_library_names():
    return [declaration["name"] for declaration in PUBLIC_LIBRARY_DECLARATIONS]


def resolve_public_library_ids(jellyfin_libraries):
    library_id_by_name = {
        library.get("Name"): library.get("ItemId") for library in jellyfin_libraries
    }
    missing_library_names = [
        name for name in public_library_names() if not library_id_by_name.get(name)
    ]
    if missing_library_names:
        raise ValueError(
            "refusing to write a friend policy while these declared public "
            f"libraries are missing from Jellyfin: {', '.join(missing_library_names)}"
        )
    return [library_id_by_name[name] for name in public_library_names()]


def private_library_names_present(jellyfin_libraries):
    declared_public_names = set(public_library_names())
    return [
        library.get("Name")
        for library in jellyfin_libraries
        if library.get("Name") not in declared_public_names
    ]
