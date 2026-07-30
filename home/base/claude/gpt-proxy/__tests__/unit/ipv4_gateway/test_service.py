import importlib.util
import threading
from pathlib import Path

import pytest

GATEWAY_PATH = (
    Path(__file__).resolve().parents[3] / "scripts" / "cli_proxy_api_ipv4_gateway.py"
)
GPT_PROXY_NIX_MODULE_PATH = Path(__file__).resolve().parents[3] / "default.nix"
GATEWAY_SPECIFICATION = importlib.util.spec_from_file_location(
    "cli_proxy_api_ipv4_gateway_service", GATEWAY_PATH
)
assert GATEWAY_SPECIFICATION
assert GATEWAY_SPECIFICATION.loader
GATEWAY_MODULE = importlib.util.module_from_spec(GATEWAY_SPECIFICATION)
GATEWAY_SPECIFICATION.loader.exec_module(GATEWAY_MODULE)


class ControlledGatewayServer:
    def __init__(self, server_address, request_handler):
        self.started = threading.Event()
        self.stopped = threading.Event()
        self.shutdown_called = False

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        return False

    def serve_forever(self):
        self.started.set()
        self.stopped.wait()

    def shutdown(self):
        self.shutdown_called = True
        self.stopped.set()


class ControlledProcess:
    def __init__(self, exit_code):
        self.exit_code = exit_code

    def wait(self):
        return self.exit_code


def test_entrypoint_starts_the_gateway_and_propagates_the_proxy_exit_code():
    controlled_server = None

    def create_server(server_address, request_handler):
        nonlocal controlled_server
        controlled_server = ControlledGatewayServer(server_address, request_handler)
        return controlled_server

    def create_process(program_arguments):
        assert controlled_server
        assert controlled_server.started.wait(timeout=1)
        return ControlledProcess(37)

    exit_code = GATEWAY_MODULE.run_cli_proxy_api_with_ipv4_gateway(
        "127.0.0.1",
        8318,
        ["cli-proxy-api", "--local-model"],
        server_factory=create_server,
        process_factory=create_process,
    )

    assert exit_code == 37
    assert controlled_server
    assert controlled_server.shutdown_called


def test_entrypoint_stops_the_gateway_when_the_proxy_cannot_start():
    controlled_server = None

    def create_server(server_address, request_handler):
        nonlocal controlled_server
        controlled_server = ControlledGatewayServer(server_address, request_handler)
        return controlled_server

    def fail_to_create_process(program_arguments):
        assert controlled_server
        assert controlled_server.started.wait(timeout=1)
        raise OSError("proxy executable is unavailable")

    with pytest.raises(OSError, match="proxy executable is unavailable"):
        GATEWAY_MODULE.run_cli_proxy_api_with_ipv4_gateway(
            "127.0.0.1",
            8318,
            ["cli-proxy-api", "--local-model"],
            server_factory=create_server,
            process_factory=fail_to_create_process,
        )

    assert controlled_server
    assert controlled_server.shutdown_called


def test_nix_module_routes_service_and_login_through_ipv4_gateways():
    module_source = GPT_PROXY_NIX_MODULE_PATH.read_text()

    assert (
        'proxy-url: "http://${proxyIpv4GatewayListenAddress}:'
        '${toString ipv4GatewayPort}"'
    ) in module_source
    assert "ipv4GatewayCliProxyApiProgramArguments" in module_source
    assert "proxyIpv4GatewayLoginPort = 8319;" in module_source
    assert "--config ${cliProxyApiLoginConfigFile} --codex-login" in module_source
