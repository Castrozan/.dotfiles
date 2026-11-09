import argparse
import json

import pytest

from archon_provider_receipt import build_receipt, descriptor_from_initialize_response

DESCRIPTOR = {"protocol": 3, "id": "claude", "version": "0.14.0"}
ARGUMENTS = argparse.Namespace(
    provider_identifier="claude",
    display_name="Claude",
    release_tag="v0.14.0",
    release_commit="8def159a6b2c23e832a5283b4131cfffd9af9344",
    installed_at_epoch=1794041828,
)


def test_the_descriptor_comes_from_the_initialize_reply_amid_log_lines():
    reply = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"agentCapabilities": {"_meta": {"archon": DESCRIPTOR}}},
    }
    lines = ["starting", json.dumps({"method": "_archon/log"}), json.dumps(reply)]
    assert descriptor_from_initialize_response(lines) == DESCRIPTOR


def test_a_silent_provider_is_refused():
    with pytest.raises(SystemExit, match="no initialize response"):
        descriptor_from_initialize_response(["not json"])


def test_the_receipt_names_the_maintained_plugin_and_its_digest():
    receipt = build_receipt(ARGUMENTS, DESCRIPTOR, "ab" * 32)
    assert receipt["id"] == "coleam00/Archon/plugins/provider-claude"
    assert receipt["manifest"]["executable"] == "archon-provider-claude"
    assert receipt["files"] == [{"path": "archon-provider-claude", "sha256": "ab" * 32}]
    assert receipt["installedAt"] == "2026-11-07T08:57:08.000Z"
    assert receipt["descriptor"] == DESCRIPTOR


def test_a_binary_describing_another_provider_is_refused():
    with pytest.raises(SystemExit, match="describes provider 'codex'"):
        build_receipt(ARGUMENTS, {**DESCRIPTOR, "id": "codex"}, "ab" * 32)
