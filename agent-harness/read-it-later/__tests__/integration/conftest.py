import pytest

from group_scenarios import propose_example_group


@pytest.fixture
def proposed_group(
    repository_with_origin, sandbox_vault, write_capture, recording_forge
):
    return propose_example_group(
        repository_with_origin, sandbox_vault, write_capture, recording_forge
    )
