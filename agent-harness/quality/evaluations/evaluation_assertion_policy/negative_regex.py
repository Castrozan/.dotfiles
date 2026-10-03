import re

BARE_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def expression_without_zero_width_boundaries(expression: str) -> str:
    expression = expression.strip()
    previous_expression = None
    while expression != previous_expression:
        previous_expression = expression
        expression = _remove_starting_boundaries(expression)
        expression = _remove_ending_boundaries(expression)
        expression = expression.strip()
    return expression


def _remove_starting_boundaries(expression: str) -> str:
    for boundary in ("^", r"\b"):
        if expression.startswith(boundary):
            expression = expression[len(boundary) :]
    return expression


def _remove_ending_boundaries(expression: str) -> str:
    for boundary in ("$", r"\b"):
        if expression.endswith(boundary):
            expression = expression[: -len(boundary)]
    return expression


def split_top_level_alternatives(expression: str) -> list[str]:
    alternatives = []
    alternative_start = 0
    parenthesis_depth = 0
    inside_character_class = False
    escaped = False
    for index, character in enumerate(expression):
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "[":
            inside_character_class = True
        elif _closes_character_class(character, inside_character_class):
            inside_character_class = False
        elif not inside_character_class and character == "(":
            parenthesis_depth += 1
        elif not inside_character_class and character == ")":
            parenthesis_depth -= 1
        elif _is_top_level_alternative(
            character, inside_character_class, parenthesis_depth
        ):
            alternatives.append(expression[alternative_start:index])
            alternative_start = index + 1
    alternatives.append(expression[alternative_start:])
    return alternatives


def _is_top_level_alternative(
    character: str, inside_character_class: bool, depth: int
) -> bool:
    return not inside_character_class and depth == 0 and character == "|"


def _opens_parenthesis(character: str, inside_character_class: bool) -> bool:
    return not inside_character_class and character == "("


def _closes_parenthesis(character: str, inside_character_class: bool) -> bool:
    return not inside_character_class and character == ")"


def _closes_character_class(character: str, inside_character_class: bool) -> bool:
    return character == "]" and inside_character_class


def expression_inside_enclosing_group(expression: str) -> str | None:
    if expression.startswith("(?:"):
        group_content_start = 3
    elif expression.startswith("("):
        group_content_start = 1
    else:
        return None
    parenthesis_depth = 0
    inside_character_class = False
    escaped = False
    for index, character in enumerate(expression):
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "[":
            inside_character_class = True
        elif _closes_character_class(character, inside_character_class):
            inside_character_class = False
        elif _opens_parenthesis(character, inside_character_class):
            parenthesis_depth += 1
        elif _closes_parenthesis(character, inside_character_class):
            parenthesis_depth -= 1
            if parenthesis_depth == 0:
                return _enclosing_group_content(expression, index, group_content_start)
    return None


def _enclosing_group_content(expression: str, index: int, content_start: int):
    if index != len(expression) - 1:
        return None
    return expression[content_start:index]


def bare_token_expressions_in_regex(pattern: str) -> list[str]:
    bare_token_expressions = []
    for alternative in split_top_level_alternatives(pattern):
        bare_token_expressions.extend(
            _bare_token_expressions_in_alternative(alternative)
        )
    return bare_token_expressions


def _bare_token_expressions_in_alternative(alternative: str) -> list[str]:
    normalized_alternative = expression_without_zero_width_boundaries(alternative)
    if BARE_TOKEN_PATTERN.fullmatch(normalized_alternative):
        return [normalized_alternative]
    enclosed_expression = expression_inside_enclosing_group(normalized_alternative)
    if enclosed_expression is not None:
        return bare_token_expressions_in_regex(enclosed_expression)
    return []
