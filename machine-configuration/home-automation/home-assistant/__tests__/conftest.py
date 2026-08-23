import sys
from pathlib import Path
import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
LIB_DIR = SCRIPTS_DIR / "lib"

sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def access_token(request, monkeypatch):
    monkeypatch.setattr(
        request.module.HOME_ASSISTANT_COMMAND_MODULE,
        "read_home_assistant_token",
        lambda: "fake-ha-token-for-testing",
    )
    return "fake-ha-token-for-testing"


@pytest.fixture
def mock_home_assistant_api_request(monkeypatch):
    import home_assistant_light_control

    recorded_calls = []

    def fake_request(token, endpoint, payload=None):
        recorded_calls.append(
            {"token": token, "endpoint": endpoint, "payload": payload}
        )
        if endpoint.startswith("/api/states/"):
            return {
                "state": "on",
                "attributes": {
                    "brightness": 200,
                    "color_temp_kelvin": 3500,
                    "friendly_name": endpoint.split("/")[-1].split(".")[-1],
                },
            }
        return None

    monkeypatch.setattr(
        home_assistant_light_control,
        "make_home_assistant_api_request",
        fake_request,
    )
    return recorded_calls
