import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HOME_ASSISTANT_BASE_URL = "http://localhost:8123"
HOME_ASSISTANT_TOKEN_PATH = Path.home() / ".secrets" / "home-assistant-token"
AIR_CONDITIONER_ENTITY_ID = "climate.150633094104375_climate"


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


def get_current_air_conditioner_state(token: str) -> str:
    result = make_home_assistant_api_request(
        token, f"/api/states/{AIR_CONDITIONER_ENTITY_ID}"
    )
    if result is None:
        return "off"
    return result.get("state", "off")


RECOVERY_WAIT_SECONDS = 3


def attempt_air_conditioner_recovery() -> bool:
    result = subprocess.run(
        ["ha-ac-recover-ip"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    time.sleep(RECOVERY_WAIT_SECONDS)
    return True


def toggle_air_conditioner(token: str, current_state: str) -> None:
    if current_state == "off":
        make_home_assistant_api_request(
            token,
            "/api/services/climate/turn_on",
            {"entity_id": AIR_CONDITIONER_ENTITY_ID},
        )
        print("air conditioner: on")
    else:
        make_home_assistant_api_request(
            token,
            "/api/services/climate/turn_off",
            {"entity_id": AIR_CONDITIONER_ENTITY_ID},
        )
        print("air conditioner: off")


def main() -> None:
    token = read_home_assistant_token()
    current_state = get_current_air_conditioner_state(token)

    if current_state == "unavailable":
        recovered = attempt_air_conditioner_recovery()
        if not recovered:
            print("air conditioner: unavailable", file=sys.stderr)
            raise SystemExit(1)
        current_state = get_current_air_conditioner_state(token)
        if current_state == "unavailable":
            print("air conditioner: unavailable", file=sys.stderr)
            raise SystemExit(1)

    toggle_air_conditioner(token, current_state)


if __name__ == "__main__":
    main()
