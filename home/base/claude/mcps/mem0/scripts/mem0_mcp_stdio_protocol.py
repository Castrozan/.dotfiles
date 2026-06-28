import json
import sys

MCP_PROTOCOL_VERSION = "2024-11-05"


class ModelContextProtocolStdioServer:
    def __init__(self, server_name, server_version, tool_definitions, tool_handlers):
        self.server_name = server_name
        self.server_version = server_version
        self.tool_definitions = tool_definitions
        self.tool_handlers = tool_handlers

    def serve_forever(self, input_stream=None, output_stream=None):
        input_stream = input_stream if input_stream is not None else sys.stdin
        output_stream = output_stream if output_stream is not None else sys.stdout
        for raw_line in input_stream:
            stripped_line = raw_line.strip()
            if not stripped_line:
                continue
            response = self.handle_raw_message(stripped_line)
            if response is not None:
                output_stream.write(json.dumps(response) + "\n")
                output_stream.flush()

    def handle_raw_message(self, raw_line):
        try:
            request = json.loads(raw_line)
        except json.JSONDecodeError:
            return self._error_response(None, -32700, "Parse error")
        return self.handle_request(request)

    def handle_request(self, request):
        method = request.get("method")
        request_id = request.get("id")
        is_notification = "id" not in request

        if method == "initialize":
            return self._success_response(request_id, self._initialize_result())
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return self._success_response(request_id, {})
        if method == "tools/list":
            return self._success_response(request_id, {"tools": self.tool_definitions})
        if method == "tools/call":
            return self._handle_tools_call(request_id, request.get("params", {}))

        if is_notification:
            return None
        return self._error_response(request_id, -32601, f"Method not found: {method}")

    def _handle_tools_call(self, request_id, params):
        tool_name = params.get("name")
        arguments = params.get("arguments", {}) or {}
        handler = self.tool_handlers.get(tool_name)
        if handler is None:
            return self._error_response(
                request_id, -32602, f"Unknown tool: {tool_name}"
            )
        try:
            text_result = handler(arguments)
        except Exception as handler_error:
            return self._success_response(
                request_id,
                {
                    "content": [{"type": "text", "text": f"Error: {handler_error}"}],
                    "isError": True,
                },
            )
        return self._success_response(
            request_id,
            {"content": [{"type": "text", "text": text_result}], "isError": False},
        )

    def _initialize_result(self):
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": self.server_name, "version": self.server_version},
        }

    def _success_response(self, request_id, result):
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _error_response(self, request_id, code, message):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }
