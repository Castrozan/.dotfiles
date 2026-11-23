from unittest.mock import patch

import brightness


class TestPersistedGammaState:
    def test_returns_maximum_when_state_file_contents_invalid(self, tmp_path):
        path = tmp_path / "gamma"
        path.write_text("not-a-number")
        with patch.object(brightness, "GAMMA_STATE_PATH", path):
            assert (
                brightness.read_persisted_gamma_percentage()
                == brightness.GAMMA_MAXIMUM_PERCENT
            )

    def test_writes_value_and_creates_parent_directory(self, tmp_path):
        path = tmp_path / "nested" / "gamma"
        with patch.object(brightness, "GAMMA_STATE_PATH", path):
            brightness.write_persisted_gamma_percentage(73)
            assert path.read_text() == "73"
