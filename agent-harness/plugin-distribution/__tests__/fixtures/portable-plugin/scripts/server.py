import json
import os
import sys
from pathlib import Path


def respond(request):
    method = request.get("method")
    if method == "initialize":
        directory = Path(__file__).resolve().parents[1]
        if (
            Path.cwd().resolve() != directory
            or Path(os.environ.get("PLUGIN_ROOT", "")).resolve() != directory
        ):
            raise RuntimeError("Plugin runtime paths were not projected")
        return {
            "protocolVersion": request["params"]["protocolVersion"],
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "distribution-probe", "version": "1.0.0"},
        }
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "distribution_echo",
                    "description": "Return the supplied distribution token.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"token": {"type": "string"}},
                        "required": ["token"],
                    },
                }
            ]
        }
    if method == "tools/call":
        token = request["params"]["arguments"]["token"]
        prefix = os.environ.get("DISTRIBUTION_PROBE_PREFIX", "")
        return {"content": [{"type": "text", "text": prefix + token}]}
    return {}


for line in sys.stdin:
    request = json.loads(line)
    if "id" in request:
        print(
            json.dumps(
                {"jsonrpc": "2.0", "id": request["id"], "result": respond(request)}
            ),
            flush=True,
        )
