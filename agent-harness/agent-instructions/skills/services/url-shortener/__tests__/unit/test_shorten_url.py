import importlib.util
import io
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "shorten_url.py"
SPECIFICATION = importlib.util.spec_from_file_location("shorten_url", SCRIPT)
shortener = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(shortener)

DESTINATION = "https://example.com/reference?branch=main&topic=keyboard%20links#usage"
SHORT_URL = "https://tinyurl.com/abc12345"


@pytest.fixture
def requests(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    calls = []

    def respond(request, timeout):
        assert timeout == shortener.REQUEST_TIMEOUT_SECONDS
        parameters = parse_qs(urlsplit(request.full_url).query)
        calls.append((request.get_method(), parameters))
        return io.BytesIO(SHORT_URL.encode("utf-8"))

    class VerificationOpener:
        def open(self, request, timeout):
            assert request.full_url == SHORT_URL
            assert request.get_method() == "HEAD"
            assert timeout == shortener.REQUEST_TIMEOUT_SECONDS
            calls.append(("HEAD", request.full_url))
            raise HTTPError(
                SHORT_URL, 301, "Moved", {"Location": DESTINATION}, io.BytesIO()
            )

    def verification_opener(handler):
        assert (
            handler.redirect_request(None, None, 301, "Moved", {}, DESTINATION) is None
        )
        return VerificationOpener()

    monkeypatch.setattr(shortener, "urlopen", respond)
    monkeypatch.setattr(shortener, "build_opener", verification_opener)
    return calls


def test_shortens_encoded_destination_verifies_it_and_reuses_cache(requests):
    assert shortener.shorten_url(DESTINATION) == SHORT_URL
    assert shortener.shorten_url(DESTINATION) == SHORT_URL
    assert requests == [
        ("GET", {"url": [DESTINATION]}),
        ("HEAD", SHORT_URL),
    ]


@pytest.mark.parametrize(
    "destination",
    [
        "file:///tmp/report",
        "https://",
        "https://localhost/report",
        "https://host.internal/report",
        "http://127.0.0.1/report",
        "http://192.168.0.1/report",
        "http://[::1]/report",
        "https://engineer:password@example.com/report",
        "https://example.com/report?access_token=secret",
        "https://example.com/report?X-Amz-Signature=secret",
        "https://example.com/report#id_token=secret",
        "https://example.com:99999/report",
        "https://example.com/report\nextra",
    ],
)
def test_nonpublic_or_credential_urls_are_rejected_without_network(
    requests, destination
):
    with pytest.raises(ValueError):
        shortener.shorten_url(destination)

    assert requests == []


def test_mismatched_destination_never_returns_or_caches_short_url(
    requests, monkeypatch
):
    class VerificationOpener:
        def open(self, request, timeout):
            raise HTTPError(
                SHORT_URL,
                301,
                "Moved",
                {"Location": "https://example.com/other"},
                io.BytesIO(),
            )

    monkeypatch.setattr(shortener, "build_opener", lambda handler: VerificationOpener())

    with pytest.raises(ValueError, match="exact destination"):
        shortener.shorten_url(DESTINATION)

    assert not shortener.cached_short_url_path(DESTINATION).exists()


@pytest.mark.parametrize(
    "body",
    [
        b"Error: service unavailable",
        b"https://other.example/link",
        b"x" * (shortener.MAXIMUM_RESPONSE_BYTES + 1),
    ],
)
def test_service_failures_do_not_emit_a_short_link(requests, monkeypatch, capsys, body):
    monkeypatch.setattr(shortener, "urlopen", lambda request, timeout: io.BytesIO(body))

    assert shortener.main([DESTINATION]) == 1
    assert capsys.readouterr().out == ""


def test_network_timeout_does_not_emit_a_short_link(requests, monkeypatch, capsys):
    def timeout(request, timeout):
        raise TimeoutError("service unavailable")

    monkeypatch.setattr(shortener, "urlopen", timeout)

    assert shortener.main([DESTINATION]) == 1
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("status", (200, 404, 503))
def test_unverified_responses_never_cache_or_emit_links(
    requests, monkeypatch, capsys, status
):
    class VerificationOpener:
        def open(self, request, timeout):
            if status == 200:
                return io.BytesIO()
            raise HTTPError(SHORT_URL, status, "Failed", {}, io.BytesIO())

    monkeypatch.setattr(shortener, "build_opener", lambda handler: VerificationOpener())

    assert shortener.main([DESTINATION]) == 1
    assert capsys.readouterr().out == ""
    assert not shortener.cached_short_url_path(DESTINATION).exists()
