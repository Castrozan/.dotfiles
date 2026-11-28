import json
import os
import platform

from jsonschema import Draft202012Validator

from agent_api.contract import CapabilityError

LOCAL_HOST = "local"
INVENTORY_VARIABLE = "AGENT_API_COMPUTE_INVENTORY"
NIX_ARCHITECTURES = {"arm64": "aarch64"}
HOST_NAME = {"type": "string", "pattern": "^[a-z][a-z0-9-]{0,62}$"}
INVENTORY_SCHEMA = {
    "type": "object",
    "properties": {
        "self": HOST_NAME,
        "hosts": {
            "type": "array",
            "maxItems": 32,
            "items": {
                "type": "object",
                "properties": {
                    "name": {**HOST_NAME, "not": {"const": LOCAL_HOST}},
                    "ssh_alias": {
                        "type": "string",
                        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,252}$",
                    },
                    "system": {"type": "string", "pattern": "^[a-z0-9_]+-[a-z]+$"},
                    "cores": {"type": "integer", "minimum": 1},
                    "memory_gigabytes": {"type": "integer", "minimum": 1},
                    "trust": {"enum": ["owned", "rented"]},
                },
                "required": ["name", "trust"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["self", "hosts"],
    "additionalProperties": False,
}


def local_host():
    machine = platform.machine()
    return {
        "name": LOCAL_HOST,
        "transport": "local",
        "system": f"{NIX_ARCHITECTURES.get(machine, machine)}-{platform.system().lower()}",
        "cores": os.cpu_count(),
        "trust": "owned",
    }


def load_inventory():
    inventory_path = os.environ.get(INVENTORY_VARIABLE)
    if not inventory_path:
        return {"self": LOCAL_HOST, "hosts": []}
    with open(inventory_path, "rb") as stream:
        try:
            inventory = json.load(stream)
        except (ValueError, UnicodeError):
            raise CapabilityError("invalid_inventory") from None
    if next(Draft202012Validator(INVENTORY_SCHEMA).iter_errors(inventory), None):
        raise CapabilityError("invalid_inventory")
    names = [entry["name"] for entry in inventory["hosts"]]
    if len(set(names)) != len(names):
        raise CapabilityError("invalid_inventory")
    return inventory


def self_name():
    return load_inventory()["self"]


def hosts():
    inventory = load_inventory()
    return [
        local_host(),
        *(
            {
                "ssh_alias": entry["name"],
                **entry,
                "transport": "local" if entry["name"] == inventory["self"] else "ssh",
            }
            for entry in inventory["hosts"]
        ),
    ]


def host(name):
    entry = next((entry for entry in hosts() if entry["name"] == name), None)
    if entry is None:
        raise CapabilityError("unsupported_host")
    return entry
