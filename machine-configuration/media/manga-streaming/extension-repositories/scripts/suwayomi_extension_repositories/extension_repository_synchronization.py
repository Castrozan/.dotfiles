import runtime_configuration
import suwayomi_graphql_client


def synchronize_extension_repositories():
    graphql_url = runtime_configuration.graphql_url()
    declared_repository_urls = runtime_configuration.declared_repository_urls()
    if declared_repository_urls is None:
        return {
            "repositories": None,
            "rewritten": False,
            "extensions_offered": None,
        }
    if not suwayomi_graphql_client.wait_until_ready(graphql_url):
        raise ValueError(
            f"Suwayomi at {graphql_url} never became reachable; its extension "
            "repositories were left as they already are"
        )
    current_repository_urls = suwayomi_graphql_client.read_extension_repository_urls(
        graphql_url
    )
    if current_repository_urls == declared_repository_urls:
        return {
            "repositories": current_repository_urls,
            "rewritten": False,
            "extensions_offered": None,
        }
    written_repository_urls = suwayomi_graphql_client.write_extension_repository_urls(
        graphql_url, declared_repository_urls
    )
    if written_repository_urls != declared_repository_urls:
        raise ValueError(
            "Suwayomi accepted the settings write but reports "
            f"{written_repository_urls}, not the declared {declared_repository_urls}"
        )
    return {
        "repositories": written_repository_urls,
        "rewritten": True,
        "extensions_offered": suwayomi_graphql_client.count_extensions_offered(
            graphql_url
        ),
    }
