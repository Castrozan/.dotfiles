import json
import os
import re

from reply_configuration_validation import (
    compile_reply_pattern,
    require_fields,
    require_nonempty_text,
    require_nonnegative_integer,
    require_text_mapping,
    validate_instruction_templates,
    validate_reply_labels,
    validate_restriction,
    validate_word_budget,
)


def exceeds_word_budget(word_count, budget):
    return word_count > budget["maximum_words"] + budget["grace_words"]


def validate_reply_syntax(syntax):
    require_fields(
        syntax,
        (
            "tree_branch_pattern",
            "label_emphasis_marker",
            "quotation_pairs",
            "apostrophe_characters",
        ),
        "syntax",
    )
    if syntax["label_emphasis_marker"] not in ("**", "__"):
        raise ValueError("label emphasis must use CommonMark strong emphasis")
    require_nonempty_text(syntax["apostrophe_characters"], "apostrophe characters")
    require_text_mapping(syntax["quotation_pairs"], "quotation pairs")
    if any(
        len(character) != 1
        for pair in syntax["quotation_pairs"].items()
        for character in pair
    ):
        raise ValueError("quotation pairs must contain single characters")
    return compile_reply_pattern(syntax["tree_branch_pattern"], "tree branch pattern")


class ReplyFormatConfiguration:
    def __init__(self, document):
        require_fields(
            document,
            (
                "formats",
                "lists",
                "syntax",
                "restrictions",
                "feedback",
                "instruction_paragraphs",
            ),
            "reply formats",
        )
        self.formats = document["formats"]
        require_fields(self.formats, ("confirmation", "labeled_reply"), "formats")
        validate_word_budget(self.formats["confirmation"], "confirmation")
        labeled_reply = self.formats["labeled_reply"]
        require_fields(
            labeled_reply, ("body", "combined_labels", "labels"), "labeled_reply"
        )
        for name in ("body", "combined_labels"):
            validate_word_budget(labeled_reply[name], name)
        self.labels = validate_reply_labels(labeled_reply["labels"])
        self.lists = document["lists"]
        require_fields(
            self.lists, ("maximum_lines", "maximum_exempt_items", "item"), "lists"
        )
        validate_word_budget(self.lists["item"], "list item")
        for field in ("maximum_lines", "maximum_exempt_items"):
            require_nonnegative_integer(self.lists[field], f"lists.{field}")
        if self.lists["maximum_exempt_items"] > self.lists["maximum_lines"]:
            raise ValueError("exempt list size cannot exceed the list line limit")
        self.syntax = document["syntax"]
        self.tree_branch_pattern = validate_reply_syntax(self.syntax)
        self.label_patterns = {
            name: re.compile(
                rf"^\s*(?:\*{{1,2}}|_{{1,2}})?{re.escape(name)}(?:\*{{1,2}}|_{{1,2}})?\s*:",
                re.IGNORECASE,
            )
            for name in self.labels
        }
        self.restrictions, self.restriction_patterns = self.validated_restrictions(
            document["restrictions"]
        )
        self.feedback = document["feedback"]
        require_fields(self.feedback, ("prefix", "repair"), "feedback")
        for field, value in self.feedback.items():
            require_nonempty_text(value, f"feedback.{field}")
        validate_instruction_templates(document)

    @staticmethod
    def validated_restrictions(configured_restrictions):
        if not isinstance(configured_restrictions, list):
            raise ValueError("reply restrictions must be a list")
        restrictions = {}
        patterns = {}
        for restriction in configured_restrictions:
            compiled_patterns = validate_restriction(restriction)
            name = restriction["name"]
            if name in restrictions:
                raise ValueError(f"duplicate reply restriction: {name}")
            restrictions[name] = restriction
            patterns[name] = compiled_patterns
        return restrictions, patterns

    def violation(self, restriction, **values):
        return self.restrictions[restriction]["message"].format(**values)


with open(
    os.path.join(os.path.dirname(__file__), "reply-formats.json"), encoding="utf-8"
) as configuration_file:
    REPLY_FORMAT_CONFIGURATION = ReplyFormatConfiguration(json.load(configuration_file))
