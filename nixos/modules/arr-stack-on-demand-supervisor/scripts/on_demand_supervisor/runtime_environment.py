import json
import os
import xml.etree.ElementTree as ElementTree
from datetime import datetime, timezone


def log(message):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"{timestamp} arr-stack-on-demand-supervisor: {message}", flush=True)


def parse_iso8601_to_epoch(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def required_environment_value(name):
    value = os.environ.get(name)
    if value is None or value == "":
        raise SystemExit(f"missing required environment variable {name}")
    return value


def read_arr_bind_address_from_env_file(env_file_path, bind_address_key):
    with open(env_file_path, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith(f"{bind_address_key}="):
                return stripped.split("=", 1)[1]
    raise SystemExit(f"{bind_address_key} not found in {env_file_path}")


def read_jellyseerr_api_key(settings_file_path):
    with open(settings_file_path, encoding="utf-8") as handle:
        return json.load(handle)["main"]["apiKey"]


def read_arr_api_key_from_config_xml(config_xml_path):
    root = ElementTree.parse(config_xml_path).getroot()
    element = root.find("ApiKey")
    if element is None or not (element.text or "").strip():
        raise SystemExit(f"ApiKey not found in {config_xml_path}")
    return element.text.strip()
