import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import benchmark_core

LIBRARY_DIRECTORY = Path(benchmark_core.__file__).resolve().parent


def _resolved_constant_in_a_fresh_interpreter(constant_name: str, environment: dict):
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import benchmark_core; print(benchmark_core.{constant_name})",
        ],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(LIBRARY_DIRECTORY), **environment},
    )
    assert completed.returncode == 0, completed.stderr
    return Path(completed.stdout.strip())


class TestConfiguredBenchmarkTarget:
    @pytest.mark.parametrize("host", ["kira", "rin"])
    def test_maps_each_darwin_host_to_its_own_system_output(self, host):
        with patch.dict("os.environ", {benchmark_core.BENCHMARK_HOST_VARIABLE: host}):
            target = benchmark_core.required_benchmark_target()

        assert target.host == host
        assert target.configuration == "darwin"
        assert target.flake_output == f"darwinConfigurations.{host}.system"

    def test_maps_the_nixos_host_to_its_toplevel_build(self):
        with patch.dict(
            "os.environ", {benchmark_core.BENCHMARK_HOST_VARIABLE: "chise"}
        ):
            target = benchmark_core.required_benchmark_target()

        assert target.configuration == "nixos"
        assert target.flake_output == (
            "nixosConfigurations.chise.config.system.build.toplevel"
        )

    def test_ignores_surrounding_whitespace_on_the_injected_host(self):
        with patch.dict(
            "os.environ", {benchmark_core.BENCHMARK_HOST_VARIABLE: "  chise\n"}
        ):
            assert benchmark_core.configured_benchmark_target().host == "chise"

    @pytest.mark.parametrize("host", ["", "localhost", "Kira", "zanoni"])
    def test_reports_no_target_for_a_name_that_is_not_a_configuration_host(self, host):
        with patch.dict("os.environ", {benchmark_core.BENCHMARK_HOST_VARIABLE: host}):
            assert benchmark_core.configured_benchmark_target() is None

    def test_exits_with_an_actionable_message_when_no_host_is_injected(self, capsys):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(SystemExit) as exit_info:
                benchmark_core.required_benchmark_target()

        assert exit_info.value.code == 1
        report = capsys.readouterr().out
        assert benchmark_core.BENCHMARK_HOST_VARIABLE in report
        assert "chise, kira, rin" in report


class TestCheckoutResolution:
    def test_defaults_to_the_dotfiles_checkout_in_home(self, tmp_path):
        resolved = _resolved_constant_in_a_fresh_interpreter(
            "DOTFILES_DIRECTORY", {"HOME": str(tmp_path)}
        )
        assert resolved == tmp_path / ".dotfiles"

    def test_reads_a_source_checkout_from_the_environment(self, tmp_path):
        resolved = _resolved_constant_in_a_fresh_interpreter(
            "TRACKED_BASELINE_DIRECTORY",
            {
                "HOME": str(tmp_path / "home"),
                benchmark_core.BENCHMARK_CHECKOUT_VARIABLE: str(tmp_path / "checkout"),
            },
        )
        assert resolved == (
            tmp_path / "checkout" / "machine-configuration" / "development" / "testing"
        )
