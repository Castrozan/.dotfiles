#!/usr/bin/env python3

from __future__ import annotations

from reply_format_configuration import REPLY_FORMAT_CONFIGURATION
from reply_restriction_contracts import REPLY_RESTRICTIONS
from reply_text_metrics import ReplyUnderReview


def violations_from_rules(reply: ReplyUnderReview) -> list[str]:
    return [
        violation
        for violation in (
            REPLY_RESTRICTIONS[name].evaluate(reply)
            for name in reply.configuration.restrictions
        )
        if violation
    ]


def template_violations_in_reply(
    reply_text: str,
    *,
    configuration=REPLY_FORMAT_CONFIGURATION,
) -> list[str]:
    return violations_from_rules(ReplyUnderReview(reply_text, configuration))
