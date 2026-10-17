from urllib.parse import urlparse

from shorts_browser_pages.arguments import positional_tab_arguments, tab_arguments

POSITIONAL_BROWSER_COMMANDS = frozenset({"tab"})


def owned_arguments(pages, state, arguments):
    remaining, identifier = tab_arguments(arguments)
    if identifier is not None:
        pages.require_owned(state, identifier)
    if arguments[0] in POSITIONAL_BROWSER_COMMANDS:
        return scoped_positional(pages, state, remaining, identifier)
    if arguments[0] == "open":
        return scoped_navigation(pages, state, remaining, identifier)
    return scoped_action(pages, state, remaining, identifier)


def scoped_positional(pages, state, arguments, identifier):
    positional = positional_tab_arguments(arguments)
    identifier = pages.require_owned(
        state, positional.identifier or identifier or state["current"]
    )
    if positional.command == ["tab", "select"]:
        pages.select_page(state, identifier)
    return [*positional.command, identifier, *positional.options]


def scoped_navigation(pages, state, arguments, identifier):
    validate_navigation(arguments)
    remaining = arguments
    identifier = identifier or pages.navigation_page(
        state, navigation_role(remaining[1])
    )
    return scoped_action(pages, state, remaining, identifier)


def validate_navigation(arguments):
    if len(arguments) < 2 or arguments[1].startswith("-"):
        raise ValueError("Use open URL to navigate a run-owned page")


def navigation_role(url):
    return "publisher" if urlparse(url).hostname == "studio.youtube.com" else "research"


def scoped_action(pages, state, arguments, identifier):
    identifier = identifier or state["current"]
    if identifier is None:
        raise ValueError("Navigate before using a run-owned browser tab")
    pages.require_owned(state, identifier)
    pages.select_page(state, identifier)
    position = arguments.index("--") if "--" in arguments else len(arguments)
    return [*arguments[:position], "--tab", identifier, *arguments[position:]]
