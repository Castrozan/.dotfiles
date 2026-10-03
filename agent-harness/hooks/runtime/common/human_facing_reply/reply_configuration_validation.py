import re
from string import Formatter

from reply_restriction_contracts import REPLY_RESTRICTION_CONTRACTS


def require_fields(value, fields, location):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f"{location} must contain exactly {', '.join(sorted(fields))}")


def require_nonnegative_integer(value, location):
    if type(value) is not int or value < 0:
        raise ValueError(f"{location} must be a nonnegative integer")


def require_nonempty_text(value, location):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location} must be a nonempty string")


def require_text_mapping(value, location):
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{location} must be a nonempty mapping")
    for key, item in value.items():
        require_nonempty_text(key, location)
        require_nonempty_text(item, location)


def validate_word_budget(budget, location):
    require_fields(budget, ("maximum_words", "grace_words"), location)
    for field, value in budget.items():
        require_nonnegative_integer(value, f"{location}.{field}")


def validate_reply_labels(configured_labels):
    if not isinstance(configured_labels, list) or not configured_labels:
        raise ValueError("labeled replies require at least one label")
    labels = {}
    for label in configured_labels:
        _validate_reply_label(label, labels)
    return labels


def _validate_reply_label(label: dict, labels: dict) -> None:
    require_fields(
        label, ("name", "maximum_words", "grace_words", "instruction"), "label"
    )
    name = label["name"]
    require_nonempty_text(name, "label name")
    if _label_name_is_already_configured(name, labels):
        raise ValueError("reply labels must have distinct nonempty names")
    require_nonempty_text(label["instruction"], f"{name}.instruction")
    for field in ("maximum_words", "grace_words"):
        require_nonnegative_integer(label[field], f"{name}.{field}")
    labels[name] = label


def _label_name_is_already_configured(name: str, labels: dict) -> bool:
    return name.casefold() in {existing.casefold() for existing in labels}


def compile_reply_pattern(value, location):
    require_nonempty_text(value, location)
    try:
        return re.compile(value, re.IGNORECASE)
    except re.error as error:
        raise ValueError(f"{location}: {error}") from error


def validate_message_template(message, placeholders, location):
    require_nonempty_text(message, location)
    for _, field, specification, conversion in Formatter().parse(message):
        if not _template_field_is_supported(
            field, specification, conversion, placeholders
        ):
            raise ValueError(f"{location} has an unsupported placeholder: {field}")


def _template_field_is_supported(
    field, specification, conversion, placeholders
) -> bool:
    return field is None or (
        field in placeholders and not specification and not conversion
    )


def validate_artifact_patterns(restriction, patterns):
    expected_groups = {
        "pattern": {"generic_kind", "numbered_kind", "number"},
        "required_pattern": {"kind", "number"},
    }
    for field, groups in expected_groups.items():
        if groups.difference(patterns[field].groupindex):
            raise ValueError(
                f"unlinked_artifact.{field} requires groups {sorted(groups)}"
            )
    require_text_mapping(restriction["kind_paths"], "artifact kinds")


def validate_restriction(restriction):
    if not isinstance(restriction, dict):
        raise ValueError("reply restrictions must be objects")
    name, parameters, placeholders = _restriction_contract(restriction)
    require_fields(restriction, {"name", "message"} | parameters, name)
    validate_message_template(restriction["message"], placeholders, f"{name}.message")
    patterns = {
        field: compile_reply_pattern(restriction[field], f"{name}.{field}")
        for field in parameters
        if field.endswith("pattern")
    }
    _validate_restriction_specific_fields(name, restriction, patterns)
    return patterns


def _restriction_contract(restriction):
    name = restriction.get("name")
    if not isinstance(name, str) or name not in REPLY_RESTRICTION_CONTRACTS:
        raise ValueError(f"unknown reply restriction: {name}")
    parameters, placeholders = REPLY_RESTRICTION_CONTRACTS[name]
    return name, parameters, placeholders


def _validate_restriction_specific_fields(name, restriction, patterns) -> None:
    if name == "unlinked_artifact":
        validate_artifact_patterns(restriction, patterns)
    if name == "sentence_dash":
        require_text_mapping(restriction["characters"], "sentence dash characters")
        if any(len(character) != 1 for character in restriction["characters"]):
            raise ValueError("sentence dash keys must be single characters")


def validate_instruction_templates(document):
    paragraphs = document["instruction_paragraphs"]
    if not isinstance(paragraphs, list) or not paragraphs:
        raise ValueError("instruction paragraphs must be a nonempty list")
    values = {**document, "label_instructions": "", "label_budgets": ""}
    for paragraph in paragraphs:
        require_nonempty_text(paragraph, "instruction paragraph")
        try:
            paragraph.format_map(values)
        except (KeyError, ValueError, TypeError, AttributeError, IndexError) as error:
            raise ValueError(f"invalid instruction paragraph: {error}") from error
