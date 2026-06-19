import argparse
import json
import os
import re


def parse_channel_ids(raw_text):
    return [token for token in re.split(r"[\s,]+", raw_text.strip()) if token.isdigit()]


def default_access_document():
    return {"dmPolicy": "pairing", "allowFrom": [], "groups": {}, "pending": {}}


def load_access_document(target_access_file, shared_access_file):
    if os.path.isfile(target_access_file):
        with open(target_access_file) as target_handle:
            return json.load(target_handle)
    if shared_access_file and os.path.isfile(shared_access_file):
        with open(shared_access_file) as shared_handle:
            return json.load(shared_handle)
    return default_access_document()


def read_declared_channel_ids(channels_secret_file):
    if not channels_secret_file or not os.path.isfile(channels_secret_file):
        return []
    with open(channels_secret_file) as secret_handle:
        return parse_channel_ids(secret_handle.read())


def ensure_channels_present(access_document, channel_ids):
    groups = access_document.setdefault("groups", {})
    for channel_id in channel_ids:
        if channel_id not in groups:
            groups[channel_id] = {"requireMention": False, "allowFrom": []}


def write_access_document(target_access_file, access_document):
    os.makedirs(os.path.dirname(target_access_file), exist_ok=True)
    with open(target_access_file, "w") as target_handle:
        json.dump(access_document, target_handle, indent=2)
    os.chmod(target_access_file, 0o600)


def reconcile_agent_access(state_directory, shared_access_file, channels_secret_file):
    target_access_file = os.path.join(state_directory, "access.json")
    access_document = load_access_document(target_access_file, shared_access_file)
    ensure_channels_present(
        access_document, read_declared_channel_ids(channels_secret_file)
    )
    write_access_document(target_access_file, access_document)


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="merge-discord-channel-access",
        description="Reconcile a clawde agent's per-agent Discord access.json, migrating from the shared file when absent and merging declared channel ids without clobbering existing entries",
    )
    parser.add_argument("--state-directory", required=True)
    parser.add_argument("--shared-access-file", default=None)
    parser.add_argument("--channels-secret-file", default=None)
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    reconcile_agent_access(
        arguments.state_directory,
        arguments.shared_access_file,
        arguments.channels_secret_file,
    )


if __name__ == "__main__":
    main()
