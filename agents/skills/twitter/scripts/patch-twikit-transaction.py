#!/usr/bin/env python3
import re
import sys
from pathlib import Path


def patch_twikit_transaction_regex(venv_path: str):
    transaction_file = Path(venv_path) / "lib/python3.12/site-packages/twikit/x_client_transaction/transaction.py"
    if not transaction_file.exists():
        print(f"[patch] transaction.py not found at {transaction_file}", file=sys.stderr)
        sys.exit(1)

    source = transaction_file.read_text()

    old_on_demand_regex = (
        "ON_DEMAND_FILE_REGEX = re.compile(\n"
        """    r\"\"\"['|\\\"]{1}ondemand\\.s['|\\\"]{1}:\\s*['|\\\"]{1}([\\w]*)['|\\\"]{1}\"\"\", flags=(re.VERBOSE | re.MULTILINE))"""
    )
    new_on_demand_regex = (
        "ON_DEMAND_FILE_REGEX = re.compile(\n"
        """    r\"\"\",(\\d+):[\"']ondemand\\.s[\"']\"\"\", flags=(re.VERBOSE | re.MULTILINE))\n"""
        """ON_DEMAND_HASH_PATTERN = r',{}:\\\"([0-9a-f]+)\\\"'"""
    )

    if old_on_demand_regex in source:
        source = source.replace(old_on_demand_regex, new_on_demand_regex)
        print("[patch] Replaced ON_DEMAND_FILE_REGEX", file=sys.stderr)
    elif "ON_DEMAND_HASH_PATTERN" in source:
        print("[patch] Already patched, skipping", file=sys.stderr)
        return
    else:
        print("[patch] Could not find ON_DEMAND_FILE_REGEX to replace", file=sys.stderr)
        sys.exit(1)

    old_get_indices = (
        '        on_demand_file = ON_DEMAND_FILE_REGEX.search(str(response))\n'
        '        if on_demand_file:\n'
        '            on_demand_file_url = f"https://abs.twimg.com/responsive-web/client-web/ondemand.s.{on_demand_file.group(1)}a.js"'
    )
    new_get_indices = (
        '        response_str = str(response)\n'
        '        on_demand_file = ON_DEMAND_FILE_REGEX.search(response_str)\n'
        '        if on_demand_file:\n'
        '            on_demand_file_index = on_demand_file.group(1)\n'
        '            hash_regex = re.compile(ON_DEMAND_HASH_PATTERN.format(on_demand_file_index))\n'
        '            hash_match = hash_regex.search(response_str)\n'
        '            filename = hash_match.group(1) if hash_match else on_demand_file.group(1)\n'
        '            on_demand_file_url = f"https://abs.twimg.com/responsive-web/client-web/ondemand.s.{filename}a.js"'
    )

    if old_get_indices in source:
        source = source.replace(old_get_indices, new_get_indices)
        print("[patch] Replaced get_indices method", file=sys.stderr)
    else:
        print("[patch] Could not find get_indices to replace", file=sys.stderr)
        sys.exit(1)

    old_indices_regex = (
        "INDICES_REGEX = re.compile(\n"
        """    r\"\"\"(\\(\\w{1}\\[(\\d{1,2})\\],\\s*16\\))+\"\"\", flags=(re.VERBOSE | re.MULTILINE))"""
    )
    new_indices_regex = """INDICES_REGEX = re.compile(r\"\\[(\\d+)\\],\\s*16\")"""

    if old_indices_regex in source:
        source = source.replace(old_indices_regex, new_indices_regex)
        source = source.replace("key_byte_indices.append(item.group(2))", "key_byte_indices.append(item.group(1))")
        print("[patch] Replaced INDICES_REGEX and group reference", file=sys.stderr)

    transaction_file.write_text(source)
    print("[patch] transaction.py patched successfully", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <venv-path>", file=sys.stderr)
        sys.exit(1)
    patch_twikit_transaction_regex(sys.argv[1])
