from unittest.mock import patch

import benchmark_rebuild


class TestDetectConfigurationType:
    def test_returns_nixos_when_nixos_directory_and_hostname_match(self, tmp_path):
        hostname_file = tmp_path / "hostname"
        hostname_file.write_text("zanoni\n")
        nixos_dir = tmp_path / "nixos"
        nixos_dir.mkdir()

        real_path = __import__("pathlib").Path

        def path_factory(p):
            if p == "/etc/hostname":
                return real_path(hostname_file)
            if p == "/etc/nixos":
                return real_path(nixos_dir)
            return real_path(p)

        with patch(
            "benchmark_rebuild.Path",
            side_effect=path_factory,
        ):
            result = benchmark_rebuild.detect_configuration_type()
            assert result == "nixos"

    def test_returns_darwin_when_no_nixos_directory(self):
        with patch(
            "benchmark_rebuild.Path",
        ) as mock_path:
            mock_path.return_value.is_dir.return_value = False
            result = benchmark_rebuild.detect_configuration_type()
            assert result == "darwin"


class TestGetFlakeOutputForConfiguration:
    def test_returns_nixos_output(self):
        result = benchmark_rebuild.get_flake_output_for_configuration("nixos")
        assert "nixosConfigurations" in result

    def test_returns_darwin_output_for_darwin(self):
        result = benchmark_rebuild.get_flake_output_for_configuration("darwin")
        assert "darwinConfigurations" in result

    def test_returns_darwin_output_for_unknown(self):
        result = benchmark_rebuild.get_flake_output_for_configuration("other")
        assert "darwinConfigurations" in result
