import argparse

import pytest

from a2a_server.__main__ import construct_backend_from_arguments
from a2a_server.backends.herdr_backend import HerdrAttachedAgentBackend


def _herdr_backend_arguments(**overrides) -> argparse.Namespace:
    defaults = dict(
        backend_type="herdr",
        herdr_pane="wP:pT",
        herdr_meaningful_line_pattern=None,
        subprocess_command=None,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class TestConstructHerdrBackendFromArguments:
    def test_missing_herdr_pane_exits_with_code_two(self):
        with pytest.raises(SystemExit) as raised_exit:
            construct_backend_from_arguments(_herdr_backend_arguments(herdr_pane=None))
        assert raised_exit.value.code == 2

    def test_builds_herdr_backend_bound_to_the_given_pane(self):
        backend = construct_backend_from_arguments(
            _herdr_backend_arguments(herdr_pane="wZ:p9")
        )
        assert isinstance(backend, HerdrAttachedAgentBackend)
        assert backend._herdr_pane_id == "wZ:p9"
