import argparse
import hashlib
import ipaddress
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

REQUEST_TIMEOUT_SECONDS = 10
MAXIMUM_RESPONSE_BYTES = 16384
SHORT_URL_PATTERN = re.compile(r"https://tinyurl\.com/[A-Za-z0-9_-]{4,64}")
SENSITIVE_QUERY_MARKERS = (
    "token",
    "secret",
    "password",
    "signature",
    "credential",
    "authorization",
    "apikey",
    "accesskey",
)


def require_public_destination(destination):
    if len(destination) > 8192 or any(
        character.isspace() or ord(character) < 32 for character in destination
    ):
        raise ValueError("Expected one complete public URL")
    parsed = urlsplit(destination)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or (parsed.port is not None and not 0 < parsed.port < 65536)
    ):
        raise ValueError("Expected a public HTTP or HTTPS URL without credentials")
    require_public_hostname(parsed.hostname)
    for name, _ in parse_qsl(parsed.query) + parse_qsl(parsed.fragment):
        normalized_name = re.sub(r"[^a-z0-9]", "", name.casefold())
        if any(marker in normalized_name for marker in SENSITIVE_QUERY_MARKERS):
            raise ValueError("Keep URLs containing credentials or signatures direct")


def require_public_hostname(hostname):
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        if "." not in hostname or hostname.rstrip(".").endswith(
            (".localhost", ".local", ".internal", ".home", ".lan", ".test", ".invalid")
        ):
            raise ValueError("Keep local and internal URLs direct")
        return
    if not address.is_global:
        raise ValueError("Keep nonpublic IP addresses direct")


def create_tinyurl(destination):
    request = Request(
        "https://tinyurl.com/api-create.php?" + urlencode({"url": destination}),
        headers={"User-Agent": "dotfiles-url-shortener"},
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        body = response.read(MAXIMUM_RESPONSE_BYTES + 1)
    if len(body) > MAXIMUM_RESPONSE_BYTES:
        raise ValueError("Shortener response exceeded its size limit")
    return require_short_url(body.decode("utf-8").strip())


class ShortenerRedirectVerifier(HTTPRedirectHandler):
    def redirect_request(
        self, request, response, status, message, headers, destination
    ):
        return None


def verify_short_url(short_url, destination):
    request = Request(short_url, method="HEAD")
    opener = build_opener(ShortenerRedirectVerifier())
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS):
            raise ValueError("Short URL did not redirect")
    except HTTPError as response:
        try:
            if response.code not in (301, 302, 303, 307, 308):
                raise ValueError("Short URL verification failed") from response
            if response.headers.get("Location") != destination:
                raise ValueError("Short URL does not preserve the exact destination")
        finally:
            response.close()


def cached_short_url_path(destination):
    cache_directory = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    destination_digest = hashlib.sha256(destination.encode("utf-8")).hexdigest()
    return cache_directory / "dotfiles-url-shortener" / destination_digest


def require_short_url(value):
    if not isinstance(value, str) or not SHORT_URL_PATTERN.fullmatch(value):
        raise ValueError("Shortener returned an invalid short URL")
    return value


def shorten_url(destination):
    require_public_destination(destination)
    cache_path = cached_short_url_path(destination)
    try:
        return require_short_url(cache_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        pass
    short_url = create_tinyurl(destination)
    verify_short_url(short_url, destination)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(short_url + "\n", encoding="utf-8")
    return short_url


def main(arguments=None):
    parser = argparse.ArgumentParser(
        description="Shorten a public URL with TinyURL, verify its exact destination, and cache the result."
    )
    parser.add_argument("url", help="Public HTTP or HTTPS URL without credentials")
    options = parser.parse_args(arguments)
    try:
        print(shorten_url(options.url))
    except (OSError, ValueError) as error:
        print(f"Could not shorten URL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
