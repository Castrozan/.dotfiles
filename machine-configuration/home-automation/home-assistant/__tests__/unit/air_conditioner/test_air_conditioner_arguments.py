import air_conditioner_arguments
import pytest


class TestValidateTemperature:
    def test_accepts_minimum(self):
        assert air_conditioner_arguments.validate_temperature("16") == 16.0

    def test_rejects_below_minimum(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_temperature("15")

    def test_rejects_above_maximum(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_temperature("31")


class TestValidateHvacMode:
    def test_accepts_auto(self):
        assert air_conditioner_arguments.validate_hvac_mode("auto") == "auto"

    def test_accepts_fan_only(self):
        assert air_conditioner_arguments.validate_hvac_mode("fan_only") == "fan_only"

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_hvac_mode("turbo")


class TestValidateFanMode:
    def test_accepts_silent(self):
        assert air_conditioner_arguments.validate_fan_mode("silent") == "silent"

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_fan_mode("turbo")


class TestValidateSwingMode:
    def test_accepts_vertical(self):
        assert air_conditioner_arguments.validate_swing_mode("vertical") == "vertical"

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_swing_mode("diagonal")


class TestValidatePresetMode:
    def test_accepts_boost(self):
        assert air_conditioner_arguments.validate_preset_mode("boost") == "boost"

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_preset_mode("max")


class TestParseSetCommandArguments:
    def test_parses_fan_flag(self):
        result = air_conditioner_arguments.parse_set_command_arguments(
            ["--fan", "high"]
        )
        assert result == {"fan_mode": "high"}

    def test_parses_multiple_flags(self):
        result = air_conditioner_arguments.parse_set_command_arguments(
            ["--temp", "20", "--fan", "low", "--mode", "cool"]
        )
        assert result == {
            "temperature": 20.0,
            "fan_mode": "low",
            "hvac_mode": "cool",
        }

    def test_parses_all_flags(self):
        result = air_conditioner_arguments.parse_set_command_arguments(
            [
                "--temp",
                "25",
                "--fan",
                "auto",
                "--swing",
                "both",
                "--mode",
                "heat",
                "--preset",
                "eco",
            ]
        )
        assert result == {
            "temperature": 25.0,
            "fan_mode": "auto",
            "swing_mode": "both",
            "hvac_mode": "heat",
            "preset_mode": "eco",
        }

    def test_exits_on_unknown_flag(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.parse_set_command_arguments(["--color", "red"])
