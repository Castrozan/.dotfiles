import ipaddress
import json

import pytest

import home_assistant_air_conditioner_recover_ip as recover_ip_module


@pytest.fixture
def mock_recover_token(tmp_path, monkeypatch):
    token_file = tmp_path / "home-assistant-token"
    token_file.write_text("fake-ha-token-for-testing")
    monkeypatch.setattr(
        recover_ip_module,
        "HOME_ASSISTANT_TOKEN_PATH",
        token_file,
    )
    return "fake-ha-token-for-testing"


@pytest.fixture
def mock_config_entries(tmp_path, monkeypatch):
    config_file = tmp_path / "core.config_entries"
    config_data = {
        "version": 1,
        "data": {
            "entries": [
                {
                    "domain": "midea_ac_lan",
                    "entry_id": "test-entry-id-123",
                    "data": {
                        "device_id": 150633094104375,
                        "ip_address": "192.168.7.2",
                        "port": 6444,
                    },
                }
            ]
        },
    }
    config_file.write_text(json.dumps(config_data))
    monkeypatch.setattr(
        recover_ip_module,
        "HOME_ASSISTANT_CONFIG_ENTRIES_PATH",
        config_file,
    )
    return config_file, config_data


@pytest.fixture
def mock_recover_api_request(monkeypatch):
    recorded_calls = []

    def fake_request(token, endpoint, payload=None):
        recorded_calls.append(
            {"token": token, "endpoint": endpoint, "payload": payload}
        )
        return None

    monkeypatch.setattr(
        recover_ip_module,
        "make_home_assistant_api_request",
        fake_request,
    )
    return recorded_calls


class TestReadMideaConfigEntry:
    def test_reads_midea_entry(self, mock_config_entries):
        entry = recover_ip_module.read_midea_config_entry()
        assert entry["domain"] == "midea_ac_lan"
        assert entry["data"]["ip_address"] == "192.168.7.2"
        assert entry["entry_id"] == "test-entry-id-123"

    def test_exits_when_no_midea_entry(self, tmp_path, monkeypatch):
        config_file = tmp_path / "core.config_entries"
        config_file.write_text(json.dumps({"data": {"entries": [{"domain": "other"}]}}))
        monkeypatch.setattr(
            recover_ip_module,
            "HOME_ASSISTANT_CONFIG_ENTRIES_PATH",
            config_file,
        )
        with pytest.raises(SystemExit):
            recover_ip_module.read_midea_config_entry()

    def test_exits_when_config_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            recover_ip_module,
            "HOME_ASSISTANT_CONFIG_ENTRIES_PATH",
            tmp_path / "nonexistent",
        )
        with pytest.raises(SystemExit):
            recover_ip_module.read_midea_config_entry()


class TestParseLocalIpv4Networks:
    def test_extracts_scannable_lan_subnet(self):
        sample_output = (
            "3: wlp4s0    inet 10.10.12.170/21 brd 10.10.15.255 scope global "
            "dynamic noprefixroute wlp4s0\\       valid_lft 403sec\n"
        )
        result = (
            recover_ip_module.parse_local_ipv4_networks_from_ip_address_command_output(
                sample_output
            )
        )
        assert result == [ipaddress.ip_network("10.10.8.0/21")]

    def test_skips_docker_and_tailscale_and_oversized_networks(self):
        sample_output = (
            "3: wlp4s0    inet 10.10.12.170/21 brd 10.10.15.255 scope global "
            "wlp4s0\n"
            "5: docker0    inet 172.17.0.1/16 brd 172.17.255.255 scope global "
            "docker0\n"
            "7: tailscale0    inet 100.100.100.100/32 scope global tailscale0\n"
            "9: bigif    inet 10.0.0.5/8 scope global bigif\n"
        )
        result = (
            recover_ip_module.parse_local_ipv4_networks_from_ip_address_command_output(
                sample_output
            )
        )
        assert result == [ipaddress.ip_network("10.10.8.0/21")]

    def test_skips_single_host_networks(self):
        sample_output = "11: somevpn    inet 10.20.30.40/32 scope global somevpn\n"
        result = (
            recover_ip_module.parse_local_ipv4_networks_from_ip_address_command_output(
                sample_output
            )
        )
        assert result == []

    def test_handles_multiple_interfaces(self):
        sample_output = (
            "3: wlp4s0    inet 10.10.12.170/24 scope global wlp4s0\n"
            "4: eth0    inet 192.168.7.5/24 scope global eth0\n"
        )
        result = (
            recover_ip_module.parse_local_ipv4_networks_from_ip_address_command_output(
                sample_output
            )
        )
        assert ipaddress.ip_network("10.10.12.0/24") in result
        assert ipaddress.ip_network("192.168.7.0/24") in result
        assert len(result) == 2


class TestEnumerateUniqueHostAddresses:
    def test_enumerates_unique_hosts(self):
        networks = [
            ipaddress.ip_network("192.168.7.0/30"),
            ipaddress.ip_network("10.0.0.0/30"),
        ]
        result = recover_ip_module.enumerate_unique_host_addresses_across_networks(
            networks
        )
        assert "192.168.7.1" in result
        assert "192.168.7.2" in result
        assert "10.0.0.1" in result
        assert "10.0.0.2" in result

    def test_deduplicates_overlapping_networks(self):
        networks = [
            ipaddress.ip_network("192.168.7.0/30"),
            ipaddress.ip_network("192.168.7.0/30"),
        ]
        result = recover_ip_module.enumerate_unique_host_addresses_across_networks(
            networks
        )
        assert result == ["192.168.7.1", "192.168.7.2"]

    def test_respects_maximum_host_addresses(self):
        networks = [ipaddress.ip_network("10.0.0.0/24")]
        result = recover_ip_module.enumerate_unique_host_addresses_across_networks(
            networks, maximum_host_addresses=5
        )
        assert len(result) == 5


class TestScanAddressesForOpenMideaPort:
    def test_returns_only_addresses_with_open_port(self, monkeypatch):
        open_set = {"10.0.0.5", "10.0.0.99"}
        monkeypatch.setattr(
            recover_ip_module,
            "check_midea_port_open",
            lambda ip: ip in open_set,
        )
        result = recover_ip_module.scan_addresses_for_open_midea_port(
            ["10.0.0.1", "10.0.0.5", "10.0.0.42", "10.0.0.99"]
        )
        assert result == ["10.0.0.5", "10.0.0.99"]

    def test_empty_input_returns_empty(self):
        result = recover_ip_module.scan_addresses_for_open_midea_port([])
        assert result == []


class TestFilterAddressesConfirmedAsMideaDevices:
    def test_keeps_only_addresses_with_midea_udp_response(self, monkeypatch):
        midea_set = {"10.0.0.5"}
        monkeypatch.setattr(
            recover_ip_module,
            "probe_address_appears_to_be_midea_device",
            lambda ip: ip in midea_set,
        )
        result = recover_ip_module.filter_addresses_confirmed_as_midea_devices(
            ["10.0.0.5", "10.0.0.42"]
        )
        assert result == ["10.0.0.5"]


class TestPickBestMideaCandidateAddress:
    def test_prefers_confirmed_over_unconfirmed(self, capsys):
        result = recover_ip_module.pick_best_midea_candidate_address(
            confirmed_midea_addresses=["10.0.0.5"],
            all_port_open_addresses=["10.0.0.5", "10.0.0.42"],
        )
        assert result == "10.0.0.5"
        stderr_output = capsys.readouterr().err
        assert "10.0.0.42" in stderr_output

    def test_falls_back_to_tcp_only_when_no_udp_confirmation(self, capsys):
        result = recover_ip_module.pick_best_midea_candidate_address(
            confirmed_midea_addresses=[],
            all_port_open_addresses=["10.0.0.42"],
        )
        assert result == "10.0.0.42"
        assert "TCP-only" in capsys.readouterr().err

    def test_returns_none_when_no_candidates(self):
        result = recover_ip_module.pick_best_midea_candidate_address(
            confirmed_midea_addresses=[],
            all_port_open_addresses=[],
        )
        assert result is None

    def test_warns_and_picks_first_when_multiple_confirmed(self, capsys):
        result = recover_ip_module.pick_best_midea_candidate_address(
            confirmed_midea_addresses=["10.0.0.5", "10.0.0.7"],
            all_port_open_addresses=["10.0.0.5", "10.0.0.7"],
        )
        assert result == "10.0.0.5"
        stderr_output = capsys.readouterr().err
        assert "multiple midea candidates" in stderr_output


class TestUpdateMideaConfigEntryIpAddress:
    def test_updates_ip_in_config_file(self, mock_config_entries):
        config_file, _ = mock_config_entries
        recover_ip_module.update_midea_config_entry_ip_address("192.168.7.99")
        updated = json.loads(config_file.read_text())
        midea_entry = updated["data"]["entries"][0]
        assert midea_entry["data"]["ip_address"] == "192.168.7.99"


class TestReloadMideaIntegration:
    def test_calls_reload_endpoint(self, mock_recover_token, mock_recover_api_request):
        result = recover_ip_module.reload_midea_integration(
            "fake-token", "test-entry-id"
        )
        assert result is True
        assert len(mock_recover_api_request) == 1
        call = mock_recover_api_request[0]
        assert (
            call["endpoint"] == "/api/config/config_entries/entry/test-entry-id/reload"
        )

    def test_returns_false_on_api_error(self, monkeypatch):
        def failing_request(token, endpoint, payload=None):
            raise Exception("connection refused")

        monkeypatch.setattr(
            recover_ip_module,
            "make_home_assistant_api_request",
            failing_request,
        )
        result = recover_ip_module.reload_midea_integration(
            "fake-token", "test-entry-id"
        )
        assert result is False


class TestMainRecoveryFlow:
    def test_no_recovery_needed_when_port_open(
        self,
        mock_config_entries,
        mock_recover_token,
        mock_recover_api_request,
        monkeypatch,
        capsys,
    ):
        monkeypatch.setattr(
            recover_ip_module,
            "check_midea_port_open",
            lambda ip: True,
        )
        recover_ip_module.main()
        assert "no recovery needed" in capsys.readouterr().out

    def test_recovers_via_multi_subnet_scan_when_ip_changed(
        self,
        mock_config_entries,
        mock_recover_token,
        mock_recover_api_request,
        monkeypatch,
        capsys,
    ):
        open_ports = {"10.10.12.170"}

        monkeypatch.setattr(
            recover_ip_module,
            "check_midea_port_open",
            lambda ip: ip in open_ports,
        )
        monkeypatch.setattr(
            recover_ip_module,
            "discover_local_ipv4_networks",
            lambda: [ipaddress.ip_network("10.10.12.0/30")],
        )
        monkeypatch.setattr(
            recover_ip_module,
            "enumerate_unique_host_addresses_across_networks",
            lambda networks, maximum_host_addresses=4096: [
                "10.10.12.170",
                "10.10.12.171",
            ],
        )
        monkeypatch.setattr(
            recover_ip_module,
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
        mock_recover_token,
        monkeypatch,
    ):
        monkeypatch.setattr(
            recover_ip_module,
            "check_midea_port_open",
            lambda ip: False,
        )
        monkeypatch.setattr(
            recover_ip_module,
            "discover_local_ipv4_networks",
            lambda: [],
        )
        with pytest.raises(SystemExit):
            recover_ip_module.main()

    def test_exits_when_device_not_found_on_any_subnet(
        self,
        mock_config_entries,
        mock_recover_token,
        monkeypatch,
        capsys,
    ):
        monkeypatch.setattr(
            recover_ip_module,
            "check_midea_port_open",
            lambda ip: False,
        )
        monkeypatch.setattr(
            recover_ip_module,
            "discover_local_ipv4_networks",
            lambda: [ipaddress.ip_network("10.10.12.0/30")],
        )
        with pytest.raises(SystemExit):
            recover_ip_module.main()
        assert "device not found on any local subnet" in capsys.readouterr().err
