import sys

import air_conditioner_arguments
from home_assistant_client import (
    make_home_assistant_api_request,
    read_home_assistant_token,
)
from home_assistant_entities import AIR_CONDITIONER_ENTITY_ID


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
        air_conditioner_arguments.print_usage_and_exit()

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
            air_conditioner_arguments.print_usage_and_exit()
        hvac_mode = air_conditioner_arguments.validate_hvac_mode(sys.argv[2])
        set_air_conditioner_hvac_mode(token, hvac_mode)

    elif command == "temp":
        if len(sys.argv) < 3:
            air_conditioner_arguments.print_usage_and_exit()
        temperature = air_conditioner_arguments.validate_temperature(sys.argv[2])
        set_air_conditioner_temperature(token, temperature)

    elif command == "fan":
        if len(sys.argv) < 3:
            air_conditioner_arguments.print_usage_and_exit()
        fan_mode = air_conditioner_arguments.validate_fan_mode(sys.argv[2])
        set_air_conditioner_fan_mode(token, fan_mode)

    elif command == "swing":
        if len(sys.argv) < 3:
            air_conditioner_arguments.print_usage_and_exit()
        swing_mode = air_conditioner_arguments.validate_swing_mode(sys.argv[2])
        set_air_conditioner_swing_mode(token, swing_mode)

    elif command == "preset":
        if len(sys.argv) < 3:
            air_conditioner_arguments.print_usage_and_exit()
        preset_mode = air_conditioner_arguments.validate_preset_mode(sys.argv[2])
        set_air_conditioner_preset_mode(token, preset_mode)

    elif command == "set":
        if len(sys.argv) < 4:
            air_conditioner_arguments.print_usage_and_exit()
        attributes = air_conditioner_arguments.parse_set_command_arguments(sys.argv[2:])
        if not attributes:
            print("No attributes specified.", file=sys.stderr)
            raise SystemExit(1)
        apply_air_conditioner_attributes(token, attributes)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        air_conditioner_arguments.print_usage_and_exit()


if __name__ == "__main__":
    main()
