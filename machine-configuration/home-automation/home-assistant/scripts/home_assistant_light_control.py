import sys

from home_assistant_client import (
    make_home_assistant_api_request,
    read_home_assistant_token,
)
from home_assistant_entities import ALL_LIGHT_ENTITY_IDS

MINIMUM_COLOR_TEMPERATURE_KELVIN = 2000
MAXIMUM_COLOR_TEMPERATURE_KELVIN = 6500
MAXIMUM_BRIGHTNESS = 255


def resolve_target_entity_ids(target_name: str) -> list[str]:
    if target_name == "all":
        return list(ALL_LIGHT_ENTITY_IDS)
    entity_id = f"light.{target_name}"
    if entity_id not in ALL_LIGHT_ENTITY_IDS:
        available = [eid.split(".")[1] for eid in ALL_LIGHT_ENTITY_IDS]
        joined = ", ".join(available)
        print(
            f"Unknown light '{target_name}'. Available: {joined}, all",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return [entity_id]


def turn_on_lights(token: str, entity_ids: list[str], extra_attributes: dict) -> None:
    for entity_id in entity_ids:
        payload = {"entity_id": entity_id}
        payload.update(extra_attributes)
        make_home_assistant_api_request(token, "/api/services/light/turn_on", payload)
        print(f"{entity_id}: on")


def turn_off_lights(token: str, entity_ids: list[str]) -> None:
    for entity_id in entity_ids:
        make_home_assistant_api_request(
            token,
            "/api/services/light/turn_off",
            {"entity_id": entity_id},
        )
        print(f"{entity_id}: off")


def get_light_states(token: str, entity_ids: list[str]) -> None:
    for entity_id in entity_ids:
        result = make_home_assistant_api_request(token, f"/api/states/{entity_id}")
        if result is None:
            print(f"{entity_id}: error fetching state", file=sys.stderr)
            continue
        state = result.get("state", "unknown")
        attributes = result.get("attributes", {})
        brightness = attributes.get("brightness", "N/A")
        color_temp_kelvin = attributes.get("color_temp_kelvin", "N/A")
        friendly_name = attributes.get("friendly_name", entity_id)
        status_line = (
            f"{friendly_name}: state={state}"
            f" brightness={brightness} temp={color_temp_kelvin}K"
        )
        print(status_line)


def activate_scene(token: str, scene_name: str) -> None:
    entity_id = f"scene.{scene_name}"
    make_home_assistant_api_request(
        token, "/api/services/scene/turn_on", {"entity_id": entity_id}
    )
    print(f"{entity_id}: activated")


def parse_brightness_argument(value_string: str) -> int:
    value = int(value_string)
    if value < 0 or value > MAXIMUM_BRIGHTNESS:
        print(
            f"Brightness must be 0-{MAXIMUM_BRIGHTNESS}, got {value}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return value


def parse_color_temperature_argument(value_string: str) -> int:
    value = int(value_string)
    if (
        value < MINIMUM_COLOR_TEMPERATURE_KELVIN
        or value > MAXIMUM_COLOR_TEMPERATURE_KELVIN
    ):
        min_k = MINIMUM_COLOR_TEMPERATURE_KELVIN
        max_k = MAXIMUM_COLOR_TEMPERATURE_KELVIN
        print(
            f"Color temperature must be {min_k}-{max_k}K, got {value}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return value


def print_usage_and_exit() -> None:
    print(
        "Usage: ha-light <command> [target] [options]\n"
        "\n"
        "Commands:\n"
        "  on    <target> [--brightness N] [--temp N]  Turn on light(s)\n"
        "  off   <target>                              Turn off light(s)\n"
        "  set   <target> --brightness N [--temp N]    Set light attributes\n"
        "  status [target]                             Show light state(s)\n"
        "  scene <name>                                Activate a Tuya scene\n"
        "\n"
        "Targets: bedroom, kitchen, livingroom, bathroom, all",
        file=sys.stderr,
    )
    raise SystemExit(1)


def parse_optional_attributes_from_arguments(arguments: list[str]) -> dict:
    attributes = {}
    index = 0
    while index < len(arguments):
        if arguments[index] == "--brightness" and index + 1 < len(arguments):
            attributes["brightness"] = parse_brightness_argument(arguments[index + 1])
            index += 2
        elif arguments[index] == "--temp" and index + 1 < len(arguments):
            attributes["color_temp_kelvin"] = parse_color_temperature_argument(
                arguments[index + 1]
            )
            index += 2
        else:
            print(f"Unknown option: {arguments[index]}", file=sys.stderr)
            raise SystemExit(1)
    return attributes


def handle_light_mutation_command(command: str, token: str) -> bool:
    if command in ("on", "off", "set"):
        execute_light_mutation(command, token)
        return True
    return False


def execute_light_mutation(command: str, token: str) -> None:
    minimum_argument_count = 4 if command == "set" else 3
    if len(sys.argv) < minimum_argument_count:
        print_usage_and_exit()
    entity_ids = resolve_target_entity_ids(sys.argv[2])
    if command == "off":
        turn_off_lights(token, entity_ids)
        return

    extra_attributes = parse_optional_attributes_from_arguments(sys.argv[3:])
    require_light_mutation_attributes(command, extra_attributes)
    turn_on_lights(token, entity_ids, extra_attributes)


def require_light_mutation_attributes(command: str, attributes: dict) -> None:
    if command == "set" and not attributes:
        print(
            "No attributes specified. Use --brightness and/or --temp",
            file=sys.stderr,
        )
        raise SystemExit(1)


def handle_light_query_command(command: str, token: str) -> bool:
    if command == "status":
        target = sys.argv[2] if len(sys.argv) > 2 else "all"
        entity_ids = resolve_target_entity_ids(target)
        get_light_states(token, entity_ids)
    elif command == "scene":
        if len(sys.argv) < 3:
            print_usage_and_exit()
        activate_scene(token, sys.argv[2])
    else:
        return False
    return True


def main() -> None:
    if len(sys.argv) < 2:
        print_usage_and_exit()

    command = sys.argv[1]
    token = read_home_assistant_token()
    if handle_light_mutation_command(command, token):
        return
    if handle_light_query_command(command, token):
        return
    print(f"Unknown command: {command}", file=sys.stderr)
    print_usage_and_exit()


if __name__ == "__main__":
    main()
