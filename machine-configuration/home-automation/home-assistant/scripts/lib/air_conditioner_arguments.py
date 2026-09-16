import sys

VALID_HVAC_MODES = ["off", "auto", "cool", "dry", "heat", "fan_only"]
VALID_FAN_MODES = ["silent", "low", "medium", "high", "full", "auto"]
VALID_SWING_MODES = ["off", "vertical", "horizontal", "both"]
VALID_PRESET_MODES = ["none", "comfort", "eco", "boost", "sleep", "away"]

MINIMUM_TEMPERATURE_CELSIUS = 16
MAXIMUM_TEMPERATURE_CELSIUS = 30


def validate_hvac_mode(value: str) -> str:
    if value not in VALID_HVAC_MODES:
        joined = ", ".join(VALID_HVAC_MODES)
        print(f"Invalid HVAC mode '{value}'. Valid: {joined}", file=sys.stderr)
        raise SystemExit(1)
    return value


def validate_fan_mode(value: str) -> str:
    if value not in VALID_FAN_MODES:
        joined = ", ".join(VALID_FAN_MODES)
        print(f"Invalid fan mode '{value}'. Valid: {joined}", file=sys.stderr)
        raise SystemExit(1)
    return value


def validate_swing_mode(value: str) -> str:
    if value not in VALID_SWING_MODES:
        joined = ", ".join(VALID_SWING_MODES)
        print(f"Invalid swing mode '{value}'. Valid: {joined}", file=sys.stderr)
        raise SystemExit(1)
    return value


def validate_preset_mode(value: str) -> str:
    if value not in VALID_PRESET_MODES:
        joined = ", ".join(VALID_PRESET_MODES)
        print(f"Invalid preset mode '{value}'. Valid: {joined}", file=sys.stderr)
        raise SystemExit(1)
    return value


def validate_temperature(value_string: str) -> float:
    temperature = float(value_string)
    if (
        temperature < MINIMUM_TEMPERATURE_CELSIUS
        or temperature > MAXIMUM_TEMPERATURE_CELSIUS
    ):
        min_t = MINIMUM_TEMPERATURE_CELSIUS
        max_t = MAXIMUM_TEMPERATURE_CELSIUS
        print(
            f"Temperature must be {min_t}-{max_t}°C, got {temperature}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return temperature


def print_usage_and_exit() -> None:
    print(
        "Usage: ha-ac <command> [options]\n"
        "\n"
        "Commands:\n"
        "  on                                Turn on\n"
        "  off                               Turn off\n"
        "  status                            Show current state\n"
        "  mode   <mode>                     Set HVAC mode"
        " (off, auto, cool, dry, heat, fan_only)\n"
        "  temp   <celsius>                  Set temperature (16-30)\n"
        "  fan    <speed>                    Set fan"
        " (silent, low, medium, high, full, auto)\n"
        "  swing  <direction>                Set swing"
        " (off, vertical, horizontal, both)\n"
        "  preset <preset>                   Set preset"
        " (none, comfort, eco, boost, sleep, away)\n"
        "  set    [--temp N] [--fan F]       Set multiple attributes"
        " [--swing S] [--mode M] [--preset P]",
        file=sys.stderr,
    )
    raise SystemExit(1)


def parse_set_command_arguments(arguments: list[str]) -> dict:
    attributes = {}
    index = 0
    while index < len(arguments):
        if arguments[index] == "--temp" and index + 1 < len(arguments):
            attributes["temperature"] = validate_temperature(arguments[index + 1])
            index += 2
        elif arguments[index] == "--fan" and index + 1 < len(arguments):
            attributes["fan_mode"] = validate_fan_mode(arguments[index + 1])
            index += 2
        elif arguments[index] == "--swing" and index + 1 < len(arguments):
            attributes["swing_mode"] = validate_swing_mode(arguments[index + 1])
            index += 2
        elif arguments[index] == "--mode" and index + 1 < len(arguments):
            attributes["hvac_mode"] = validate_hvac_mode(arguments[index + 1])
            index += 2
        elif arguments[index] == "--preset" and index + 1 < len(arguments):
            attributes["preset_mode"] = validate_preset_mode(arguments[index + 1])
            index += 2
        else:
            print(f"Unknown option: {arguments[index]}", file=sys.stderr)
            raise SystemExit(1)
    return attributes
