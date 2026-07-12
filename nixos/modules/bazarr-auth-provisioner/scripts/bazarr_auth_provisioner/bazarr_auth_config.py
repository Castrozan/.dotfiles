import hashlib
import re

AUTH_SECTION_HEADER = re.compile(r"^auth:\s*$")
TOP_LEVEL_KEY = re.compile(r"^\S")
AUTH_CHILD_KEY = re.compile(r"^(?P<indent>\s+)(?P<key>[A-Za-z0-9_]+):(?P<rest>.*)$")
LOGIN_KEYS = ("type", "username", "password")


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
        if AUTH_SECTION_HEADER.match(line):
            inside_auth = True
            continue
        if inside_auth and TOP_LEVEL_KEY.match(line):
            break
        if inside_auth:
            match = AUTH_CHILD_KEY.match(line)
            if match:
                auth_values[match.group("key")] = unquote_scalar(match.group("rest"))
    return auth_values


def auth_already_matches(auth_values, username, password_hash):
    return (
        auth_values.get("type") == "form"
        and auth_values.get("username") == username
        and auth_values.get("password") == password_hash
    )


def apply_forms_login(config_lines, username, password_hash):
    desired_values = {"type": "form", "username": username, "password": password_hash}
    result_lines = []
    inside_auth = False
    block_indent = "  "
    written_keys = set()

    def emit_missing_login_keys():
        for key in LOGIN_KEYS:
            if key not in written_keys:
                result_lines.append(f"{block_indent}{key}: {desired_values[key]}")
                written_keys.add(key)

    for line in config_lines:
        if AUTH_SECTION_HEADER.match(line):
            inside_auth = True
            result_lines.append(line)
            continue
        if inside_auth and TOP_LEVEL_KEY.match(line):
            emit_missing_login_keys()
            inside_auth = False
            result_lines.append(line)
            continue
        if inside_auth:
            match = AUTH_CHILD_KEY.match(line)
            if match:
                block_indent = match.group("indent")
                key = match.group("key")
                if key in desired_values:
                    result_lines.append(f"{block_indent}{key}: {desired_values[key]}")
                    written_keys.add(key)
                    continue
            result_lines.append(line)
            continue
        result_lines.append(line)

    if inside_auth:
        emit_missing_login_keys()
    if not written_keys:
        result_lines.append("auth:")
        for key in LOGIN_KEYS:
            result_lines.append(f"  {key}: {desired_values[key]}")
    return result_lines
