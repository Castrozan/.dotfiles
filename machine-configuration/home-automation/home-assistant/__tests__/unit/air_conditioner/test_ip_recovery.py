import ipaddress
import json

import home_assistant_air_conditioner_recover_ip as recover_ip_module
import midea_device_discovery
import pytest

HOME_ASSISTANT_COMMAND_MODULE = recover_ip_module


class TestMainRecoveryFlow:
    def test_no_recovery_needed_when_port_open(
        self,
        mock_config_entries,
        access_token,
        mock_recover_api_request,
        monkeypatch,
        capsys,
    ):
        monkeypatch.setattr(
            midea_device_discovery,
            "check_midea_port_open",
            lambda ip: True,
        )
        recover_ip_module.main()
        assert "no recovery needed" in capsys.readouterr().out

    def test_recovers_via_multi_subnet_scan_when_ip_changed(
        self,
        mock_config_entries,
        access_token,
        mock_recover_api_request,
        monkeypatch,
        capsys,
    ):
        open_ports = {"10.10.12.170"}

        monkeypatch.setattr(
            midea_device_discovery,
            "check_midea_port_open",
            lambda ip: ip in open_ports,
        )
        monkeypatch.setattr(
            midea_device_discovery,
            "discover_local_ipv4_networks",
            lambda: [ipaddress.ip_network("10.10.12.0/30")],
        )
        monkeypatch.setattr(
            midea_device_discovery,
            "enumerate_unique_host_addresses_across_networks",
            lambda networks, maximum_host_addresses=4096: [
                "10.10.12.170",
                "10.10.12.171",
            ],
        )
        monkeypatch.setattr(
            midea_device_discovery,
            "probe_address_appears_to_be_midea_device",
            lambda ip: ip == "10.10.12.170",
        )

        recover_ip_module.main()

        output = capsys.readouterr()
        assert "recovered: 192.168.7.2 -> 10.10.12.170" in output.out

        config_file, _ = mock_config_entries
        updated = json.loads(config_file.read_text())
        assert updated["data"]["entries"][0]["data"]["ip_address"] == "10.10.12.170"
        assert any("reload" in call["endpoint"] for call in mock_recover_api_request)

    def test_exits_when_no_local_networks_available(
        self,
        mock_config_entries,
        access_token,
        monkeypatch,
    ):
        monkeypatch.setattr(
            midea_device_discovery,
            "check_midea_port_open",
            lambda ip: False,
        )
        monkeypatch.setattr(
            midea_device_discovery,
            "discover_local_ipv4_networks",
            lambda: [],
        )
        with pytest.raises(SystemExit):
            recover_ip_module.main()

    def test_exits_when_device_not_found_on_any_subnet(
        self,
        mock_config_entries,
        access_token,
        monkeypatch,
        capsys,
    ):
        monkeypatch.setattr(
            midea_device_discovery,
            "check_midea_port_open",
            lambda ip: False,
        )
        monkeypatch.setattr(
            midea_device_discovery,
            "discover_local_ipv4_networks",
            lambda: [ipaddress.ip_network("10.10.12.0/30")],
        )
        with pytest.raises(SystemExit):
            recover_ip_module.main()
        assert "device not found on any local subnet" in capsys.readouterr().err
