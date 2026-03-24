import json
import socket

import pytest

import home_assistant_air_conditioner_recover_ip


@pytest.fixture
def mock_recover_token(tmp_path, monkeypatch):
    token_file = tmp_path / "home-assistant-token"
    token_file.write_text("fake-ha-token-for-testing")
    monkeypatch.setattr(
        home_assistant_air_conditioner_recover_ip,
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
        home_assistant_air_conditioner_recover_ip,
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
        home_assistant_air_conditioner_recover_ip,
        "make_home_assistant_api_request",
        fake_request,
    )
    return recorded_calls


class TestReadMideaConfigEntry:
    def test_reads_midea_entry(self, mock_config_entries):
        entry = home_assistant_air_conditioner_recover_ip.read_midea_config_entry()
        assert entry["domain"] == "midea_ac_lan"
        assert entry["data"]["ip_address"] == "192.168.7.2"
        assert entry["entry_id"] == "test-entry-id-123"

    def test_exits_when_no_midea_entry(self, tmp_path, monkeypatch):
        config_file = tmp_path / "core.config_entries"
        config_file.write_text(json.dumps({"data": {"entries": [{"domain": "other"}]}}))
        monkeypatch.setattr(
            home_assistant_air_conditioner_recover_ip,
            "HOME_ASSISTANT_CONFIG_ENTRIES_PATH",
            config_file,
        )
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_recover_ip.read_midea_config_entry()

    def test_exits_when_config_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            home_assistant_air_conditioner_recover_ip,
            "HOME_ASSISTANT_CONFIG_ENTRIES_PATH",
            tmp_path / "nonexistent",
        )
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_recover_ip.read_midea_config_entry()


class TestDeriveSubnetPrefix:
    def test_extracts_first_three_octets(self):
        result = home_assistant_air_conditioner_recover_ip.derive_subnet_prefix(
            "192.168.7.5"
        )
        assert result == "192.168.7"

    def test_handles_different_subnet(self):
        result = home_assistant_air_conditioner_recover_ip.derive_subnet_prefix(
            "10.0.1.42"
        )
        assert result == "10.0.1"


class TestScanSubnetForMideaDevice:
    def test_finds_device_on_subnet(self, monkeypatch):
        def fake_check(ip):
            return ip == "192.168.7.5"

        monkeypatch.setattr(
            home_assistant_air_conditioner_recover_ip,
            "check_midea_port_open",
            fake_check,
        )
        result = home_assistant_air_conditioner_recover_ip.scan_subnet_for_midea_device(
            "192.168.7"
        )
        assert result == "192.168.7.5"

    def test_returns_none_when_no_device(self, monkeypatch):
        monkeypatch.setattr(
            home_assistant_air_conditioner_recover_ip,
            "check_midea_port_open",
            lambda ip: False,
        )
        result = home_assistant_air_conditioner_recover_ip.scan_subnet_for_midea_device(
            "192.168.7"
        )
        assert result is None


class TestUpdateMideaConfigEntryIpAddress:
    def test_updates_ip_in_config_file(self, mock_config_entries):
        config_file, _ = mock_config_entries
        home_assistant_air_conditioner_recover_ip.update_midea_config_entry_ip_address(
            "192.168.7.99"
        )
        updated = json.loads(config_file.read_text())
        midea_entry = updated["data"]["entries"][0]
        assert midea_entry["data"]["ip_address"] == "192.168.7.99"


class TestReloadMideaIntegration:
    def test_calls_reload_endpoint(self, mock_recover_token, mock_recover_api_request):
        result = home_assistant_air_conditioner_recover_ip.reload_midea_integration(
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
            home_assistant_air_conditioner_recover_ip,
            "make_home_assistant_api_request",
            failing_request,
        )
        result = home_assistant_air_conditioner_recover_ip.reload_midea_integration(
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
            home_assistant_air_conditioner_recover_ip,
            "check_midea_port_open",
            lambda ip: True,
        )
        home_assistant_air_conditioner_recover_ip.main()
        assert "no recovery needed" in capsys.readouterr().out

    def test_recovers_when_ip_changed(
        self,
        mock_config_entries,
        mock_recover_token,
        mock_recover_api_request,
        monkeypatch,
        capsys,
    ):
        port_open_ips = {"192.168.7.5"}

        monkeypatch.setattr(
            home_assistant_air_conditioner_recover_ip,
            "check_midea_port_open",
            lambda ip: ip in port_open_ips,
        )
        monkeypatch.setattr(
            home_assistant_air_conditioner_recover_ip,
            "scan_subnet_for_midea_device",
            lambda prefix: "192.168.7.5",
        )

        home_assistant_air_conditioner_recover_ip.main()

        output = capsys.readouterr()
        assert "recovered: 192.168.7.2 -> 192.168.7.5" in output.out

        config_file, _ = mock_config_entries
        updated = json.loads(config_file.read_text())
        assert updated["data"]["entries"][0]["data"]["ip_address"] == "192.168.7.5"

        assert any("reload" in call["endpoint"] for call in mock_recover_api_request)

    def test_exits_when_device_not_found(
        self,
        mock_config_entries,
        mock_recover_token,
        monkeypatch,
    ):
        monkeypatch.setattr(
            home_assistant_air_conditioner_recover_ip,
            "check_midea_port_open",
            lambda ip: False,
        )
        monkeypatch.setattr(
            home_assistant_air_conditioner_recover_ip,
            "scan_subnet_for_midea_device",
            lambda prefix: None,
        )
        with pytest.raises(SystemExit):
            home_assistant_air_conditioner_recover_ip.main()
