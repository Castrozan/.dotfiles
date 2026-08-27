from dataclasses import dataclass

import runtime_configuration
import suwayomi_graphql_client


@dataclass(frozen=True)
class RepositoryServer:
    name: str
    url: str
    client: object
    repository_file_variable: str
    reports_extension_count: bool = True


def suwayomi_server():
    return RepositoryServer(
        name="Suwayomi",
        url=runtime_configuration.graphql_url(),
        client=suwayomi_graphql_client,
        repository_file_variable=runtime_configuration.DECLARED_REPOSITORY_LIST_FILE_VARIABLE,
    )


def synchronize_extension_repositories(server=None):
    repository_server = server or suwayomi_server()
    declared_repository_urls = runtime_configuration.declared_repository_urls(
        repository_server.repository_file_variable
    )
    if declared_repository_urls is None:
        return {
            "repositories": None,
            "rewritten": False,
            "extensions_offered": None,
        }
    if not repository_server.client.wait_until_ready(repository_server.url):
        raise ValueError(
            f"{repository_server.name} at {repository_server.url} never became reachable; "
            "its extension repositories were left as they already are"
        )
    current_repository_urls = repository_server.client.read_extension_repository_urls(
        repository_server.url
    )
    if current_repository_urls == declared_repository_urls:
        return {
            "repositories": current_repository_urls,
            "rewritten": False,
            "extensions_offered": None,
        }
    written_repository_urls = repository_server.client.write_extension_repository_urls(
        repository_server.url, declared_repository_urls
    )
    if written_repository_urls != declared_repository_urls:
        raise ValueError(
            f"{repository_server.name} accepted the settings write but reports a list "
            "that is not the declared repository list"
        )
    extensions_offered = (
        repository_server.client.count_extensions_offered(repository_server.url)
        if repository_server.reports_extension_count
        else None
    )
    return {
        "repositories": written_repository_urls,
        "rewritten": True,
        "extensions_offered": extensions_offered,
    }
