from pathlib import Path

from home_assistant_client import (
    make_home_assistant_api_request,
    read_home_assistant_token,
)
from home_assistant_entities import ALL_LIGHT_ENTITY_IDS

SCENE_CYCLE_STATE_FILE = Path("/tmp/ha-light-scene-cycle-index")

MINIMUM_COLOR_TEMPERATURE_KELVIN = 2000
MAXIMUM_COLOR_TEMPERATURE_KELVIN = 6500
MAXIMUM_BRIGHTNESS = 255

# Each step drives the lights directly rather than activating a scene.* entity.
# The Tuya scenes this cycle used to call carry no targets, so scene/turn_on
# returned success and changed nothing. Brightness uses the Home Assistant
# 0-255 scale; temperature is Kelvin inside the range the bulbs report.
LIGHT_SCENE_CYCLE_STEPS = [
    {"name": "low_warm", "brightness": 64, "color_temp_kelvin": 2000},
    {"name": "half_half", "brightness": 128, "color_temp_kelvin": 4250},
    {"name": "70_70", "brightness": 179, "color_temp_kelvin": 5150},
    {"name": "high_warm", "brightness": 255, "color_temp_kelvin": 2000},
]


def read_current_scene_cycle_index() -> int:
    if SCENE_CYCLE_STATE_FILE.is_file():
        try:
            return int(SCENE_CYCLE_STATE_FILE.read_text().strip())
        except (ValueError, OSError):
            return -1
    return -1


def write_scene_cycle_index(index: int) -> None:
    SCENE_CYCLE_STATE_FILE.write_text(str(index))


def apply_light_scene_cycle_step(token: str, step: dict) -> None:
    for entity_id in ALL_LIGHT_ENTITY_IDS:
        make_home_assistant_api_request(
            token,
            "/api/services/light/turn_on",
            {
                "entity_id": entity_id,
                "brightness": step["brightness"],
                "color_temp_kelvin": step["color_temp_kelvin"],
            },
        )


def main() -> None:
    token = read_home_assistant_token()
    current_index = read_current_scene_cycle_index()
    next_index = (current_index + 1) % len(LIGHT_SCENE_CYCLE_STEPS)
    step = LIGHT_SCENE_CYCLE_STEPS[next_index]
    apply_light_scene_cycle_step(token, step)
    write_scene_cycle_index(next_index)
    print(step["name"])


if __name__ == "__main__":
    main()
