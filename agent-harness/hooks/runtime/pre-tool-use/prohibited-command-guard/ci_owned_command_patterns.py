from shell_command_invocation_position import COMMAND_INVOCATION_POSITION_PREFIX

TEST_DIRECTORY_PATTERN = (
    r"(?:__tests__|__test[*?@\[][^\s/]*|__tes[*?@\[][^\s/]*|"
    r"__te[*?@\[][^\s/]*|__t[*?@\[][^\s/]*|__[*?@\[][^\s/]*|"
    r"[*?@\[][^\s/]*tests__)"
)
TEST_RUNNER_DIRECTORY_PATTERN = rf"(?:{TEST_DIRECTORY_PATTERN}|repository/verification)"
TEST_RUNNER_PATH_PATTERN = rf"{TEST_RUNNER_DIRECTORY_PATTERN}/run\.sh"
TEST_RUNNER_DYNAMIC_PATH_PATTERN = (
    rf"{TEST_RUNNER_DIRECTORY_PATTERN}/[^\s;&|]*[$*?\[{{%`]"
)
TEST_RUNNER_VARIABLE_PATH_PATTERN = (
    rf"(?=[\s\S]*={TEST_RUNNER_DIRECTORY_PATTERN})(?=[\s\S]*\./\$)"
    rf"(?=[\s\S]*(?:=run\.sh\b|=run(?:[;\s]|$)))"
    rf"(?=[\s\S]*(?:=sh(?:[;\s]|$)|\brun\.sh\b))"
)
TEST_RUNNER_TEMPLATE_PATH_PATTERN = (
    rf"\$\([^;\n]*{TEST_RUNNER_DIRECTORY_PATTERN}/[^;\n]*%"
)
TEST_RUNNER_AFTER_DIRECTORY_CHANGE_PATTERN = rf"\bcd\s+{TEST_RUNNER_DIRECTORY_PATTERN}\s*(?:&&|;)\s*\./[^;\n]*(?:\brun\.sh\b|`|\$\()"
TEST_RUNNER_DENIAL_REASON = (
    "repository/verification/run.sh is prohibited locally; CI runs it after push. Run the affected "
    "test file or small named set directly."
)
PYTEST_INVOCATION_PREFIX = r"(?:python3? -m )?pytest\b"
PYTEST_WHOLE_TIER_PATH_TERMINATOR = r"(?:/[*?[]|[\s;&|]|$)"
PYTEST_CI_OWNED_TREE_ROOT_PATTERN = (
    rf"(?:{TEST_DIRECTORY_PATTERN}|agent-harness/quality/evaluations)"
)
PYTEST_WHOLE_CI_OWNED_TIER_DIRECTORY_PATTERN = (
    rf"{PYTEST_INVOCATION_PREFIX}[^;&|\n]*?{PYTEST_CI_OWNED_TREE_ROOT_PATTERN}/"
    rf"(?:unit|integration)/*{PYTEST_WHOLE_TIER_PATH_TERMINATOR}"
)
PYTEST_WHOLE_TESTS_TREE_PATTERN = (
    rf"{PYTEST_INVOCATION_PREFIX}[^;&|\n]*?{PYTEST_CI_OWNED_TREE_ROOT_PATTERN}/"
    rf"*{PYTEST_WHOLE_TIER_PATH_TERMINATOR}"
)
PYTEST_NO_PATH_PATTERN = (
    rf"{PYTEST_INVOCATION_PREFIX}(?!\s+--?(?:version|help|fixtures)\b)(?!\s+-h\b)"
    rf"(?:\s+(?:-\S+(?:\s+\S+)?|\S+=\S+))*\s*(?:[;&|]|$)"
)
PYTEST_DOT_PATH_PATTERN = rf"{PYTEST_INVOCATION_PREFIX}\s+\.(?:/\.|/)?(?:\s|$|[;&|])"
PYTEST_AGENTS_TREE_PATTERN = (
    rf"{PYTEST_INVOCATION_PREFIX}[^;&|\n]*?\bagents\b/?"
    rf"(?:\s+-\S+(?:\s+\S+)?)*\s*(?:[;&|]|$)"
)
PYTEST_CI_OWNED_TIER_DENIAL_REASON = (
    "pytest over a whole CI-owned tier directory is prohibited; CI runs the unit "
    "and integration tiers after push. Run a specific test file, for example "
    "'pytest agent-harness/hooks/runtime/__tests__/unit/test_specific_thing.py'."
)
PYTEST_WHOLE_COLLECTION_DENIAL_REASON = (
    "Bare pytest or a whole tests-tree run collects CI-owned tiers; CI runs them "
    "after push. Run a specific test file, for example "
    "'pytest agent-harness/hooks/runtime/__tests__/unit/test_specific_thing.py'."
)
NIX_FLAKE_CHECK_PATTERN = (
    rf"{COMMAND_INVOCATION_POSITION_PREFIX}nix\s+flake\s+check"
    rf"(?!\s+--?(?:help|version)\b)(?:\s|$|[;&|])"
)
NIX_FLAKE_CHECK_DENIAL_REASON = (
    "nix flake check runs in CI after push; the local verification for a nix "
    "change is 'rebuild'."
)

CI_OWNED_BASH_COMMAND_PATTERNS = [
    (TEST_RUNNER_PATH_PATTERN, TEST_RUNNER_DENIAL_REASON),
    (PYTEST_WHOLE_CI_OWNED_TIER_DIRECTORY_PATTERN, PYTEST_CI_OWNED_TIER_DENIAL_REASON),
    (PYTEST_WHOLE_TESTS_TREE_PATTERN, PYTEST_WHOLE_COLLECTION_DENIAL_REASON),
    (TEST_RUNNER_DYNAMIC_PATH_PATTERN, TEST_RUNNER_DENIAL_REASON),
    (TEST_RUNNER_VARIABLE_PATH_PATTERN, TEST_RUNNER_DENIAL_REASON),
    (TEST_RUNNER_TEMPLATE_PATH_PATTERN, TEST_RUNNER_DENIAL_REASON),
    (TEST_RUNNER_AFTER_DIRECTORY_CHANGE_PATTERN, TEST_RUNNER_DENIAL_REASON),
    (PYTEST_NO_PATH_PATTERN, PYTEST_WHOLE_COLLECTION_DENIAL_REASON),
    (PYTEST_DOT_PATH_PATTERN, PYTEST_WHOLE_COLLECTION_DENIAL_REASON),
    (PYTEST_AGENTS_TREE_PATTERN, PYTEST_WHOLE_COLLECTION_DENIAL_REASON),
    (NIX_FLAKE_CHECK_PATTERN, NIX_FLAKE_CHECK_DENIAL_REASON),
]
