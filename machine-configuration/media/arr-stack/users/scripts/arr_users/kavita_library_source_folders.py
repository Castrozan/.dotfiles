from pathlib import Path

import runtime_credentials


def resolve_source_library_folders():
    host_root_path = runtime_credentials.kavita_source_root_host_path()
    container_root_path = runtime_credentials.kavita_source_root_container_path()
    if not host_root_path or not container_root_path:
        return []
    host_root = Path(host_root_path)
    if not host_root.is_dir():
        return []
    return [
        f"{container_root_path}/{source_directory_name}"
        for source_directory_name in sorted(
            entry.name for entry in host_root.iterdir() if entry.is_dir()
        )
    ]


def library_already_points_at_sources(library, source_library_folders):
    return sorted(library.get("folders") or []) == sorted(source_library_folders)


def build_library_source_folder_update(library, source_library_folders):
    library_update = dict(library)
    library_update["folders"] = list(source_library_folders)
    library_update["fileGroupTypes"] = library.get("libraryFileTypes") or []
    return library_update
