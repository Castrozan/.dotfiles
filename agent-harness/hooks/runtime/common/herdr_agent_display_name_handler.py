#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import sys
import time

shared_common_hook_modules_directory = os.path.dirname(os.path.realpath(__file__))
if shared_common_hook_modules_directory not in sys.path:
    sys.path.insert(0, shared_common_hook_modules_directory)

from herdr_pane_client import (  # noqa: E402
    ask_herdr,
    belongs_to_a_subagent,
    owned_by_the_clawde_supervisor,
    report_source_for,
    running_inside_a_herdr_pane,
    surrounding_pane_id,
    surrounding_tab_id,
)
from hook_dispatch import requested_hook_surface  # noqa: E402

HERDR_EXPLAIN_AGENT_METHOD = "agent.explain"
HERDR_GET_TAB_METHOD = "tab.get"
HERDR_RENAME_TAB_METHOD = "tab.rename"
HERDR_REPORT_METADATA_METHOD = "pane.report_metadata"

HARNESS_WRITTEN_TITLE_REGION = "osc_title"
LEADING_HARNESS_STATUS_GLYPH = re.compile(r"^[✳✴◐-◓⠀-⣿]+\s*")
TRAILING_PREVIEW_ELLIPSIS = re.compile(r"(\.\.\.|…)$")
COLLAPSIBLE_WHITESPACE = re.compile(r"\s+")
UNNAMED_TAB_LABEL = re.compile(r"^\d+$")

LONGEST_PANE_TITLE = 64
LONGEST_TAB_LABEL = 24


def readable_title(written_title: str) -> str:
    without_status_glyph = LEADING_HARNESS_STATUS_GLYPH.sub("", written_title.strip())
    without_ellipsis = TRAILING_PREVIEW_ELLIPSIS.sub("", without_status_glyph.strip())
    return COLLAPSIBLE_WHITESPACE.sub(" ", without_ellipsis).strip()


def shortened_to(name: str, longest_length: int) -> str:
    if len(name) <= longest_length:
        return name
    clipped_at_a_word_boundary = name[:longest_length].rsplit(" ", 1)[0]
    return (clipped_at_a_word_boundary or name[:longest_length]).rstrip(" ,.;:-")


def title_the_harness_wrote() -> str:
    explanation = ask_herdr(
        HERDR_EXPLAIN_AGENT_METHOD, {"target": surrounding_pane_id()}
    )
    try:
        for evaluated_rule in (explanation or {})["explain"]["evaluated_rules"]:
            if evaluated_rule["region"] == HARNESS_WRITTEN_TITLE_REGION:
                return readable_title(evaluated_rule["evidence"]["region_preview"])
    except (AttributeError, KeyError, TypeError):
        return ""
    return ""


def working_directory_identity(hook_input: dict) -> str:
    working_directory = hook_input.get("cwd")
    if not isinstance(working_directory, str) or not working_directory:
        working_directory = os.getcwd()
    return os.path.basename(working_directory.rstrip("/"))


def report_the_pane_title(pane_title: str, agent_name: str) -> None:
    ask_herdr(
        HERDR_REPORT_METADATA_METHOD,
        {
            "pane_id": surrounding_pane_id(),
            "source": report_source_for(agent_name),
            "agent": agent_name,
            "title": shortened_to(pane_title, LONGEST_PANE_TITLE),
            "seq": time.time_ns(),
        },
    )


def this_agent_is_the_only_occupant_of_an_unnamed_tab(tab_id: str) -> bool:
    tab = (ask_herdr(HERDR_GET_TAB_METHOD, {"tab_id": tab_id}) or {}).get("tab")
    if not isinstance(tab, dict) or tab.get("pane_count") != 1:
        return False
    return bool(UNNAMED_TAB_LABEL.match(str(tab.get("label", ""))))


def name_the_tab_while_it_is_still_unnamed(tab_label: str) -> None:
    tab_id = surrounding_tab_id()
    if not tab_id or not this_agent_is_the_only_occupant_of_an_unnamed_tab(tab_id):
        return
    ask_herdr(
        HERDR_RENAME_TAB_METHOD,
        {"tab_id": tab_id, "label": shortened_to(tab_label, LONGEST_TAB_LABEL)},
    )


def handle(hook_input: dict):
    if belongs_to_a_subagent(hook_input):
        return None
    if owned_by_the_clawde_supervisor():
        return None
    if not running_inside_a_herdr_pane():
        return None
    harness_written_title = title_the_harness_wrote()
    report_the_pane_title(
        harness_written_title or working_directory_identity(hook_input),
        requested_hook_surface(),
    )
    if harness_written_title:
        name_the_tab_while_it_is_still_unnamed(harness_written_title)
    return None
