import importlib
import json
import sys
import urllib.error
from pathlib import Path

PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "suwayomi_extension_repositories"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))

miwayomi_rest_client = importlib.import_module("miwayomi_rest_client")
extension_repository_synchronization = importlib.import_module(
    "extension_repository_synchronization"
)

DECLARED_URLS = [
    "https://declared-one.invalid/index.json",
    "https://declared-two.invalid/index.json",
]


class JsonResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception, _traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_reads_the_persisted_repository_list(monkeypatch):
    requests = []

    def respond(request, timeout):
        requests.append((request, timeout))
        return JsonResponse({"repos": ["https://declared.invalid/index.json"]})

    monkeypatch.setattr(miwayomi_rest_client.urllib.request, "urlopen", respond)

    repositories = miwayomi_rest_client.read_extension_repository_urls(
        "http://miwayomi:4567"
    )

    assert repositories == ["https://declared.invalid/index.json"]
    assert requests[0][0].full_url.endswith("/api/v1/extensions/repos")
    assert requests[0][0].method == "GET"
    assert requests[0][1] == miwayomi_rest_client.MIWAYOMI_REQUEST_TIMEOUT_SECONDS


def test_writes_then_echoes_the_repository_list(monkeypatch):
    calls = []

    def execute(base_url, path, method="GET", payload=None, timeout_seconds=None):
        calls.append((base_url, path, method, payload, timeout_seconds))
        if method == "POST":
            return {"ok": True}
        return {"repos": list(payload_urls)}

    payload_urls = ["https://declared.invalid/index.json"]
    monkeypatch.setattr(miwayomi_rest_client, "execute", execute)

    written = miwayomi_rest_client.write_extension_repository_urls(
        "http://miwayomi:4567", payload_urls
    )

    assert written == payload_urls
    assert calls[0][2] == "POST"
    assert calls[0][3] == {"repos": payload_urls}
    assert calls[1][2] == "GET"


def test_readiness_retries_a_bounded_number_of_times(monkeypatch):
    attempts = []

    def execute(*_arguments, **_keywords):
        attempts.append(None)
        raise urllib.error.URLError("not ready")

    monkeypatch.setattr(miwayomi_rest_client, "execute", execute)
    monkeypatch.setattr(miwayomi_rest_client.time, "sleep", lambda _seconds: None)

    assert miwayomi_rest_client.wait_until_ready("http://miwayomi:4567") is False
    assert len(attempts) == miwayomi_rest_client.MIWAYOMI_READINESS_ATTEMPTS


def test_reads_installed_extensions(monkeypatch):
    calls = []

    def execute(base_url, path, method="GET", payload=None, timeout_seconds=None):
        calls.append((base_url, path, method, payload, timeout_seconds))
        return {"extensions": [{"pkg": "example.package", "version": "2.0"}]}

    monkeypatch.setattr(miwayomi_rest_client, "execute", execute)

    installed_extensions = miwayomi_rest_client.read_installed_extensions(
        "http://miwayomi:4567"
    )

    assert installed_extensions == [{"pkg": "example.package", "version": "2.0"}]
    assert calls[0][1] == "/api/v1/extensions/installed"


def test_uninstalls_extensions_through_supported_api(monkeypatch):
    calls = []

    def execute(base_url, path, method="GET", payload=None, timeout_seconds=None):
        calls.append((base_url, path, method, payload, timeout_seconds))
        return {"ok": True}

    monkeypatch.setattr(miwayomi_rest_client, "execute", execute)

    miwayomi_rest_client.uninstall_extension("http://miwayomi:4567", "obsolete.package")

    assert calls[0][1] == "/api/v1/extensions/uninstall"
    assert calls[0][2] == "POST"
    assert calls[0][3] == {"pkg": "obsolete.package"}


def test_reuses_the_shared_echo_back_reconciliation(monkeypatch, tmp_path):
    list_file_path = tmp_path / "miwayomi-extension-repositories"
    list_file_path.write_text(json.dumps(DECLARED_URLS))
    monkeypatch.setenv("MIWAYOMI_EXTENSION_REPOSITORIES_FILE", str(list_file_path))
    monkeypatch.setattr(miwayomi_rest_client, "wait_until_ready", lambda _url: True)
    monkeypatch.setattr(
        miwayomi_rest_client,
        "read_extension_repository_urls",
        lambda _url: ["https://obsolete.invalid/index.json"],
    )
    monkeypatch.setattr(
        miwayomi_rest_client,
        "write_extension_repository_urls",
        lambda _url, repository_urls: list(repository_urls),
    )
    monkeypatch.setattr(
        miwayomi_rest_client,
        "count_extensions_offered",
        lambda _url: (_ for _ in ()).throw(
            AssertionError("Miwayomi does not expose a combined extension count")
        ),
    )
    server = extension_repository_synchronization.RepositoryServer(
        name="Miwayomi",
        url="http://miwayomi:4567",
        client=miwayomi_rest_client,
        repository_file_variable="MIWAYOMI_EXTENSION_REPOSITORIES_FILE",
        reports_extension_count=False,
    )

    result = extension_repository_synchronization.synchronize_extension_repositories(
        server
    )

    assert result["repositories"] == DECLARED_URLS
    assert result["rewritten"] is True
