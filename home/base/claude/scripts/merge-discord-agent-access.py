import argparse
import json
import os


def default_access_document():
    return {"dmPolicy": "pairing", "allowFrom": [], "groups": {}, "pending": {}}


def load_existing_or_default(target_access_file):
    if os.path.isfile(target_access_file):
        with open(target_access_file) as target_handle:
            return json.load(target_handle)
    return default_access_document()


def apply_direct_message_allowlist(access_document, dm_policy, allow_from_user_ids):
    access_document["dmPolicy"] = dm_policy
    access_document["allowFrom"] = allow_from_user_ids
    access_document.setdefault("groups", {})
    access_document.setdefault("pending", {})
    return access_document


def write_access_document(target_access_file, access_document):
    os.makedirs(os.path.dirname(target_access_file), exist_ok=True)
    with open(target_access_file, "w") as target_handle:
        json.dump(access_document, target_handle, indent=2)
    os.chmod(target_access_file, 0o600)


def reconcile_direct_message_allowlist(state_directory, dm_policy, allow_from_user_ids):
    target_access_file = os.path.join(state_directory, "access.json")
    access_document = load_existing_or_default(target_access_file)
    apply_direct_message_allowlist(access_document, dm_policy, allow_from_user_ids)
    write_access_document(target_access_file, access_document)


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="merge-discord-agent-access",
        description="Declaratively set a clawde Discord agent's dmPolicy and allowFrom in its access.json while preserving any groups and pending entries the clawde channel merge or runtime pairing manage.",
    )
    parser.add_argument("--state-directory", required=True)
    parser.add_argument("--dm-policy", required=True)
    parser.add_argument("--allow-from-user-id", action="append", default=[])
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    reconcile_direct_message_allowlist(
        arguments.state_directory,
        arguments.dm_policy,
        arguments.allow_from_user_id,
    )


if __name__ == "__main__":
    main()
