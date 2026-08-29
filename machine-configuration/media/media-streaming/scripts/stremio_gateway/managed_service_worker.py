from pathlib import Path


MANAGED_SERVICE_WORKER_SOURCE = Path(__file__).with_suffix(".js").read_bytes()


def render_managed_service_worker() -> bytes:
    return MANAGED_SERVICE_WORKER_SOURCE
