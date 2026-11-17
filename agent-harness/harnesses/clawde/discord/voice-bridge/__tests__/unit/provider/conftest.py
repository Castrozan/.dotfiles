import pytest

from fake_bridge import FakeBridge


@pytest.fixture
def bridge_factory():
    bridges = []

    def make(**options):
        bridges.append(FakeBridge(**options))
        return bridges[-1]

    yield make
    for bridge in bridges:
        bridge.close()
