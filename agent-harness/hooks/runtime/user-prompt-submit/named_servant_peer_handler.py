#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from collections import Counter

from servant_identity_handler import servant_for_hook_input
from catalog import SERVANT_CATALOG  # noqa: E402
from hook_dispatch import HandlerResult  # noqa: E402

PEER_DIRECTORY_COMMAND = ("a2a", "list", "--json")
PEER_DIRECTORY_TIMEOUT_SECONDS = 1.0
NON_WORD_RUN = re.compile(r"[\W_]+")


def searchable_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return f" {NON_WORD_RUN.sub(' ', without_marks).casefold().strip()} "


SEARCHABLE_CATALOG_NAMES = tuple(
    searchable_text(servant["name"]) for servant in SERVANT_CATALOG
)


def prompt_names_any_servant(searchable_prompt: str) -> bool:
    return any(name in searchable_prompt for name in SEARCHABLE_CATALOG_NAMES)


def live_peer_directory() -> dict:
    try:
        completed = subprocess.run(
            PEER_DIRECTORY_COMMAND,
            capture_output=True,
            text=True,
            check=False,
            timeout=PEER_DIRECTORY_TIMEOUT_SECONDS,
        )
        directory = json.loads(completed.stdout) if completed.returncode == 0 else {}
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return {}
    return directory if isinstance(directory, dict) else {}


def named_peers(searchable_prompt: str, directory: dict, own_servant: str) -> list:
    return [
        peer
        for peer in directory.values()
        if peer.get("servant")
        and peer["servant"] != own_servant
        and searchable_text(peer["servant"]) in searchable_prompt
    ]


def peer_context_line(peer: dict, servant_holders: Counter) -> str:
    target = peer["servant"] if servant_holders[peer["servant"]] == 1 else peer["name"]
    return (
        f"Servant {peer['servant']} is the live a2a peer {peer['name']} "
        f"({peer['harness']}, pane {peer['paneId']}). "
        f'Reach it with: a2a ask "{target}" "<task>"'
    )


def handle(hook_input: dict):
    own_servant = servant_for_hook_input(hook_input)
    if own_servant is None:
        return None
    searchable_prompt = searchable_text(str(hook_input.get("prompt", "")))
    if not prompt_names_any_servant(searchable_prompt):
        return None
    peers = named_peers(searchable_prompt, live_peer_directory(), own_servant["name"])
    if not peers:
        return None
    servant_holders = Counter(peer["servant"] for peer in peers)
    return HandlerResult(
        additional_context="\n".join(
            peer_context_line(peer, servant_holders) for peer in peers
        )
    )
