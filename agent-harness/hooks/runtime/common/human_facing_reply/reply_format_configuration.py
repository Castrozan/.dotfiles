import json
import os
import re


def require_fields(value, fields, location):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f"{location} must contain exactly {', '.join(fields)}")


def require_nonnegative_integer(value, location):
    if type(value) is not int or value < 0:
        raise ValueError(f"{location} must be a nonnegative integer")


def validate_word_budget(budget, location):
    require_fields(budget, ("maximum_words", "grace_words"), location)
    for field, value in budget.items():
        require_nonnegative_integer(value, f"{location}.{field}")


def validate_restriction(restriction):
    required = {"name", "message"}
    allowed = required | {"pattern", "required_pattern", "characters"}
    if (
        not isinstance(restriction, dict)
        or not required <= restriction.keys() <= allowed
    ):
        raise ValueError(
            "reply restrictions require name, message, and supported parameters"
        )
    for field in required:
        if not isinstance(restriction[field], str) or not restriction[field]:
            raise ValueError(f"restriction {field} must be a nonempty string")
    restriction["message"].format(
        word_count=0,
        maximum_words=0,
        grace_words=0,
        missing_labels="",
        label="",
        line_count=0,
        maximum_lines=0,
        character_name="",
    )


def exceeds_word_budget(word_count, budget):
    return word_count > budget["maximum_words"] + budget["grace_words"]


def validate_reply_labels(configured_labels):
    labels = {}
    for label in configured_labels:
        require_fields(
            label, ("name", "maximum_words", "grace_words", "instruction"), "label"
        )
        name = label["name"]
        if (
            not isinstance(name, str)
            or not name
            or name.lower() in {existing.lower() for existing in labels}
        ):
            raise ValueError("reply labels must have distinct nonempty names")
        for field in ("maximum_words", "grace_words"):
            require_nonnegative_integer(label[field], f"{name}.{field}")
        labels[name] = label
    if not labels:
        raise ValueError("labeled replies require at least one label")
    return labels


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
        require_fields(
            self.syntax,
            (
                "list_marker_pattern",
                "table_row_prefix",
                "box_drawing_characters",
                "code_fence_prefix",
                "label_emphasis_marker",
                "block_quote_pattern",
                "inline_code_pattern",
                "quotation_pattern",
            ),
            "syntax",
        )
        if any(
            not isinstance(value, str) or not value for value in self.syntax.values()
        ):
            raise ValueError("reply syntax values must be nonempty strings")
        self.syntax_patterns = {
            name: re.compile(value)
            for name, value in self.syntax.items()
            if name.endswith("_pattern")
        }
        emphasis = self.syntax["label_emphasis_marker"]
        marker = f"(?:{re.escape(emphasis)}|{re.escape(emphasis[0])})?"
        self.label_patterns = {
            name: re.compile(
                rf"^\s*{marker}{re.escape(name)}{marker}\s*:", re.IGNORECASE
            )
            for name in self.labels
        }
        self.restrictions = {}
        self.restriction_patterns = {}
        for restriction in document["restrictions"]:
            validate_restriction(restriction)
            name = restriction["name"]
            if name in self.restrictions:
                raise ValueError(f"duplicate reply restriction: {name}")
            self.restrictions[name] = restriction
            self.restriction_patterns[name] = {
                key: re.compile(value, re.IGNORECASE)
                for key, value in restriction.items()
                if key in ("pattern", "required_pattern")
            }
        self.feedback = document["feedback"]
        require_fields(self.feedback, ("prefix", "repair"), "feedback")
        if any(not isinstance(value, str) for value in self.feedback.values()):
            raise ValueError("reply feedback must contain strings")

    def violation(self, restriction, **values):
        return self.restrictions[restriction]["message"].format(**values)


with open(
    os.path.join(os.path.dirname(__file__), "reply-formats.json"), encoding="utf-8"
) as configuration_file:
    REPLY_FORMAT_CONFIGURATION = ReplyFormatConfiguration(json.load(configuration_file))
