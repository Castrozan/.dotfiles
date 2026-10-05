from contextlib import contextmanager
from pathlib import Path
import threading

from websockets.exceptions import ConnectionClosed
from websockets.sync.client import unix_connect
from websockets.sync.server import unix_serve

from profile_write_adapter import CodexProfileWriteAdapter


MAXIMUM_MESSAGE_BYTES = 64 * 1024 * 1024


def relay_server_responses(upstream, downstream, adapter) -> None:
    try:
        for frame in upstream:
            downstream.send(adapter.finish_response(frame))
    except (ConnectionClosed, OSError):
        pass
    finally:
        downstream.close()


def relay_profile_connection(downstream, server_path: Path, profile_path: Path) -> None:
    try:
        upstream = unix_connect(
            str(server_path),
            uri="ws://localhost",
            open_timeout=1.0,
            close_timeout=0.1,
            max_size=MAXIMUM_MESSAGE_BYTES,
            max_queue=1,
            compression=None,
        )
    except OSError:
        downstream.close()
        return
    with upstream:
        adapter = CodexProfileWriteAdapter(profile_path)
        response_thread = threading.Thread(
            target=relay_server_responses,
            args=(upstream, downstream, adapter),
            daemon=True,
        )
        response_thread.start()
        try:
            for frame in downstream:
                upstream.send(adapter.prepare_request(frame))
        except (ConnectionClosed, OSError):
            pass
        finally:
            upstream.close()
            response_thread.join(timeout=0.5)


@contextmanager
def profile_connection_path(server_path: Path, profile_path: Path | None):
    if profile_path is None:
        yield server_path
        return
    client_path = server_path.parent / "client.sock"
    server = unix_serve(
        lambda connection: relay_profile_connection(
            connection, server_path, profile_path
        ),
        str(client_path),
        open_timeout=1.0,
        close_timeout=0.1,
        max_size=MAXIMUM_MESSAGE_BYTES,
        max_queue=1,
        compression=None,
    )
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        yield client_path
    finally:
        server.shutdown()
        server_thread.join(timeout=0.5)
