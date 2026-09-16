import json

import home_assistant_air_conditioner_control
import home_assistant_air_conditioner_recover_ip as recover_ip_module
import pytest


@pytest.fixture
def mock_ac_api_request(monkeypatch):
    recorded_calls = []

    def fake_request(token, endpoint, payload=None):
        recorded_calls.append(
            {"token": token, "endpoint": endpoint, "payload": payload}
        )
        if endpoint.startswith("/api/states/"):
            return {
                "state": "cool",
                "attributes": {
                    "indoor_temperature": 23.5,
                    "temperature": 24.0,
                    "fan_mode": "auto",
                    "swing_mode": "off",
                    "preset_mode": "none",
                    "realtime_power": 850.0,
                    "total_energy_consumption": 120.5,
                },
            }
        return None

    monkeypatch.setattr(
        home_assistant_air_conditioner_control,
        "make_home_assistant_api_request",
        fake_request,
    )
    return recorded_calls


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
