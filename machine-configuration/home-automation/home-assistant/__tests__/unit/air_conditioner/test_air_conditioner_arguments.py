import air_conditioner_arguments
import pytest


class TestValidateTemperature:
    def test_accepts_minimum(self):
        assert air_conditioner_arguments.validate_temperature("16") == 16.0

    def test_accepts_maximum(self):
        assert air_conditioner_arguments.validate_temperature("30") == 30.0

    def test_accepts_half_degree(self):
        assert air_conditioner_arguments.validate_temperature("22.5") == 22.5

    def test_rejects_below_minimum(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_temperature("15")

    def test_rejects_above_maximum(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_temperature("31")


class TestValidateHvacMode:
    def test_accepts_cool(self):
        assert air_conditioner_arguments.validate_hvac_mode("cool") == "cool"

    def test_accepts_heat(self):
        assert air_conditioner_arguments.validate_hvac_mode("heat") == "heat"

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

    def test_accepts_auto(self):
        assert air_conditioner_arguments.validate_fan_mode("auto") == "auto"

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_fan_mode("turbo")


class TestValidateSwingMode:
    def test_accepts_vertical(self):
        assert air_conditioner_arguments.validate_swing_mode("vertical") == "vertical"

    def test_accepts_both(self):
        assert air_conditioner_arguments.validate_swing_mode("both") == "both"

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_swing_mode("diagonal")


class TestValidatePresetMode:
    def test_accepts_eco(self):
        assert air_conditioner_arguments.validate_preset_mode("eco") == "eco"

    def test_accepts_boost(self):
        assert air_conditioner_arguments.validate_preset_mode("boost") == "boost"

    def test_rejects_invalid(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.validate_preset_mode("max")


class TestParseSetCommandArguments:
    def test_parses_temp_flag(self):
        result = air_conditioner_arguments.parse_set_command_arguments(["--temp", "22"])
        assert result == {"temperature": 22.0}

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

    def test_returns_empty_dict_for_no_arguments(self):
        result = air_conditioner_arguments.parse_set_command_arguments([])
        assert result == {}

    def test_exits_on_unknown_flag(self):
        with pytest.raises(SystemExit):
            air_conditioner_arguments.parse_set_command_arguments(["--color", "red"])
