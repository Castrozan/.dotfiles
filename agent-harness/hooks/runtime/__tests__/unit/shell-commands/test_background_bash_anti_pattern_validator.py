import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

HOOK_SCRIPT_PATH = next(
    candidate
    for candidate in Path(__file__)
    .resolve()
    .parent.parent.parent.parent.rglob(
        "background_bash_anti_pattern_validator_handler.py"
    )
    if "__pycache__" not in candidate.parts
)

_module_spec = importlib.util.spec_from_file_location(
    "background_bash_anti_pattern_validator_handler", HOOK_SCRIPT_PATH
)
sut = importlib.util.module_from_spec(_module_spec)
sys.modules["background_bash_anti_pattern_validator_handler"] = sut
_module_spec.loader.exec_module(sut)


class TestCommandFiltersByHardcodedLongLiteralUsedInCountOrTest:
    @pytest.mark.parametrize(
        "command",
        [
            "gh run list --json headSha --jq '[.[] | select(.headSha == \"1e42771447c81fb6a96b2d3eef3e16df9f8517b3\")] | length'",
            "cat data.json | jq '[.[] | select(.id == \"abc12345\")] | length'",
            'echo "$(jq \'select(.branch == "feature/some-branch") | length\' file.json)" = "0"',
        ],
    )
    def test_flags_jq_select_with_long_literal_and_count_test(self, command):
        assert (
            sut.command_filters_by_hardcoded_long_literal_used_in_count_or_test(command)
            is True
        )

    @pytest.mark.parametrize(
        "command",
        [
            "jq --arg sha \"$SHA\" 'select(.headSha == $sha) | length' data.json",
            "jq 'select(.id == \"short\")' file.json",
            "echo hello world",
            "jq 'select(.headSha == \"1e42771447c81fb6a96b2d3eef3e16df9f8517b3\")' file.json",
        ],
    )
    def test_passes_safe_filters_or_no_downstream_count(self, command):
        assert (
            sut.command_filters_by_hardcoded_long_literal_used_in_count_or_test(command)
            is False
        )


class TestCommandPipesCountIntoTestAgainstLiteralZero:
    @pytest.mark.parametrize(
        "command",
        [
            '[ "$(jq length file.json)" = "0" ]',
            '[ "$(gh pr list --json number --jq length)" = "0" ]',
            '[ "$(wc -l < file.txt)" = "0" ]',
            '[ "$(ls | wc -l)" = 0 ]',
        ],
    )
    def test_flags_count_into_test_against_zero(self, command):
        assert sut.command_pipes_count_into_test_against_literal_zero(command) is True

    @pytest.mark.parametrize(
        "command",
        [
            '[ "$(jq length file.json)" -gt "0" ]',
            'matched=$(jq length file.json); [ "$matched" -gt 0 ]',
            'pr_list_json=$(gh pr list --json number); [ "$pr_list_json" = "[]" ]',
        ],
    )
    def test_passes_affirmative_or_inverted_tests(self, command):
        assert sut.command_pipes_count_into_test_against_literal_zero(command) is False
