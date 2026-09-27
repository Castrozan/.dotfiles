import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ModelHandler(BaseHTTPRequestHandler):
    def log_message(self, *_arguments):
        pass

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append(request)
        messages = request.get("messages", [])
        user_index = next(
            (
                index
                for index in range(len(messages) - 1, -1, -1)
                if messages[index].get("role") == "user"
            ),
            None,
        )
        action = None
        if user_index is not None and not any(
            item.get("role") in {"assistant", "tool"}
            for item in messages[user_index + 1 :]
        ):
            content = messages[user_index].get("content", "")
            if isinstance(content, list):
                content = "".join(item.get("text", "") for item in content)
            try:
                action, _ = json.JSONDecoder().raw_decode(content)
            except (ValueError, TypeError):
                pass
        if isinstance(action, dict) and "tool" in action:
            delta = {
                "role": "assistant",
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "call_acceptance",
                        "type": "function",
                        "function": {
                            "name": action["tool"],
                            "arguments": json.dumps(action["input"]),
                        },
                    }
                ],
            }
            finish = "tool_calls"
        else:
            delta = {"role": "assistant", "content": "Acceptance complete."}
            finish = "stop"
        if "Do not include the <template> tags" in json.dumps(messages):
            delta = {
                "role": "assistant",
                "content": "## Objective\nVerify native compaction.\n\n## Work State\n### Completed\nAcceptance complete.",
            }
            finish = "stop"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for change, reason in [(delta, None), ({}, finish)]:
            chunk = {
                "id": "chatcmpl-acceptance",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "fixture",
                "choices": [{"index": 0, "delta": change, "finish_reason": reason}],
            }
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


@contextmanager
def native_model_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), ModelHandler)
    server.requests = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
