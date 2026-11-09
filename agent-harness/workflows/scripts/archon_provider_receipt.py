import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ARCHON_PROTOCOL_VERSION = 3
MAINTAINED_PROVIDER_REPOSITORY = "coleam00/Archon/plugins"
INITIALIZE_REQUEST = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": 1,
        "clientCapabilities": {
            "fs": {"readTextFile": False, "writeTextFile": False},
            "terminal": False,
            "_meta": {"archon": {"protocol": ARCHON_PROTOCOL_VERSION}},
        },
    },
}
HANDSHAKE_TIMEOUT_SECONDS = 60


def parse_command_line(command_line_arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Write the install receipt Archon reads for a provider plugin placed "
            "outside its own installer."
        )
    )
    parser.add_argument("--provider-binary", required=True, type=Path)
    parser.add_argument("--provider-identifier", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--release-tag", required=True)
    parser.add_argument("--release-commit", required=True)
    parser.add_argument("--installed-at-epoch", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(command_line_arguments)


def descriptor_from_initialize_response(response_lines: list[str]) -> dict:
    for response_line in response_lines:
        try:
            message = json.loads(response_line)
        except json.JSONDecodeError:
            continue
        if message.get("id") != INITIALIZE_REQUEST["id"]:
            continue
        if "error" in message:
            raise SystemExit(f"initialize was refused: {message['error']}")
        return message["result"]["agentCapabilities"]["_meta"]["archon"]
    raise SystemExit("the provider answered no initialize response")


def read_provider_descriptor(provider_binary: Path) -> dict:
    handshake = subprocess.run(
        [str(provider_binary)],
        input=json.dumps(INITIALIZE_REQUEST) + "\n",
        capture_output=True,
        text=True,
        timeout=HANDSHAKE_TIMEOUT_SECONDS,
        check=False,
    )
    return descriptor_from_initialize_response(handshake.stdout.splitlines())


def build_receipt(
    arguments: argparse.Namespace, descriptor: dict, binary_digest: str
) -> dict:
    executable_name = f"archon-provider-{arguments.provider_identifier}"
    if descriptor.get("id") != arguments.provider_identifier:
        raise SystemExit(
            f"the binary describes provider {descriptor.get('id')!r}, "
            f"not {arguments.provider_identifier!r}"
        )
    installed_at = datetime.fromtimestamp(
        arguments.installed_at_epoch, tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return {
        "schemaVersion": 1,
        "id": f"{MAINTAINED_PROVIDER_REPOSITORY}/provider-{arguments.provider_identifier}",
        "manifest": {
            "schemaVersion": 1,
            "kind": "provider",
            "name": f"provider-{arguments.provider_identifier}",
            "description": f"Archon maintained {arguments.display_name} provider.",
            "executable": executable_name,
        },
        "tag": arguments.release_tag,
        "commit": arguments.release_commit,
        "installedAt": installed_at,
        "files": [{"path": executable_name, "sha256": binary_digest}],
        "descriptor": descriptor,
    }


def main() -> int:
    arguments = parse_command_line(sys.argv[1:])
    descriptor = read_provider_descriptor(arguments.provider_binary)
    binary_digest = hashlib.sha256(arguments.provider_binary.read_bytes()).hexdigest()
    receipt = build_receipt(arguments, descriptor, binary_digest)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(receipt, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
