import hashlib
import re
from dataclasses import dataclass

AUTH_SECTION_HEADER = re.compile(r"^auth:\s*$")
TOP_LEVEL_KEY = re.compile(r"^\S")
AUTH_CHILD_KEY = re.compile(r"^(?P<indent>\s+)(?P<key>[A-Za-z0-9_]+):(?P<rest>.*)$")
LOGIN_KEYS = ("type", "username", "password")


@dataclass
class AuthEditState:
    desired_values: dict
    result_lines: list
    written_keys: set
    block_indent: str = "  "
    inside_auth: bool = False


def md5_hex(plaintext):
    return hashlib.md5(plaintext.encode("utf-8")).hexdigest()


def unquote_scalar(rest):
    value = rest.strip()
    if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
        return value[1:-1]
    return value


def parse_auth_block(config_lines):
    auth_values = {}
    inside_auth = False
    for line in config_lines:
        inside_auth, should_continue = _parse_auth_block_line(
            line, auth_values, inside_auth
        )
        if not should_continue:
            break
    return auth_values


def _parse_auth_block_line(line, auth_values, inside_auth):
    if AUTH_SECTION_HEADER.match(line):
        return True, True
    if not inside_auth:
        return False, True
    if TOP_LEVEL_KEY.match(line):
        return False, False
    match = AUTH_CHILD_KEY.match(line)
    if match:
        auth_values[match.group("key")] = unquote_scalar(match.group("rest"))
    return inside_auth, True


def auth_already_matches(auth_values, username, password_hash):
    return (
        auth_values.get("type") == "form"
        and auth_values.get("username") == username
        and auth_values.get("password") == password_hash
    )


def apply_forms_login(config_lines, username, password_hash):
    desired_values = {"type": "form", "username": username, "password": password_hash}
    state = AuthEditState(desired_values, [], set())

    def emit_missing_login_keys():
        for key in LOGIN_KEYS:
            if key not in state.written_keys:
                state.result_lines.append(
                    f"{state.block_indent}{key}: {state.desired_values[key]}"
                )
                state.written_keys.add(key)

    for line in config_lines:
        _append_auth_config_line(line, state, emit_missing_login_keys)

    if state.inside_auth:
        emit_missing_login_keys()
    if not state.written_keys:
        state.result_lines.append("auth:")
        for key in LOGIN_KEYS:
            state.result_lines.append(f"  {key}: {state.desired_values[key]}")
    return state.result_lines


def _append_auth_config_line(line, state, emit_missing_login_keys):
    if AUTH_SECTION_HEADER.match(line):
        state.inside_auth = True
        state.result_lines.append(line)
        return
    if state.inside_auth and TOP_LEVEL_KEY.match(line):
        emit_missing_login_keys()
        state.inside_auth = False
        state.result_lines.append(line)
        return
    if state.inside_auth:
        _append_auth_child_config_line(line, state)
        return
    state.result_lines.append(line)


def _append_auth_child_config_line(line, state):
    match = AUTH_CHILD_KEY.match(line)
    if not match:
        state.result_lines.append(line)
        return
    state.block_indent = match.group("indent")
    key = match.group("key")
    if key not in state.desired_values:
        state.result_lines.append(line)
        return
    state.result_lines.append(f"{state.block_indent}{key}: {state.desired_values[key]}")
    state.written_keys.add(key)
