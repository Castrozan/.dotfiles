import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path


def owned_processes():
    if sys.platform == "darwin":
        return darwin_owned_processes()
    found = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            arguments = (path / "cmdline").read_bytes().split(bytes([0]))
            name = Path(arguments[0].decode()).name
            browser = name in ("chrome", "chromium", ".chromium-wrapped") and any(
                value.startswith(b"--user-data-dir=") and b"/opencli/profiles/" in value
                for value in arguments
            )
            daemon = name == "node" and any(
                b"/opencli/node_modules/@jackwener/opencli/dist/src/daemon.js" in value
                for value in arguments
            )
            if browser or daemon:
                found.append(int(path.name))
        except (OSError, UnicodeDecodeError, IndexError):
            pass
    return found


def darwin_owned_processes():
    result = subprocess.run(
        ["/bin/ps", "-axww", "-o", "pid=,command="],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    found = []
    for line in result.stdout.splitlines():
        identifier, _, arguments = line.strip().partition(" ")
        browser = "--user-data-dir=" in arguments and "/opencli/profiles/" in arguments
        daemon = (
            "/opencli/node_modules/@jackwener/opencli/dist/src/daemon.js" in arguments
        )
        if identifier.isdigit() and (browser or daemon):
            found.append(int(identifier))
    return found


def clean():
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if not owned_processes():
            return True
        time.sleep(0.1)
    return False


class Fixture(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        if self.path.startswith("/api/items"):
            self.wfile.write(b'{"items":[1,2,3]}')
        elif self.path == "/app.js":
            self.wfile.write(
                b"document.querySelector('#load').onclick=async()=>{const data=await (await fetch('/api/items')).json();document.querySelector('#result').textContent=document.querySelector('#name').value+': '+data.items.length+' items';};"
            )
        else:
            self.wfile.write(
                b'<html><title>OpenCLI proof</title><main><h1>OpenCLI proof</h1><p>Research workflow fixture.</p><label>Name<input id="name"></label><button id="load">Load items</button><p id="result">Ready</p><input id="upload" type="file"><script src="/app.js"></script></main></html>'
            )

    def log_message(self, *arguments):
        pass
