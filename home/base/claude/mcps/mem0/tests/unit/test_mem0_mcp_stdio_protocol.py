from mem0_mcp_stdio_protocol import (
    MCP_PROTOCOL_VERSION,
    ModelContextProtocolStdioServer,
)


def build_server(tool_handlers=None):
    tool_definitions = [
        {"name": "add_memory", "description": "x", "inputSchema": {"type": "object"}}
    ]
    handlers = tool_handlers or {"add_memory": lambda arguments: "stored"}
    return ModelContextProtocolStdioServer("mem0", "1.0.0", tool_definitions, handlers)


def test_initialize_reports_protocol_and_server_info():
    server = build_server()
    response = server.handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert response["id"] == 1
    assert response["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION
    assert response["result"]["serverInfo"]["name"] == "mem0"
    assert "tools" in response["result"]["capabilities"]


def test_initialized_notification_produces_no_response():
    server = build_server()
    assert (
        server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
        is None
    )


def test_tools_list_returns_registered_definitions():
    server = build_server()
    response = server.handle_request(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )
    tool_names = [tool["name"] for tool in response["result"]["tools"]]
    assert tool_names == ["add_memory"]


def test_tools_call_invokes_handler_and_wraps_text_content():
    captured_arguments = {}

    def handler(arguments):
        captured_arguments.update(arguments)
        return "remembered it"

    server = build_server({"add_memory": handler})
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "add_memory", "arguments": {"text": "hi"}},
        }
    )
    assert captured_arguments == {"text": "hi"}
    assert response["result"]["isError"] is False
    assert response["result"]["content"][0]["text"] == "remembered it"


def test_tools_call_handler_exception_becomes_is_error_content():
    def failing_handler(arguments):
        raise RuntimeError("boom")

    server = build_server({"add_memory": failing_handler})
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "add_memory", "arguments": {}},
        }
    )
    assert response["result"]["isError"] is True
    assert "boom" in response["result"]["content"][0]["text"]


def test_tools_call_unknown_tool_returns_error():
    server = build_server()
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "nope", "arguments": {}},
        }
    )
    assert response["error"]["code"] == -32602


def test_unknown_method_with_id_returns_method_not_found():
    server = build_server()
    response = server.handle_request(
        {"jsonrpc": "2.0", "id": 6, "method": "does/not/exist"}
    )
    assert response["error"]["code"] == -32601


def test_malformed_json_returns_parse_error():
    server = build_server()
    response = server.handle_raw_message("{not json")
    assert response["error"]["code"] == -32700
