import asyncio
import signal

import cockpit_session_bridge_runtime_test_doubles  # noqa: F401

import server


class FakeEventLoopSignalRegistry:
    def __init__(self):
        self.registered_signal_handlers = {}

    def add_signal_handler(self, signal_number, handler):
        self.registered_signal_handlers[signal_number] = handler


def install_handlers_and_return_registry():
    signal_registry = FakeEventLoopSignalRegistry()
    shutdown_requested = asyncio.get_running_loop().create_future()
    server.install_shutdown_signal_handlers(signal_registry, shutdown_requested)
    return signal_registry, shutdown_requested


def test_shutdown_handlers_cover_terminate_and_interrupt():
    async def install_handlers():
        signal_registry, _ = install_handlers_and_return_registry()
        return sorted(signal_registry.registered_signal_handlers)

    assert asyncio.run(install_handlers()) == sorted([signal.SIGTERM, signal.SIGINT])


def test_a_shutdown_signal_releases_the_serving_loop():
    async def install_then_signal():
        signal_registry, shutdown_requested = install_handlers_and_return_registry()
        signal_registry.registered_signal_handlers[signal.SIGTERM]()
        await asyncio.wait_for(shutdown_requested, 1)

    asyncio.run(install_then_signal())


def test_a_repeated_shutdown_signal_does_not_raise():
    async def install_then_signal_twice():
        signal_registry, shutdown_requested = install_handlers_and_return_registry()
        signal_registry.registered_signal_handlers[signal.SIGTERM]()
        signal_registry.registered_signal_handlers[signal.SIGINT]()
        await asyncio.wait_for(shutdown_requested, 1)

    asyncio.run(install_then_signal_twice())
