import re
from pathlib import Path

OPENCODE_GO_MODULE = Path(__file__).resolve().parents[2] / "default.nix"
OPENCODE_MODULE_DIRECTORY = OPENCODE_GO_MODULE.parents[2] / "opencode"
OPENCODE_GO_PROVIDER = OPENCODE_MODULE_DIRECTORY / "go-provider.nix"
TOOL_TRANSLATION_WORKAROUND = (
    OPENCODE_MODULE_DIRECTORY / "console-go-anthropic-tool-translation-workaround.nix"
)
OPENCODE_GO_BASE_URL = "https://opencode.ai/zen/go"
OPENCODE_GO_SECRET_PATH_FRAGMENT = ".secrets/opencode-api-key"
NATIVE_OPENCODE_MODELS = {
    "opus": "deepseek-v4-pro",
    "sonnet": "deepseek-v4-flash",
    "haiku": "kimi-k3",
}
MODEL_ALIASES = tuple(NATIVE_OPENCODE_MODELS)
LAUNCHER_EXEC_LINE = re.compile(r"^\s*exec \S+/bin/claude .*$", re.M)


def module_source() -> str:
    return OPENCODE_GO_MODULE.read_text()


def provider_source() -> str:
    return OPENCODE_GO_PROVIDER.read_text()


def workaround_source() -> str:
    return TOOL_TRANSLATION_WORKAROUND.read_text()


def model_definitions(section: str, source: str) -> dict[str, str]:
    matched = re.search(rf"^  {section} = \{{(?P<body>.*?)^  \}};", source, re.M | re.S)
    assert matched, f"{section} must be defined as a literal attribute set"
    return dict(re.findall(r'^    (\w+) = "([^"]+)";$', matched.group("body"), re.M))


def models_with_working_tool_translation() -> list[str]:
    matched = re.search(
        r"^  modelsConsoleGoTranslatesToolsCorrectlyFor = \[(?P<body>.*?)^  \];",
        workaround_source(),
        re.M | re.S,
    )
    assert matched, (
        "the workaround must list the models whose tool translation was verified to work"
    )
    return re.findall(r'^    "([^"]+)"$', matched.group("body"), re.M)


def launcher_exec_line() -> str:
    matched = LAUNCHER_EXEC_LINE.search(module_source())
    return matched.group(0) if matched else ""


def test_the_opencode_go_module_still_defines_a_claude_launcher():
    assert OPENCODE_GO_MODULE.is_file(), (
        f"{OPENCODE_GO_MODULE} is gone, so this guard checks nothing"
    )
    assert launcher_exec_line(), (
        "the claude-go launcher no longer execs claude, so the contract guards below are vacuous"
    )


def test_the_launcher_targets_the_opencode_go_base_url():
    source = module_source()
    assert OPENCODE_GO_MODULE.is_file(), (
        "the claude-go launcher must exist to target the shared provider"
    )
    assert OPENCODE_GO_PROVIDER.is_file(), (
        "the shared opencode-go provider definition must exist"
    )
    assert f'baseUrl = "{OPENCODE_GO_BASE_URL}"' in provider_source(), (
        "the shared provider must define the Console Go endpoint"
    )
    assert 'ANTHROPIC_BASE_URL="${opencodeGo.baseUrl}"' in source, (
        "claude-go must point ANTHROPIC_BASE_URL at the shared Console Go endpoint"
    )


def test_the_api_key_variable_is_exported_from_the_secret_file_at_runtime():
    source = module_source()
    provider = provider_source()
    assert 'ANTHROPIC_API_KEY="$(cat' in source, (
        "claude-go must read the API key from a file at runtime; a literal value would leak it into the Nix store"
    )
    assert OPENCODE_GO_SECRET_PATH_FRAGMENT in provider, (
        "the shared provider must reference the agenix-deployed API key"
    )


def test_no_secret_value_is_embedded_in_the_module():
    source = module_source()
    assert "builtins.readFile" not in source, (
        "the module must never read the secret at eval time, which would place it in the Nix store"
    )
    api_key_export = re.search(r'export ANTHROPIC_API_KEY="([^"]*)"', source)
    assert api_key_export is not None and api_key_export.group(1).startswith("$("), (
        "the ANTHROPIC_API_KEY export must carry a runtime read, never a literal key value"
    )


def test_the_launcher_removes_bearer_authentication():
    assert "unset ANTHROPIC_AUTH_TOKEN" in module_source(), (
        "claude-go must unset ANTHROPIC_AUTH_TOKEN, which the opencode-go endpoint rejects as bearer auth"
    )


def test_native_opencode_models_retain_their_existing_model_selection():
    assert (
        model_definitions("nativeModels", provider_source()) == NATIVE_OPENCODE_MODELS
    ), (
        "native OpenCode speaks the OpenAI wire format, whose tool schemas Console Go relays untouched, so it keeps its DeepSeek selection"
    )


def test_the_tool_translation_workaround_lives_in_its_own_module():
    assert TOOL_TRANSLATION_WORKAROUND.is_file(), (
        "the Console Go tool-translation compensation must live in a file named after the upstream limitation, not inline in the shared provider"
    )
    assert f"import ./{TOOL_TRANSLATION_WORKAROUND.name}" in provider_source(), (
        "the shared provider must reach the workaround through one clean import"
    )


def test_the_provider_derives_claude_code_models_instead_of_hardcoding_them():
    assert (
        "claudeCodeModels = consoleGoAnthropicToolTranslation." in provider_source()
    ), (
        "claudeCodeModels must be derived from the native selection so restoring a model upstream fixes needs only the workaround's compatibility list"
    )


def test_every_substituted_model_was_verified_to_survive_the_translation():
    compatible = models_with_working_tool_translation()
    assert compatible, "the verified-compatible list must not be empty"
    substitutes = model_definitions("toolCompatibleSubstitutes", workaround_source())
    assert set(substitutes) == set(MODEL_ALIASES), (
        "every Claude Code alias needs a substitute for when its native model cannot carry tools"
    )
    for alias, model in substitutes.items():
        assert model in compatible, (
            f"the {alias} substitute must be a model whose Console Go tool translation was verified to work"
        )


def test_no_native_model_is_assumed_to_survive_the_translation():
    compatible = models_with_working_tool_translation()
    for alias, model in NATIVE_OPENCODE_MODELS.items():
        assert model not in compatible, (
            f"{model} still 400s on tools through the Anthropic endpoint, so listing it would send the {alias} alias back into the broken path"
        )


def test_all_three_model_aliases_resolve_to_the_claude_code_models():
    source = module_source()
    for alias in MODEL_ALIASES:
        assert (
            f'ANTHROPIC_DEFAULT_{alias.upper()}_MODEL="${{opencodeGo.claudeCodeModels.{alias}}}"'
            in source
        ), f"the {alias} alias must use its tool-compatible Claude Code model"


def test_the_launch_default_and_the_exec_line_share_one_model_binding():
    assert '--model "${opencodeGo.claudeCodeModels.sonnet}"' in launcher_exec_line(), (
        "the launch default must use the tool-compatible Claude Code sonnet model"
    )


def test_the_default_model_flag_precedes_caller_arguments():
    assert (
        '--model "${opencodeGo.claudeCodeModels.sonnet}" "$@"' in launcher_exec_line()
    ), (
        "the tool-compatible default must precede caller arguments so a later --model still wins"
    )


def test_the_launcher_fails_before_claude_when_the_secret_is_missing():
    source = module_source()
    guard = '[ ! -f "$opencodeGoApiKeyFile" ] || [ ! -r "$opencodeGoApiKeyFile" ]'
    assert guard in source, (
        "claude-go must refuse to start when the API key file is absent or unreadable"
    )
    assert "no readable API key at $opencodeGoApiKeyFile" in source, (
        "the failure must name the missing secret file so the user knows which agenix secret to deploy"
    )
    assert source.index(guard) < source.index("exec "), (
        "the secret guard must run before claude is started"
    )
