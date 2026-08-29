from pathlib import Path


PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "stremio_gateway"
)


def test_managed_service_worker_retires_the_upstream_precache():
    worker_source = (PACKAGE_DIRECTORY_PATH / "managed_service_worker.js").read_text()
    server_source = (PACKAGE_DIRECTORY_PATH / "__main__.py").read_text()

    assert "self.skipWaiting()" in worker_source
    assert "caches.keys()" in worker_source
    assert "self.clients.claim()" in worker_source
    assert 'path == "/service-worker.js"' in server_source
    assert "render_managed_service_worker()" in server_source
