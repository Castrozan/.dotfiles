#!/usr/bin/env python3

from __future__ import annotations

from reply_rule_violations import unlinked_artifact_violation
from reply_text_metrics import ReplyUnderReview


class HumanFacingReplyRule:
    def __init__(self, name: str, violation_of):
        self.name = name
        self.violation_of = violation_of


HUMAN_FACING_REPLY_RULES = [
    HumanFacingReplyRule("unlinked_artifact", unlinked_artifact_violation),
]


def violations_from_rules(reply: ReplyUnderReview) -> list[str]:
    return [
        violation
        for violation in (rule.violation_of(reply) for rule in HUMAN_FACING_REPLY_RULES)
        if violation
    ]


def template_violations_in_reply(
    reply_text: str, user_request_text: str = ""
) -> list[str]:
    return violations_from_rules(ReplyUnderReview(reply_text))
