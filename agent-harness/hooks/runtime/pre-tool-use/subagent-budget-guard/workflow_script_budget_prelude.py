from __future__ import annotations

import re
from pathlib import Path

PRELUDE_TEMPLATE_PATH = Path(__file__).resolve().parent / "workflow_budget_prelude.js"
PRELUDE_TEMPLATE_LINES = PRELUDE_TEMPLATE_PATH.read_text().strip().splitlines()
PRELUDE_START_MARKER = PRELUDE_TEMPLATE_LINES[0]
PRELUDE_END_MARKER = PRELUDE_TEMPLATE_LINES[-1]
AGENT_CEILING_PLACEHOLDER = "__AGENT_CEILING__"
OUTPUT_CEILING_PLACEHOLDER = "__OUTPUT_TOKEN_CEILING__"
META_DECLARATION_PATTERN = re.compile(r"export\s+const\s+meta\s*=\s*\{")
TRAILING_SEMICOLON_PATTERN = re.compile(r"[ \t]*;")
BRACE_DEPTH_CHANGES = {"{": 1, "}": -1}
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


class _LiteralAndCommentBlanker:
    def __init__(self, source):
        self.source = source
        self.characters = list(source)
        self.mode_stack = [CODE_MODE]
        self.expression_brace_depths = [0]

    def blanked(self):
        index = 0
        while index < len(self.source):
            index = self._step(index)
        return "".join(self.characters)

    def _step(self, index):
        if self.mode_stack[-1] == CODE_MODE:
            return self._step_in_code(index)
        return self._step_in_literal(index)

    def _step_in_code(self, index):
        if self.source.startswith(("//", "/*"), index):
            comment_end = _end_of_comment(self.source, index)
            _blank(self.characters, index, comment_end)
            return comment_end
        character = self.source[index]
        if character in "'\"`":
            self.mode_stack.append(character)
        elif character == "{":
            self.expression_brace_depths[-1] += 1
        elif character == "}":
            self._close_brace()
        return index + 1

    def _close_brace(self):
        if self.expression_brace_depths[-1] == 0 and len(self.mode_stack) > 1:
            self.mode_stack.pop()
            self.expression_brace_depths.pop()
        else:
            self.expression_brace_depths[-1] -= 1

    def _step_in_literal(self, index):
        quote = self.mode_stack[-1]
        if self.source[index] == "\\":
            _blank(self.characters, index, index + 2)
            return index + 2
        if quote == TEMPLATE_QUOTE and self.source.startswith("${", index):
            self.mode_stack.append(CODE_MODE)
            self.expression_brace_depths.append(0)
            return index + 2
        if self.source[index] == quote:
            self.mode_stack.pop()
        else:
            _blank(self.characters, index, index + 1)
        return index + 1


def code_with_literals_and_comments_blanked(source):
    return _LiteralAndCommentBlanker(source).blanked()


def _closing_brace_index(code, opening_brace_index):
    brace_depth = 0
    for index in range(opening_brace_index, len(code)):
        brace_depth += BRACE_DEPTH_CHANGES.get(code[index], 0)
        if brace_depth == 0:
            return index
    return None


def meta_declaration_end(script):
    code = code_with_literals_and_comments_blanked(script)
    meta_declaration = META_DECLARATION_PATTERN.search(code)
    if meta_declaration is None:
        return None
    closing_brace_index = _closing_brace_index(code, meta_declaration.end() - 1)
    if closing_brace_index is None:
        return None
    trailing_semicolon = TRAILING_SEMICOLON_PATTERN.match(code, closing_brace_index + 1)
    return trailing_semicolon.end() if trailing_semicolon else closing_brace_index + 1


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
        .replace(OUTPUT_CEILING_PLACEHOLDER, str(output_token_ceiling))
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
