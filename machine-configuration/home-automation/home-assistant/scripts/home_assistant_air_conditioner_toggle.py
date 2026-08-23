import subprocess
import sys
import time

from home_assistant_client import (
    make_home_assistant_api_request,
    read_home_assistant_token,
)
from home_assistant_entities import AIR_CONDITIONER_ENTITY_ID


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
