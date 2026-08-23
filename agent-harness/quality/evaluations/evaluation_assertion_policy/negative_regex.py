import re

BARE_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def expression_without_zero_width_boundaries(expression: str) -> str:
    expression = expression.strip()
    previous_expression = None
    while expression != previous_expression:
        previous_expression = expression
        for boundary in ("^", r"\b"):
            if expression.startswith(boundary):
                expression = expression[len(boundary) :]
        for boundary in ("$", r"\b"):
            if expression.endswith(boundary):
                expression = expression[: -len(boundary)]
        expression = expression.strip()
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
        elif character == "]" and inside_character_class:
            inside_character_class = False
        elif not inside_character_class and character == "(":
            parenthesis_depth += 1
        elif not inside_character_class and character == ")":
            parenthesis_depth -= 1
        elif not inside_character_class and parenthesis_depth == 0 and character == "|":
            alternatives.append(expression[alternative_start:index])
            alternative_start = index + 1
    alternatives.append(expression[alternative_start:])
    return alternatives


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
        elif character == "]" and inside_character_class:
            inside_character_class = False
        elif not inside_character_class and character == "(":
            parenthesis_depth += 1
        elif not inside_character_class and character == ")":
            parenthesis_depth -= 1
            if parenthesis_depth == 0:
                if index != len(expression) - 1:
                    return None
                return expression[group_content_start:index]
    return None


def bare_token_expressions_in_regex(pattern: str) -> list[str]:
    bare_token_expressions = []
    for alternative in split_top_level_alternatives(pattern):
        normalized_alternative = expression_without_zero_width_boundaries(alternative)
        if BARE_TOKEN_PATTERN.fullmatch(normalized_alternative):
            bare_token_expressions.append(normalized_alternative)
            continue
        enclosed_expression = expression_inside_enclosing_group(normalized_alternative)
        if enclosed_expression is not None:
            bare_token_expressions.extend(
                bare_token_expressions_in_regex(enclosed_expression)
            )
    return bare_token_expressions
