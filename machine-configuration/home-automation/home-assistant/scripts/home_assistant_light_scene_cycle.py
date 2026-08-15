import json
import sys
import urllib.request
from pathlib import Path

HOME_ASSISTANT_BASE_URL = "http://localhost:8123"
HOME_ASSISTANT_TOKEN_PATH = Path.home() / ".secrets" / "home-assistant-token"
SCENE_CYCLE_STATE_FILE = Path("/tmp/ha-light-scene-cycle-index")

CYCLED_LIGHT_ENTITY_IDS = [
    "light.bedroom",
    "light.kitchen",
    "light.livingroom",
    "light.bathroom",
]

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
    for entity_id in CYCLED_LIGHT_ENTITY_IDS:
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
