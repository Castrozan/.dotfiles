from urllib.parse import urlsplit

LOOPBACK_HTTP_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def is_forbidden_endpoint_character(character):
    return character == "\\" or ord(character) <= 32 or ord(character) == 127


def parse_ingestion_endpoint(value):
    if any(is_forbidden_endpoint_character(character) for character in value):
        return None
    try:
        return urlsplit(value)
    except ValueError:
        return None


def has_valid_ingestion_authority(endpoint):
    if not endpoint.hostname:
        return False
    try:
        port = endpoint.port
    except ValueError:
        return False
    return port is None or 1 <= port <= 65535


def has_no_ingestion_credentials_or_suffix(endpoint):
    return not any(
        (
            endpoint.username is not None,
            endpoint.password is not None,
            endpoint.query,
            endpoint.fragment,
        )
    )


def has_permitted_ingestion_transport(endpoint):
    if endpoint.scheme == "https":
        return True
    return endpoint.scheme == "http" and endpoint.hostname in LOOPBACK_HTTP_HOSTS


def is_permitted_ingestion_endpoint(value):
    if not isinstance(value, str):
        return False
    endpoint = parse_ingestion_endpoint(value)
    if endpoint is None:
        return False
    return all(
        (
            has_valid_ingestion_authority(endpoint),
            has_no_ingestion_credentials_or_suffix(endpoint),
            has_permitted_ingestion_transport(endpoint),
        )
    )
