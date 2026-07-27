import jellyfin_api_client
import jellyfin_library_declaration


def create_missing_declared_libraries(base_url, api_key):
    existing_library_names = {
        library.get("Name")
        for library in jellyfin_api_client.list_virtual_folders(base_url, api_key)
    }
    created_library_names = []
    for declaration in jellyfin_library_declaration.ALL_LIBRARY_DECLARATIONS:
        if declaration["name"] in existing_library_names:
            continue
        jellyfin_api_client.create_virtual_folder(
            base_url,
            api_key,
            declaration["name"],
            declaration["collection_type"],
            declaration["container_path"],
        )
        created_library_names.append(declaration["name"])
    return created_library_names
