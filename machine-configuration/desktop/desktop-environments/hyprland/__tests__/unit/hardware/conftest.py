from unittest.mock import patch

import brightness
import pytest


@pytest.fixture
def brightness_runtime_defaults(tmp_path):
    with (
        patch.object(brightness, "GAMMA_STATE_PATH", tmp_path / "gamma"),
        patch.object(brightness, "uses_hardware_brightness", return_value=True),
        patch.object(
            brightness,
            "get_gamma_percentage",
            side_effect=lambda: brightness.read_persisted_gamma_percentage(),
        ),
    ):
        yield


@pytest.fixture
def brightness_hardware_floor():
    with patch.object(brightness, "get_hardware_brightness_percentage", return_value=1):
        yield
