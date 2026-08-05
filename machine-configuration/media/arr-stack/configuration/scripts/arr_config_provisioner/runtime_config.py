import json
import os
import re


def required_environment_value(name):
    value = os.environ.get(name)
    if value is None or value == "":
        raise SystemExit(f"missing required environment value {name}")
    return value


def read_bind_address(env_file, bind_address_key):
    with open(env_file, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith(f"{bind_address_key}="):
                return stripped.split("=", 1)[1]
    raise SystemExit(f"{bind_address_key} not found in {env_file}")


def read_app_api_key(config_root, app):
    with open(f"{config_root}/{app}/config.xml", encoding="utf-8") as handle:
        match = re.search(r"<ApiKey>([^<]+)</ApiKey>", handle.read())
    if not match:
        raise RuntimeError(f"no ApiKey element in {app} config.xml")
    return match.group(1)


def read_secret_value(secret_file_path):
    try:
        with open(secret_file_path, encoding="utf-8") as handle:
            return handle.read().strip()
    except FileNotFoundError:
        return ""


def build_secret_map(token_file_pairs):
    return {
        token: read_secret_value(secret_file)
        for token, secret_file in token_file_pairs
        if read_secret_value(secret_file)
    }


def substitute_secrets(value, secret_map):
    if isinstance(value, dict):
        return {
            key: substitute_secrets(item, secret_map) for key, item in value.items()
        }
    if isinstance(value, list):
        return [substitute_secrets(item, secret_map) for item in value]
    if isinstance(value, str) and value in secret_map:
        return secret_map[value]
    return value


def contains_unresolved_secret_token(value):
    if isinstance(value, dict):
        return any(contains_unresolved_secret_token(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_unresolved_secret_token(item) for item in value)
    if isinstance(value, str):
        return bool(re.fullmatch(r"@[A-Z0-9_]+@", value))
    return False


def load_desired_objects(desired_state_dir, app, resource, secret_map):
    with open(f"{desired_state_dir}/{app}/{resource}.json", encoding="utf-8") as handle:
        return substitute_secrets(json.load(handle), secret_map)


def load_optional_desired_objects(desired_state_dir, app, resource, secret_map):
    path = f"{desired_state_dir}/{app}/{resource}.json"
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return substitute_secrets(json.load(handle), secret_map)
