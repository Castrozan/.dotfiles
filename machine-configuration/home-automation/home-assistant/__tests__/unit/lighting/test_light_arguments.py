import home_assistant_light_control
import pytest

HOME_ASSISTANT_COMMAND_MODULE = home_assistant_light_control


class TestResolveTargetEntityIds:
    def test_resolves_all_to_every_light(self):
        result = home_assistant_light_control.resolve_target_entity_ids("all")
        assert result == home_assistant_light_control.ALL_LIGHT_ENTITY_IDS

    def test_resolves_single_light_name(self):
        result = home_assistant_light_control.resolve_target_entity_ids("bedroom")
        assert result == ["light.bedroom"]

    def test_resolves_kitchen(self):
        result = home_assistant_light_control.resolve_target_entity_ids("kitchen")
        assert result == ["light.kitchen"]

    def test_exits_on_unknown_light_name(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.resolve_target_entity_ids("garage")


class TestParseBrightnessArgument:
    def test_parses_valid_brightness(self):
        assert home_assistant_light_control.parse_brightness_argument("128") == 128

    def test_parses_zero(self):
        assert home_assistant_light_control.parse_brightness_argument("0") == 0

    def test_parses_maximum(self):
        assert home_assistant_light_control.parse_brightness_argument("255") == 255

    def test_exits_on_negative(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.parse_brightness_argument("-1")

    def test_exits_on_too_high(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.parse_brightness_argument("256")


class TestParseColorTemperatureArgument:
    def test_parses_valid_temperature(self):
        assert (
            home_assistant_light_control.parse_color_temperature_argument("3500")
            == 3500
        )

    def test_parses_minimum(self):
        assert (
            home_assistant_light_control.parse_color_temperature_argument("2000")
            == 2000
        )

    def test_parses_maximum(self):
        assert (
            home_assistant_light_control.parse_color_temperature_argument("6500")
            == 6500
        )

    def test_exits_on_too_low(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.parse_color_temperature_argument("1999")

    def test_exits_on_too_high(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.parse_color_temperature_argument("6501")


class TestParseOptionalAttributesFromArguments:
    def test_parses_brightness_flag(self):
        result = home_assistant_light_control.parse_optional_attributes_from_arguments(
            ["--brightness", "200"]
        )
        assert result == {"brightness": 200}

    def test_parses_temp_flag(self):
        result = home_assistant_light_control.parse_optional_attributes_from_arguments(
            ["--temp", "4000"]
        )
        assert result == {"color_temp_kelvin": 4000}

    def test_parses_both_flags(self):
        result = home_assistant_light_control.parse_optional_attributes_from_arguments(
            ["--brightness", "180", "--temp", "3500"]
        )
        assert result == {"brightness": 180, "color_temp_kelvin": 3500}

    def test_returns_empty_dict_for_no_arguments(self):
        result = home_assistant_light_control.parse_optional_attributes_from_arguments(
            []
        )
        assert result == {}

    def test_exits_on_unknown_flag(self):
        with pytest.raises(SystemExit):
            home_assistant_light_control.parse_optional_attributes_from_arguments(
                ["--color", "red"]
            )
