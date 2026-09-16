import json

import home_assistant_air_conditioner_recover_ip as recover_ip_module
import pytest

HOME_ASSISTANT_COMMAND_MODULE = recover_ip_module


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


class TestUpdateMideaConfigEntryIpAddress:
    def test_updates_ip_in_config_file(self, mock_config_entries):
        config_file, _ = mock_config_entries
        recover_ip_module.update_midea_config_entry_ip_address("192.168.7.99")
        updated = json.loads(config_file.read_text())
        midea_entry = updated["data"]["entries"][0]
        assert midea_entry["data"]["ip_address"] == "192.168.7.99"


class TestReloadMideaIntegration:
    def test_calls_reload_endpoint(self, access_token, mock_recover_api_request):
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
