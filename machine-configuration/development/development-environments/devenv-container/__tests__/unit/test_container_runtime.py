import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from container_runtime import ContainerRuntime


def runtime():
    policy = SimpleNamespace(
        virtual_machine=True,
        virtual_machine_profile="devenv",
        virtual_machine_cpus=2,
        virtual_machine_memory_gib=4,
    )
    return ContainerRuntime(policy)


@pytest.mark.parametrize("cpus,memory", [(4, 4 * 1024**3), (2, 8 * 1024**3)])
def test_reject_an_existing_virtual_machine_that_exceeds_the_budget(cpus, memory):
    environment = runtime()
    environment.run = Mock(
        return_value=SimpleNamespace(
            stdout=json.dumps({"cpus": cpus, "memory": memory})
        )
    )
    with pytest.raises(ValueError, match="exceeds"):
        environment.verify_machine_budget()


def test_accept_a_virtual_machine_within_the_budget():
    environment = runtime()
    environment.run = Mock(
        return_value=SimpleNamespace(
            stdout=json.dumps({"cpus": 2, "memory": 4 * 1024**3})
        )
    )
    environment.verify_machine_budget()
