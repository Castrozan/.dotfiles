import json
import time
import urllib.error
import urllib.request

SUWAYOMI_REQUEST_TIMEOUT_SECONDS = 30
SUWAYOMI_EXTENSION_FETCH_TIMEOUT_SECONDS = 180
SUWAYOMI_READINESS_ATTEMPTS = 30
SUWAYOMI_READINESS_DELAY_SECONDS = 4

READ_EXTENSION_REPOSITORIES_QUERY = "{ settings { extensionRepos } }"
WRITE_EXTENSION_REPOSITORIES_MUTATION = (
    "mutation($repositoryUrls:[String!]){ "
    "setSettings(input:{settings:{extensionRepos:$repositoryUrls}}){ "
    "settings { extensionRepos } } }"
)
FETCH_EXTENSIONS_MUTATION = (
    "mutation{ fetchExtensions(input:{}){ extensions { pkgName } } }"
)


def first_line_of(message):
    return (message or "").splitlines()[0] if message else "no message"


def execute(graphql_url, query, variables=None, timeout_seconds=None):
    payload = {"query": query}
    if variables is not None:
        payload["variables"] = variables
    request = urllib.request.Request(
        graphql_url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(
        request, timeout=timeout_seconds or SUWAYOMI_REQUEST_TIMEOUT_SECONDS
    ) as response:
        result = json.loads(response.read().decode())
    if result.get("errors"):
        raise ValueError(
            "Suwayomi refused the request: "
            f"{first_line_of(result['errors'][0].get('message'))}"
        )
    return result["data"]


def wait_until_ready(graphql_url):
    for remaining_attempt in range(SUWAYOMI_READINESS_ATTEMPTS, 0, -1):
        try:
            execute(graphql_url, READ_EXTENSION_REPOSITORIES_QUERY)
            return True
        except (urllib.error.URLError, OSError, ValueError):
            if remaining_attempt == 1:
                return False
            time.sleep(SUWAYOMI_READINESS_DELAY_SECONDS)
    return False


def read_extension_repository_urls(graphql_url):
    return execute(graphql_url, READ_EXTENSION_REPOSITORIES_QUERY)["settings"][
        "extensionRepos"
    ]


def write_extension_repository_urls(graphql_url, repository_urls):
    return execute(
        graphql_url,
        WRITE_EXTENSION_REPOSITORIES_MUTATION,
        {"repositoryUrls": list(repository_urls)},
    )["setSettings"]["settings"]["extensionRepos"]


def count_extensions_offered(graphql_url):
    try:
        return len(
            execute(
                graphql_url,
                FETCH_EXTENSIONS_MUTATION,
                timeout_seconds=SUWAYOMI_EXTENSION_FETCH_TIMEOUT_SECONDS,
            )["fetchExtensions"]["extensions"]
        )
    except (ValueError, urllib.error.URLError, OSError):
        return None
