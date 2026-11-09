import json

from hypothesis import given
from hypothesis import strategies as strategies

from instruction_data import instruction_data, serialized_values

json_values = strategies.recursive(
    strategies.none()
    | strategies.booleans()
    | strategies.integers()
    | strategies.text(),
    lambda children: (
        strategies.lists(children)
        | strategies.dictionaries(strategies.text(), children)
    ),
    max_leaves=8,
)


@given(json_values)
def test_a_serialized_value_is_one_inline_code_span_that_round_trips(value):
    serialized = instruction_data(value)
    assert serialized.startswith("`") and serialized.endswith("`")
    assert "`" not in serialized[1:-1]
    assert "\n" not in serialized
    assert json.loads(serialized[1:-1]) == value


def test_text_and_json_variables_become_named_fields():
    values = serialized_values(
        ["INPUTS_BRIEF", "TOPIC"],
        ["INPUTS_BATCH"],
        {"INPUTS_BRIEF": "a `page`", "TOPIC": "x", "INPUTS_BATCH": '[{"index": 0}]'},
    )
    assert values == {
        "brief": '`"a \\u0060page\\u0060"`',
        "topic": '`"x"`',
        "batch": '`[{"index":0}]`',
    }


def test_an_absent_variable_serializes_as_empty_or_null():
    assert serialized_values(["INPUTS_CONSTRAINTS"], ["DRAFT"], {}) == {
        "constraints": '`""`',
        "draft": "`null`",
    }
