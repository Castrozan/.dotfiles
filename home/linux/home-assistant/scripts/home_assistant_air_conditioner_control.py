import json
import sys
import urllib.request
from pathlib import Path

HOME_ASSISTANT_BASE_URL = "http://localhost:8123"
HOME_ASSISTANT_TOKEN_PATH = Path.home() / ".secrets" / "home-assistant-token"

AIR_CONDITIONER_ENTITY_ID = "climate.150633094104375_climate"

VALID_HVAC_MODES = ["off", "auto", "cool", "dry", "heat", "fan_only"]
VALID_FAN_MODES = ["silent", "low", "medium", "high", "full", "auto"]
VALID_SWING_MODES = ["off", "vertical", "horizontal", "both"]
VALID_PRESET_MODES = ["none", "comfort", "eco", "boost", "sleep", "away"]

MINIMUM_TEMPERATURE_CELSIUS = 16
MAXIMUM_TEMPERATURE_CELSIUS = 30


def read_home_assistant_token() -> str:
    token_file = HOME_ASSISTANT_TOKEN_PATH
    if not token_file.is_file():
        print(
            f"Home Assistant token not found at {token_file}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return token_file.read_text().strip()


def make_home_assistant_api_request(
    token: str, endpoint: str, payload: dict | None = None
) -> dict | list | None:
    url = f"{HOME_ASSISTANT_BASE_URL}{endpoint}"
    data = json.dumps(payload).encode() if payload else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST" if payload is not None else "GET",
    )
    response = urllib.request.urlopen(request)
    body = response.read().decode()
    if body:
        return json.loads(body)
    return None


def get_air_conditioner_status(token: str) -> None:
    result = make_home_assistant_api_request(
        token, f"/api/states/{AIR_CONDITIONER_ENTITY_ID}"
    )
    if result is None:
        print("Error fetching air conditioner state", file=sys.stderr)
        raise SystemExit(1)
    state = result.get("state", "unknown")
    attributes = result.get("attributes", {})
    indoor_temperature = attributes.get("indoor_temperature", "N/A")
    target_temperature = attributes.get("temperature", "N/A")
    fan_mode = attributes.get("fan_mode", "N/A")
    swing_mode = attributes.get("swing_mode", "N/A")
    preset_mode = attributes.get("preset_mode", "N/A")
    realtime_power = attributes.get("realtime_power", "N/A")
    total_energy = attributes.get("total_energy_consumption", "N/A")
    print(f"state: {state}")
    print(f"indoor_temperature: {indoor_temperature}°C")
    print(f"target_temperature: {target_temperature}°C")
    print(f"fan_mode: {fan_mode}")
    print(f"swing_mode: {swing_mode}")
    print(f"preset_mode: {preset_mode}")
    print(f"realtime_power: {realtime_power}W")
    print(f"total_energy: {total_energy}kWh")


def turn_on_air_conditioner(token: str) -> None:
    make_home_assistant_api_request(
        token,
        "/api/services/climate/turn_on",
        {"entity_id": AIR_CONDITIONER_ENTITY_ID},
    )
    print("air conditioner: on")


def turn_off_air_conditioner(token: str) -> None:
    make_home_assistant_api_request(
        token,
        "/api/services/climate/turn_off",
        {"entity_id": AIR_CONDITIONER_ENTITY_ID},
    )
    print("air conditioner: off")


def set_air_conditioner_hvac_mode(token: str, hvac_mode: str) -> None:
    make_home_assistant_api_request(
        token,
        "/api/services/climate/set_hvac_mode",
        {"entity_id": AIR_CONDITIONER_ENTITY_ID, "hvac_mode": hvac_mode},
    )
    print(f"hvac_mode: {hvac_mode}")


def set_air_conditioner_temperature(token: str, temperature: float) -> None:
    make_home_assistant_api_request(
        token,
        "/api/services/climate/set_temperature",
        {"entity_id": AIR_CONDITIONER_ENTITY_ID, "temperature": temperature},
    )
    print(f"temperature: {temperature}°C")


def set_air_conditioner_fan_mode(token: str, fan_mode: str) -> None:
    make_home_assistant_api_request(
        token,
        "/api/services/climate/set_fan_mode",
        {"entity_id": AIR_CONDITIONER_ENTITY_ID, "fan_mode": fan_mode},
    )
    print(f"fan_mode: {fan_mode}")


def set_air_conditioner_swing_mode(token: str, swing_mode: str) -> None:
    make_home_assistant_api_request(
        token,
        "/api/services/climate/set_swing_mode",
        {"entity_id": AIR_CONDITIONER_ENTITY_ID, "swing_mode": swing_mode},
    )
    print(f"swing_mode: {swing_mode}")


def set_air_conditioner_preset_mode(token: str, preset_mode: str) -> None:
    make_home_assistant_api_request(
        token,
        "/api/services/climate/set_preset_mode",
        {"entity_id": AIR_CONDITIONER_ENTITY_ID, "preset_mode": preset_mode},
    )
    print(f"preset_mode: {preset_mode}")


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


def apply_air_conditioner_attributes(token: str, attributes: dict) -> None:
    if "hvac_mode" in attributes:
        set_air_conditioner_hvac_mode(token, attributes["hvac_mode"])
    if "temperature" in attributes:
        set_air_conditioner_temperature(token, attributes["temperature"])
    if "fan_mode" in attributes:
        set_air_conditioner_fan_mode(token, attributes["fan_mode"])
    if "swing_mode" in attributes:
        set_air_conditioner_swing_mode(token, attributes["swing_mode"])
    if "preset_mode" in attributes:
        set_air_conditioner_preset_mode(token, attributes["preset_mode"])


def main() -> None:
    if len(sys.argv) < 2:
        print_usage_and_exit()

    command = sys.argv[1]
    token = read_home_assistant_token()

    if command == "on":
        turn_on_air_conditioner(token)

    elif command == "off":
        turn_off_air_conditioner(token)

    elif command == "status":
        get_air_conditioner_status(token)

    elif command == "mode":
        if len(sys.argv) < 3:
            print_usage_and_exit()
        hvac_mode = validate_hvac_mode(sys.argv[2])
        set_air_conditioner_hvac_mode(token, hvac_mode)

    elif command == "temp":
        if len(sys.argv) < 3:
            print_usage_and_exit()
        temperature = validate_temperature(sys.argv[2])
        set_air_conditioner_temperature(token, temperature)

    elif command == "fan":
        if len(sys.argv) < 3:
            print_usage_and_exit()
        fan_mode = validate_fan_mode(sys.argv[2])
        set_air_conditioner_fan_mode(token, fan_mode)

    elif command == "swing":
        if len(sys.argv) < 3:
            print_usage_and_exit()
        swing_mode = validate_swing_mode(sys.argv[2])
        set_air_conditioner_swing_mode(token, swing_mode)

    elif command == "preset":
        if len(sys.argv) < 3:
            print_usage_and_exit()
        preset_mode = validate_preset_mode(sys.argv[2])
        set_air_conditioner_preset_mode(token, preset_mode)

    elif command == "set":
        if len(sys.argv) < 4:
            print_usage_and_exit()
        attributes = parse_set_command_arguments(sys.argv[2:])
        if not attributes:
            print("No attributes specified.", file=sys.stderr)
            raise SystemExit(1)
        apply_air_conditioner_attributes(token, attributes)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print_usage_and_exit()


if __name__ == "__main__":
    main()
