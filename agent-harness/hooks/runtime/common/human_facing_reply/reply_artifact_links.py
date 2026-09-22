from urllib.parse import urlsplit


def artifact_destination(destination, required_pattern):
    try:
        parsed = urlsplit(destination.rstrip(".,;:!?)]}"))
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            return None
        if parsed.port is not None and not 0 < parsed.port < 65536:
            return None
    except ValueError:
        return None
    match = required_pattern.search(parsed.path)
    if match is None:
        return None
    return match["kind"].casefold(), match["number"].lstrip("0") or "0"


def artifact_destinations_in_reply(inline_blocks, patterns):
    destinations = set()
    for block in inline_blocks:
        links = block.destinations + [
            match[0] for match in patterns["url_pattern"].finditer(block.outside_code)
        ]
        destinations.update(
            artifact
            for link in links
            if (artifact := artifact_destination(link, patterns["required_pattern"]))
        )
    return destinations


def artifact_reference_is_linked(reference, kind_paths, destinations):
    kind = reference["generic_kind"] or reference["numbered_kind"]
    expected_kind = kind_paths.get(kind.casefold())
    number = reference["number"]
    if number is not None:
        return (expected_kind, number.lstrip("0") or "0") in destinations
    return any(kind == expected_kind for kind, _ in destinations)


def reply_has_unlinked_artifacts(reply):
    configuration = reply.configuration
    restriction = configuration.restrictions["unlinked_artifact"]
    patterns = configuration.restriction_patterns["unlinked_artifact"]
    destinations = artifact_destinations_in_reply(reply.inline_blocks, patterns)
    return any(
        not artifact_reference_is_linked(
            reference, restriction["kind_paths"], destinations
        )
        for block in reply.inline_blocks
        for reference in patterns["pattern"].finditer(block.outside_code)
    )
