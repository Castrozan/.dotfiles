#!/usr/bin/env python3

from __future__ import annotations

import json

from reply_format_configuration import REPLY_FORMAT_CONFIGURATION
from reply_restriction_contracts import REPLY_RESTRICTIONS
from reply_text_metrics import ReplyUnderReview


def applicable_restrictions(reply: ReplyUnderReview, user_request: str):
    restrictions = reply.configuration.restrictions
    tokens = reply.document.tokens
    if (
        len(reply.table_first_columns) == 1
        and tokens[0].type == "table_open"
        and tokens[-1].type == "table_close"
    ):
        restrictions = {
            name: rule
            for name, rule in restrictions.items()
            if name == "table_block_length"
        }
    if reply.configuration.table_request_pattern.search(user_request):
        restrictions = {
            name: rule
            for name, rule in restrictions.items()
            if name != "table_block_length"
        }
    return restrictions


def violations_from_rules(reply: ReplyUnderReview, user_request: str) -> list[str]:
    return [
        violation
        for violation in (
            REPLY_RESTRICTIONS[name].evaluate(reply)
            for name in applicable_restrictions(reply, user_request)
        )
        if violation
    ]


def template_violations_in_reply(
    reply_text: str,
    *,
    user_request: str = "",
    configuration=REPLY_FORMAT_CONFIGURATION,
) -> list[str]:
    if structured_json_reply(reply_text):
        return []
    return violations_from_rules(
        ReplyUnderReview(reply_text, configuration), user_request
    )


def structured_json_reply(reply_text):
    if not reply_text.lstrip().startswith(("{", "[")):
        return False
    try:
        json.loads(reply_text, parse_constant=reject_nonfinite_json_constant)
    except (ValueError, RecursionError):
        return False
    return True


def reject_nonfinite_json_constant(value):
    raise ValueError(f"Non-finite JSON constant: {value}")
