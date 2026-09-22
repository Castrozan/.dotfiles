import copy
import json

import pytest

from human_facing_reply_test_support import (
    REPLY_RULE_MODULE_DIRECTORY,
    labeled_reply_of,
)
from reply_format_configuration import ReplyFormatConfiguration
from reply_rule_catalog import template_violations_in_reply


@pytest.fixture
def configuration_document():
    return json.loads((REPLY_RULE_MODULE_DIRECTORY / "reply-formats.json").read_text())


def test_configured_confirmation_budget_changes_the_verdict(configuration_document):
    configuration_document["formats"]["confirmation"] = {
        "maximum_words": 5,
        "grace_words": 2,
    }
    configuration = ReplyFormatConfiguration(configuration_document)

    assert template_violations_in_reply("word " * 7, configuration=configuration) == []
    assert (
        "5-word confirmation"
        in template_violations_in_reply("word " * 8, configuration=configuration)[0]
    )


def test_configured_list_exemption_and_item_grace_change_the_verdict(
    configuration_document,
):
    configuration_document["lists"].update(
        maximum_exempt_items=2, item={"maximum_words": 2, "grace_words": 1}
    )
    configuration = ReplyFormatConfiguration(configuration_document)
    reply = "- one two\n- one two\n\n" + labeled_reply_of(80)

    assert template_violations_in_reply(reply, configuration=configuration) == []
    violations = template_violations_in_reply(
        reply.replace("- one two", "- one two three", 1), configuration=configuration
    )
    assert any(
        "2-word ceiling and its 1-word grace" in violation for violation in violations
    )


def test_configured_label_names_and_budgets_are_used(configuration_document):
    configuration_document["formats"]["confirmation"]["maximum_words"] = 0
    configuration_document["formats"]["confirmation"]["grace_words"] = 0
    configuration_document["formats"]["labeled_reply"]["labels"] = [
        {
            "name": "Result",
            "maximum_words": 2,
            "grace_words": 1,
            "instruction": "State the result.",
        }
    ]
    configuration = ReplyFormatConfiguration(configuration_document)

    assert (
        template_violations_in_reply("**Result:** one two", configuration=configuration)
        == []
    )
    assert (
        "Result:"
        in template_violations_in_reply("missing label", configuration=configuration)[0]
    )
    assert (
        "2-word budget and its 1-word grace"
        in template_violations_in_reply(
            "**Result:** one two three", configuration=configuration
        )[0]
    )


def test_configured_patterns_and_active_restrictions_are_used(configuration_document):
    configuration_document["restrictions"] = [
        {
            "name": "reaction_opener",
            "pattern": r"^custom\b",
            "message": "custom opener blocked",
        }
    ]
    configuration = ReplyFormatConfiguration(configuration_document)

    assert template_violations_in_reply(
        "Custom greeting", configuration=configuration
    ) == ["custom opener blocked"]
    assert (
        template_violations_in_reply("Sure, done — now.", configuration=configuration)
        == []
    )


def test_configured_quotation_pairs_change_dash_exemptions(configuration_document):
    configuration_document["syntax"]["quotation_pairs"] = {"«": "»"}
    configuration = ReplyFormatConfiguration(configuration_document)
    reply = "The source says «The result — verified.»"

    assert template_violations_in_reply(reply, configuration=configuration) == []
    assert template_violations_in_reply(
        reply.replace("«", '"').replace("»", '"'), configuration=configuration
    )


@pytest.mark.parametrize("value", [-1, True, "20"])
def test_invalid_budgets_fail_before_validation(configuration_document, value):
    configuration_document["lists"]["item"]["grace_words"] = value

    with pytest.raises(ValueError, match="nonnegative integer"):
        ReplyFormatConfiguration(configuration_document)


def test_duplicate_labels_are_rejected_case_insensitively(configuration_document):
    labels = configuration_document["formats"]["labeled_reply"]["labels"]
    duplicate = copy.deepcopy(labels[-1])
    duplicate["name"] = duplicate["name"].upper()
    labels.append(duplicate)

    with pytest.raises(ValueError, match="distinct nonempty"):
        ReplyFormatConfiguration(configuration_document)


def test_unknown_restrictions_are_rejected(configuration_document):
    configuration_document["restrictions"][0]["name"] = "misspelled_rule"

    with pytest.raises(ValueError, match="unknown reply restriction"):
        ReplyFormatConfiguration(configuration_document)
