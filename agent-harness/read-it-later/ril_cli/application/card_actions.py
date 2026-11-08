from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from application.session_brief import render_session_brief, session_name
from application.session_launch import HerdrSessionLauncher, SessionLaunchFailed
from capture_queue.captures import (
    DEFAULT_CLAIM_EXPIRY_MINUTES,
    capture_ordering_timestamp,
    capture_state,
    read_capture_body,
)
from capture_queue.claims import claim_capture, record_capture_verdict, release_capture
from second_brain.contract import ContractUnreadable, entry_tag_problems, read_contract
from second_brain.entries import link_into_moc, write_entry


@dataclass(frozen=True)
class CardActionContext:
    inbox_directory: Path
    vault_directory: Path
    launcher: HerdrSessionLauncher
    claim_owner: str
    now: datetime


def capture_path(context: CardActionContext, card: dict) -> Path:
    return context.inbox_directory / card["capture"]


def is_done(context: CardActionContext, card: dict) -> bool:
    path = capture_path(context, card)
    state = capture_state(
        read_capture_body(path), DEFAULT_CLAIM_EXPIRY_MINUTES, context.now
    )
    return state == "done"


def claimed(context: CardActionContext, card: dict) -> bool:
    outcome = claim_capture(
        capture_path(context, card),
        context.claim_owner,
        DEFAULT_CLAIM_EXPIRY_MINUTES,
        context.now,
    )
    return outcome in ("claimed", "reclaimed")


def recorded(
    context: CardActionContext, card: dict, outcome: str, entry: str | None = None
) -> dict:
    record_capture_verdict(capture_path(context, card), card["action"], outcome, entry)
    return {"capture": card["capture"], "status": "recorded", "outcome": outcome}


def failed(context: CardActionContext, card: dict, error: Exception) -> dict:
    release_capture(
        capture_path(context, card), DEFAULT_CLAIM_EXPIRY_MINUTES, context.now
    )
    return {"capture": card["capture"], "status": "failed", "reason": str(error)}


def apply_drop(context: CardActionContext, card: dict) -> dict:
    return recorded(context, card, f"dropped: {card['reason']}")


def apply_file(context: CardActionContext, card: dict) -> dict:
    contract = read_contract(context.vault_directory)
    draft = card["entry"]
    problems = entry_tag_problems(draft["tags"], contract)
    if problems:
        raise ContractUnreadable("; ".join(problems))
    captured = (
        capture_ordering_timestamp(capture_path(context, card)).date().isoformat()
    )
    entry_path = write_entry(
        contract, draft, {"source_url": card["origin_url"], "captured": captured}
    )
    link_into_moc(contract, draft["theme_moc"], entry_path.stem, card["tldr"])
    return recorded(
        context,
        card,
        f"filed under {draft['theme_moc']}: {card['reason']}",
        entry_path.stem,
    )


SINGLE_CARD_ACTIONS = {"drop": apply_drop, "file": apply_file}


def apply_single_card(context: CardActionContext, card: dict) -> dict:
    if is_done(context, card):
        return {"capture": card["capture"], "status": "already-done"}
    if not claimed(context, card):
        return {"capture": card["capture"], "status": "held"}
    try:
        return SINGLE_CARD_ACTIONS[card["action"]](context, card)
    except (ContractUnreadable, OSError, KeyError) as error:
        return failed(context, card, error)


def claimed_session_cards(
    context: CardActionContext, cards: list[dict]
) -> tuple[list[dict], list[dict]]:
    pending = [card for card in cards if not is_done(context, card)]
    finished = [
        {"capture": card["capture"], "status": "already-done"}
        for card in cards
        if card not in pending
    ]
    held_by_others = [card for card in pending if not claimed(context, card)]
    finished += [
        {"capture": card["capture"], "status": "held"} for card in held_by_others
    ]
    return [card for card in pending if card not in held_by_others], finished


def apply_session_bundle(
    context: CardActionContext, group: dict, cards: list[dict], pull_request: dict
) -> list[dict]:
    claimed_cards, finished = claimed_session_cards(context, cards)
    if not claimed_cards:
        return finished
    name = session_name(group)
    host = group["session"]["host"]
    try:
        launch_state = context.launcher.launch(
            host, name, render_session_brief(group, cards, pull_request)
        )
    except (SessionLaunchFailed, KeyError, ValueError) as error:
        return finished + [failed(context, card, error) for card in claimed_cards]
    outcome = f"session {name} on {host} ({launch_state})"
    return finished + [recorded(context, card, outcome) for card in claimed_cards]
