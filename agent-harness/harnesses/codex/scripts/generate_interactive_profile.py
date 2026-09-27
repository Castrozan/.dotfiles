import json
from pathlib import Path
import sys
import tomllib

import tomli_w


def generate_interactive_profile(
    instructions: str, configuration_overrides: dict[str, str]
) -> bytes:
    configuration = {}
    for key, raw_value in configuration_overrides.items():
        try:
            value = tomllib.loads(f"value = {raw_value}")["value"]
        except tomllib.TOMLDecodeError:
            value = raw_value
        table = configuration
        key_parts = key.split(".")
        for parent_key in key_parts[:-1]:
            table = table.setdefault(parent_key, {})
        table[key_parts[-1]] = value
    configuration.setdefault("developer_instructions", instructions)
    return tomli_w.dumps(configuration).encode()


if __name__ == "__main__":
    instructions_path, overrides_path, output_path = map(Path, sys.argv[1:])
    output_path.write_bytes(
        generate_interactive_profile(
            instructions_path.read_text(), json.loads(overrides_path.read_text())
        )
    )
