from types import SimpleNamespace
import sys


def test_cli_broker_is_not_reaped_as_an_orphaned_stdio_server(watchdog_module):
    broker = SimpleNamespace(
        info={
            "pid": 10,
            "name": "node",
            "cmdline": [
                "node",
                "/nix/store/package-chrome-devtools-mcp/build/src/daemon/daemon.js",
            ],
        }
    )
    worker = SimpleNamespace(
        info={
            "pid": 11,
            "name": "node",
            "cmdline": [
                "node",
                "/nix/store/package-chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js",
            ],
        }
    )
    sys.modules["psutil"].process_iter = lambda attributes: iter([broker, worker])
    assert watchdog_module.find_chrome_devtools_mcp_processes() == [worker]
