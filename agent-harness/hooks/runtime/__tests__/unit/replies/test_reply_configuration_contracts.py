import json

import pytest

from flat_deploy_test_support import (
    INTERACTIVE_ENV_VAR,
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)
from human_facing_reply_test_support import REPLY_RULE_MODULE_DIRECTORY
from reply_format_configuration import ReplyFormatConfiguration


@pytest.fixture
def configuration_document():
    return json.loads((REPLY_RULE_MODULE_DIRECTORY / "reply-formats.json").read_text())


@pytest.mark.parametrize(
    "mutation",
    ["missing_parameter", "wrong_placeholder", "bad_paragraphs", "bad_instruction"],
)
def test_invalid_configuration_is_rejected_before_any_reply(
    configuration_document, mutation
):
    restrictions = {
        rule["name"]: rule for rule in configuration_document["restrictions"]
    }
    if mutation == "missing_parameter":
        restrictions["unlinked_artifact"].pop("required_pattern")
    elif mutation == "wrong_placeholder":
        restrictions["list_line_words"]["message"] = "Bad item for {label}"
    elif mutation == "bad_paragraphs":
        configuration_document["instruction_paragraphs"] = None
    else:
        configuration_document["formats"]["labeled_reply"]["labels"][0][
            "instruction"
        ] = None

    with pytest.raises(ValueError):
        ReplyFormatConfiguration(configuration_document)


def test_invalid_configuration_cannot_silently_disable_the_stop_guard(tmp_path):
    flatten_into_single_runtime_directory(tmp_path)
    path = tmp_path / "reply-formats.json"
    document = json.loads(path.read_text())
    document["restrictions"][0].pop("required_pattern")
    path.write_text(json.dumps(document))

    result = run_flattened_hook(
        tmp_path,
        "stop-dispatcher.py",
        {
            "hook_event_name": "Stop",
            "reply_text": "PR #17 is ready. " + "evidence " * 150,
        },
        {INTERACTIVE_ENV_VAR: "/some/interactive-communication.md"},
    )

    response = json.loads(result.stdout)
    assert response.get("decision") == "block"
    assert "could not run" in response["reason"]


@pytest.mark.parametrize(
    "rule,field,value",
    [
        ("reaction_opener", "pattern", "("),
        ("reaction_opener", "message", "{label}"),
        ("list_line_words", "message", "{word_count.real}"),
        ("list_line_words", "message", "{word_count!r}"),
        ("sentence_dash", "characters", "—"),
        ("sentence_dash", "characters", {"--": "dash"}),
        ("unlinked_artifact", "pattern", "PR"),
        ("unlinked_artifact", "required_pattern", "https?://"),
        ("unlinked_artifact", "kind_paths", []),
    ],
)
def test_rule_parameters_obey_their_own_contract(
    configuration_document, rule, field, value
):
    restriction = next(
        item for item in configuration_document["restrictions"] if item["name"] == rule
    )
    restriction[field] = value

    with pytest.raises(ValueError):
        ReplyFormatConfiguration(configuration_document)


@pytest.mark.parametrize(
    "paragraphs", [[], [""], ["{unknown}"], ["{formats[missing]}"]]
)
def test_instruction_templates_are_validated_with_the_configuration(
    configuration_document, paragraphs
):
    configuration_document["instruction_paragraphs"] = paragraphs

    with pytest.raises(ValueError):
        ReplyFormatConfiguration(configuration_document)
