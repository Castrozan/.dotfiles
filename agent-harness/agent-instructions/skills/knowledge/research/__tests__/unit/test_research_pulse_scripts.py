import json
import subprocess
import sys
from pathlib import Path

import pytest

import research_pulse_finalize
import research_pulse_pool
import research_pulse_sources

SCRIPTS_DIRECTORY = Path(research_pulse_sources.__file__).resolve().parent


def run_script(name, *arguments, stdin=""):
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS_DIRECTORY / name), *arguments],
        input=stdin,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return json.loads(completed.stdout)


def test_sources_emit_one_prompt_per_source_with_topic_and_key():
    emitted = run_script(
        "research_pulse_sources.py", "--topic", "tiny models", "--accounts", "a, b"
    )
    keys = ["github", "arxiv", "hackernews", "huggingface", "reddit", "lobsters", "x"]
    assert len(emitted["sources"]) == len(keys)
    for key, prompt in zip(keys, emitted["sources"], strict=True):
        assert '`"tiny models"`' in prompt
        assert prompt.endswith(f'exactly "{key}".')
    assert '`"a, b"`' in emitted["sources"][-1]


def test_sources_fall_back_to_defaults_when_blank():
    emitted = run_script("research_pulse_sources.py", "--topic", " ", "--accounts", ",")
    assert emitted["topic"] == research_pulse_sources.DEFAULT_TOPIC
    assert "steipete, karpathy, simonw" in emitted["sources"][-1]


def test_instruction_data_escapes_backticks():
    assert research_pulse_sources.instruction_data("a`b") == '`"a\\u0060b"`'


def test_pool_tags_items_and_skips_failed_children():
    results = [
        {"source": "arxiv", "items": [{"title": "t", "url": "u", "summary": "s"}]},
        {"archon_failed": True, "error": "boom", "status": "failed"},
        {"source": "x", "items": []},
    ]
    pooled = research_pulse_pool.pool_items(results)
    assert pooled["items"] == [
        {"title": "t", "url": "u", "summary": "s", "source": "arxiv"}
    ]
    assert pooled["itemCount"] == 1
    assert pooled["sourcesHit"] == 2


def test_pool_cli_reads_empty_stdin_as_no_results():
    pooled = run_script("research_pulse_pool.py", stdin="")
    assert pooled == {"items": [], "itemCount": 0, "sourcesHit": 0}


@pytest.mark.parametrize("maximum_items", [0, 1, 2, 5])
def test_top_ranked_sorts_descending_and_truncates(maximum_items):
    ranked = {"items": [{"score": 3}, {"score": 9}, {"score": 5}]}
    top = research_pulse_finalize.top_ranked(ranked, maximum_items)
    scores = [item["score"] for item in top]
    assert scores == sorted([9, 5, 3], reverse=True)[:maximum_items]


def test_select_accepts_skipped_rank_output():
    selected = run_script(
        "research_pulse_finalize.py", "select", "--max-items", "3", stdin=""
    )
    assert selected == {"items": [], "itemCount": 0}


def test_result_without_items_reports_no_items_found():
    payload = {
        "pool": {"itemCount": 0, "sourcesHit": 4},
        "select": {"itemCount": 0},
        "digest": None,
    }
    result = run_script(
        "research_pulse_finalize.py",
        "result",
        "--topic",
        "x",
        stdin=json.dumps(payload),
    )
    assert result["itemCount"] == 0
    assert result["sourcesHit"] == 4
    assert result["digest"].startswith('No items found for "x".')


def test_result_with_items_carries_digest():
    payload = {
        "pool": {"itemCount": 9, "sourcesHit": 6},
        "select": {"itemCount": 5},
        "digest": {"digest": "# hi"},
    }
    result = run_script(
        "research_pulse_finalize.py",
        "result",
        "--topic",
        "x",
        stdin=json.dumps(payload),
    )
    assert result == {"topic": "x", "digest": "# hi", "itemCount": 5, "sourcesHit": 6}
