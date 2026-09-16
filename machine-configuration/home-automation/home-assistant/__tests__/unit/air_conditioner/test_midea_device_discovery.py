import ipaddress

import home_assistant_air_conditioner_recover_ip as recover_ip_module
import midea_device_discovery

HOME_ASSISTANT_COMMAND_MODULE = recover_ip_module


class TestParseLocalIpv4Networks:
    def test_extracts_scannable_lan_subnet(self):
        sample_output = (
            "3: wlp4s0    inet 10.10.12.170/21 brd 10.10.15.255 scope global "
            "dynamic noprefixroute wlp4s0\\       valid_lft 403sec\n"
        )
        result = midea_device_discovery.parse_local_ipv4_networks_from_ip_address_command_output(
            sample_output
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
        result = midea_device_discovery.parse_local_ipv4_networks_from_ip_address_command_output(
            sample_output
        )
        assert result == [ipaddress.ip_network("10.10.8.0/21")]

    def test_skips_single_host_networks(self):
        sample_output = "11: somevpn    inet 10.20.30.40/32 scope global somevpn\n"
        result = midea_device_discovery.parse_local_ipv4_networks_from_ip_address_command_output(
            sample_output
        )
        assert result == []

    def test_handles_multiple_interfaces(self):
        sample_output = (
            "3: wlp4s0    inet 10.10.12.170/24 scope global wlp4s0\n"
            "4: eth0    inet 192.168.7.5/24 scope global eth0\n"
        )
        result = midea_device_discovery.parse_local_ipv4_networks_from_ip_address_command_output(
            sample_output
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
        result = midea_device_discovery.enumerate_unique_host_addresses_across_networks(
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
        result = midea_device_discovery.enumerate_unique_host_addresses_across_networks(
            networks
        )
        assert result == ["192.168.7.1", "192.168.7.2"]

    def test_respects_maximum_host_addresses(self):
        networks = [ipaddress.ip_network("10.0.0.0/24")]
        result = midea_device_discovery.enumerate_unique_host_addresses_across_networks(
            networks, maximum_host_addresses=5
        )
        assert len(result) == 5


class TestScanAddressesForOpenMideaPort:
    def test_returns_only_addresses_with_open_port(self, monkeypatch):
        open_set = {"10.0.0.5", "10.0.0.99"}
        monkeypatch.setattr(
            midea_device_discovery,
            "check_midea_port_open",
            lambda ip: ip in open_set,
        )
        result = midea_device_discovery.scan_addresses_for_open_midea_port(
            ["10.0.0.1", "10.0.0.5", "10.0.0.42", "10.0.0.99"]
        )
        assert result == ["10.0.0.5", "10.0.0.99"]

    def test_empty_input_returns_empty(self):
        result = midea_device_discovery.scan_addresses_for_open_midea_port([])
        assert result == []


class TestFilterAddressesConfirmedAsMideaDevices:
    def test_keeps_only_addresses_with_midea_udp_response(self, monkeypatch):
        midea_set = {"10.0.0.5"}
        monkeypatch.setattr(
            midea_device_discovery,
            "probe_address_appears_to_be_midea_device",
            lambda ip: ip in midea_set,
        )
        result = midea_device_discovery.filter_addresses_confirmed_as_midea_devices(
            ["10.0.0.5", "10.0.0.42"]
        )
        assert result == ["10.0.0.5"]


class TestPickBestMideaCandidateAddress:
    def test_prefers_confirmed_over_unconfirmed(self, capsys):
        result = midea_device_discovery.pick_best_midea_candidate_address(
            confirmed_midea_addresses=["10.0.0.5"],
            all_port_open_addresses=["10.0.0.5", "10.0.0.42"],
        )
        assert result == "10.0.0.5"
        stderr_output = capsys.readouterr().err
        assert "10.0.0.42" in stderr_output

    def test_falls_back_to_tcp_only_when_no_udp_confirmation(self, capsys):
        result = midea_device_discovery.pick_best_midea_candidate_address(
            confirmed_midea_addresses=[],
            all_port_open_addresses=["10.0.0.42"],
        )
        assert result == "10.0.0.42"
        assert "TCP-only" in capsys.readouterr().err

    def test_returns_none_when_no_candidates(self):
        result = midea_device_discovery.pick_best_midea_candidate_address(
            confirmed_midea_addresses=[],
            all_port_open_addresses=[],
        )
        assert result is None

    def test_warns_and_picks_first_when_multiple_confirmed(self, capsys):
        result = midea_device_discovery.pick_best_midea_candidate_address(
            confirmed_midea_addresses=["10.0.0.5", "10.0.0.7"],
            all_port_open_addresses=["10.0.0.5", "10.0.0.7"],
        )
        assert result == "10.0.0.5"
        stderr_output = capsys.readouterr().err
        assert "multiple midea candidates" in stderr_output
