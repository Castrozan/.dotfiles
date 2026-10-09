import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
import unittest


PROXY_EXECUTABLE = sys.argv[1]
ACTIVATION_PROGRAM = """import os
import sys

descriptor = int(sys.argv[1])
if descriptor != 3:
    os.dup2(descriptor, 3)
    os.close(descriptor)
os.set_inheritable(3, True)
os.environ["LISTEN_PID"] = str(os.getpid())
os.environ["LISTEN_FDS"] = "1"
os.execv(sys.argv[2], sys.argv[2:])
"""


class InferenceConnection(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(3)
        while True:
            try:
                payload = self.request.recv(4096)
            except (TimeoutError, ConnectionError):
                return
            if not payload:
                return
            self.request.sendall(payload)


class SocketProxyLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.backend = socketserver.ThreadingTCPServer(
            ("127.0.0.1", 0), InferenceConnection
        )
        self.backend.daemon_threads = True
        self.backend_thread = threading.Thread(
            target=self.backend.serve_forever,
            kwargs={"poll_interval": 0.05},
            daemon=True,
        )
        self.backend_thread.start()
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(8)
        self.processes = []
        self.clients = []

    def tearDown(self):
        for client in self.clients:
            client.close()
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
            try:
                process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=3)
        self.listener.close()
        self.backend.shutdown()
        self.backend.server_close()
        self.backend_thread.join(timeout=3)

    def start_proxy(self):
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                ACTIVATION_PROGRAM,
                str(self.listener.fileno()),
                PROXY_EXECUTABLE,
                "--exit-idle-time=400ms",
                f"127.0.0.1:{self.backend.server_address[1]}",
            ],
            pass_fds=(self.listener.fileno(),),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "NOTIFY_SOCKET": ""},
        )
        self.processes.append(process)
        return process

    def connect_actor(self):
        client = socket.create_connection(self.listener.getsockname(), timeout=3)
        self.clients.append(client)
        return client

    def assert_idle_exit(self, process):
        output, errors = process.communicate(timeout=3)
        self.assertEqual(process.returncode, 0, (output, errors))

    def test_completed_actor_request_releases_proxy_but_preserves_listener(self):
        actor = self.connect_actor()
        actor.sendall(b"initial demand")
        process = self.start_proxy()
        self.assertEqual(actor.recv(4096), b"initial demand")
        actor.close()

        self.assert_idle_exit(process)
        self.assertEqual(
            self.listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN), 1
        )

    def test_one_actor_leaving_does_not_interrupt_another_idle_connection(self):
        process = self.start_proxy()
        first_actor = self.connect_actor()
        second_actor = self.connect_actor()
        first_actor.sendall(b"first request")
        self.assertEqual(first_actor.recv(4096), b"first request")
        second_actor.sendall(b"second request")
        self.assertEqual(second_actor.recv(4096), b"second request")

        first_actor.close()
        time.sleep(0.6)
        self.assertIsNone(process.poll())
        second_actor.sendall(b"continued stream")
        self.assertEqual(second_actor.recv(4096), b"continued stream")

        second_actor.close()
        self.assert_idle_exit(process)

    def test_next_actor_request_survives_a_new_proxy_after_idle_exit(self):
        first_actor = self.connect_actor()
        first_actor.sendall(b"first demand")
        first_process = self.start_proxy()
        self.assertEqual(first_actor.recv(4096), b"first demand")
        first_actor.close()
        self.assert_idle_exit(first_process)
        actor = self.connect_actor()
        actor.sendall(b"cold request queued on socket")

        second_process = self.start_proxy()
        self.assertEqual(actor.recv(4096), b"cold request queued on socket")

        actor.close()
        self.assert_idle_exit(second_process)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
