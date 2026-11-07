from __future__ import annotations

import re
from pathlib import Path

PRELUDE_TEMPLATE_PATH = Path(__file__).resolve().parent / "workflow_budget_prelude.js"
PRELUDE_TEMPLATE_LINES = PRELUDE_TEMPLATE_PATH.read_text().strip().splitlines()
PRELUDE_START_MARKER = PRELUDE_TEMPLATE_LINES[0]
PRELUDE_END_MARKER = PRELUDE_TEMPLATE_LINES[-1]
AGENT_CEILING_PLACEHOLDER = "__AGENT_CEILING__"
OUTPUT_TOKEN_CEILING_PLACEHOLDER = "__OUTPUT_TOKEN_CEILING__"
META_DECLARATION_PATTERN = re.compile(r"export\s+const\s+meta\s*=\s*\{")
PRELUDE_BYPASSING_CONSTRUCT_PATTERNS = {
    "globalThis": re.compile(r"(?<![\w$.])globalThis\b"),
    "eval()": re.compile(r"(?<![\w$.])eval\s*\("),
    "Function()": re.compile(r"(?<![\w$.])Function\s*\("),
    "workflow()": re.compile(r"(?<![\w$.])workflow\s*\("),
}
CODE_MODE = "code"
TEMPLATE_QUOTE = "`"


def _blank(characters, start, end):
    for index in range(start, min(end, len(characters))):
        if characters[index] != "\n":
            characters[index] = " "


def _end_of_comment(source, index):
    if source.startswith("//", index):
        line_end = source.find("\n", index)
        return len(source) if line_end == -1 else line_end
    block_end = source.find("*/", index + 2)
    return len(source) if block_end == -1 else block_end + 2


def code_with_literals_and_comments_blanked(source):
    characters = list(source)
    mode_stack = [CODE_MODE]
    expression_brace_depths = [0]
    index = 0
    while index < len(source):
        mode = mode_stack[-1]
        character = source[index]
        if mode == CODE_MODE:
            if source.startswith("//", index) or source.startswith("/*", index):
                comment_end = _end_of_comment(source, index)
                _blank(characters, index, comment_end)
                index = comment_end
                continue
            if character in "'\"`":
                mode_stack.append(character)
            elif character == "{":
                expression_brace_depths[-1] += 1
            elif character == "}":
                if expression_brace_depths[-1] == 0 and len(mode_stack) > 1:
                    mode_stack.pop()
                    expression_brace_depths.pop()
                else:
                    expression_brace_depths[-1] -= 1
            index += 1
            continue
        if character == "\\":
            _blank(characters, index, index + 2)
            index += 2
            continue
        if mode == TEMPLATE_QUOTE and source.startswith("${", index):
            mode_stack.append(CODE_MODE)
            expression_brace_depths.append(0)
            index += 2
            continue
        if character == mode:
            mode_stack.pop()
        else:
            _blank(characters, index, index + 1)
        index += 1
    return "".join(characters)


def meta_declaration_end(script):
    code = code_with_literals_and_comments_blanked(script)
    meta_declaration = META_DECLARATION_PATTERN.search(code)
    if meta_declaration is None:
        return None
    brace_depth = 0
    for index in range(meta_declaration.end() - 1, len(code)):
        if code[index] == "{":
            brace_depth += 1
        elif code[index] == "}":
            brace_depth -= 1
            if brace_depth == 0:
                declaration_end = index + 1
                following_code = code[declaration_end:]
                trailing_semicolon = re.match(r"[ \t]*;", following_code)
                return declaration_end + (
                    trailing_semicolon.end() if trailing_semicolon else 0
                )
    return None


def script_without_budget_prelude(script):
    while True:
        prelude_start = script.find(PRELUDE_START_MARKER)
        prelude_end = script.find(PRELUDE_END_MARKER, prelude_start)
        if prelude_start == -1 or prelude_end == -1:
            return script
        removal_end = prelude_end + len(PRELUDE_END_MARKER)
        if script.startswith("\n", removal_end):
            removal_end += 1
        script = script[:prelude_start] + script[removal_end:]


def prelude_bypassing_constructs(script):
    code = code_with_literals_and_comments_blanked(script)
    return [
        construct_name
        for construct_name, construct_pattern in PRELUDE_BYPASSING_CONSTRUCT_PATTERNS.items()
        if construct_pattern.search(code)
    ]


def rendered_budget_prelude(agent_ceiling, output_token_ceiling):
    return (
        PRELUDE_TEMPLATE_PATH.read_text()
        .replace(AGENT_CEILING_PLACEHOLDER, str(agent_ceiling))
        .replace(OUTPUT_TOKEN_CEILING_PLACEHOLDER, str(output_token_ceiling))
    )


def script_with_budget_prelude(script, agent_ceiling, output_token_ceiling):
    declaration_end = meta_declaration_end(script)
    if declaration_end is None:
        return None
    return (
        script[:declaration_end]
        + "\n"
        + rendered_budget_prelude(agent_ceiling, output_token_ceiling)
        + script[declaration_end:]
    )
