import json
import sys
import urllib.request
from pathlib import Path

HOME_ASSISTANT_BASE_URL = "http://localhost:8123"
HOME_ASSISTANT_TOKEN_PATH = Path.home() / ".secrets" / "home-assistant-token"
SCENE_CYCLE_STATE_FILE = Path("/tmp/ha-light-scene-cycle-index")

SCENE_CYCLE_ORDER = [
    "low_warm",
    "half_half",
    "70_70",
    "high_warm",
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


def main() -> None:
    token = read_home_assistant_token()
    current_index = read_current_scene_cycle_index()
    next_index = (current_index + 1) % len(SCENE_CYCLE_ORDER)
    scene_name = SCENE_CYCLE_ORDER[next_index]
    entity_id = f"scene.{scene_name}"
    make_home_assistant_api_request(
        token, "/api/services/scene/turn_on", {"entity_id": entity_id}
    )
    write_scene_cycle_index(next_index)
    print(f"{scene_name}")


if __name__ == "__main__":
    main()
