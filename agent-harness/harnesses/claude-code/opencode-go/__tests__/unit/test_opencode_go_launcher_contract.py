import re
from pathlib import Path

OPENCODE_GO_MODULE = Path(__file__).resolve().parents[2] / "default.nix"
OPENCODE_GO_LAUNCHER_SCRIPT = OPENCODE_GO_MODULE.parent / "scripts" / "claude-go"
OPENCODE_GO_PROVIDER = OPENCODE_GO_MODULE.parents[2] / "opencode" / "go-provider.nix"
TRANSLATION_PROXY_CONFIGURATION = (
    OPENCODE_GO_MODULE.parent / "translation-proxy-configuration.nix"
)
CONSOLE_GO_BASE_URL = "https://opencode.ai/zen/go"
OPENCODE_GO_SECRET_PATH_FRAGMENT = ".secrets/opencode-api-key"
CONSOLE_GO_MODELS = {
    "opus": "deepseek-v4-pro",
    "sonnet": "deepseek-v4-flash",
    "haiku": "kimi-k3",
}
API_KEY_PLACEHOLDER = "@OPENCODE_GO_API_KEY@"
LAUNCHER_EXEC_LINE = re.compile(
    r'^\s*exec "\$CLAUDE_GO_LAUNCHER_CLAUDE_BINARY" .*$', re.M
)


def module_source() -> str:
    return OPENCODE_GO_MODULE.read_text()


def launcher_source() -> str:
    return OPENCODE_GO_LAUNCHER_SCRIPT.read_text()


def provider_source() -> str:
    return OPENCODE_GO_PROVIDER.read_text()


def model_definitions(section: str) -> dict[str, str]:
    matched = re.search(
        rf"^  {section} = \{{(?P<body>.*?)^  \}};", provider_source(), re.M | re.S
    )
    assert matched, f"the shared provider must define {section}"
    return dict(re.findall(r'^    (\w+) = "([^"]+)";$', matched.group("body"), re.M))


def launcher_exec_line() -> str:
    matched = LAUNCHER_EXEC_LINE.search(launcher_source())
    return matched.group(0) if matched else ""


def test_the_opencode_go_module_still_defines_a_claude_launcher():
    assert OPENCODE_GO_MODULE.is_file(), (
        f"{OPENCODE_GO_MODULE} is gone, so this guard checks nothing"
    )
    assert OPENCODE_GO_LAUNCHER_SCRIPT.is_file(), (
        f"{OPENCODE_GO_LAUNCHER_SCRIPT} is gone, so this guard checks nothing"
    )
    assert "builtins.readFile ./scripts/claude-go" in module_source(), (
        "the module must still deploy the extracted launcher script as the claude-go body"
    )
    assert launcher_exec_line(), (
        "the claude-go launcher no longer execs claude, so the contract guards below are vacuous"
    )


def test_the_launcher_targets_the_loopback_translation_proxy():
    source = module_source()
    assert 'ANTHROPIC_BASE_URL = "http://${translationProxyListenAddress}' in source, (
        "claude-go must reach Console Go through the local proxy; the endpoint's own Anthropic translation drops tool names and 400s on the first message"
    )
    assert 'translationProxyListenAddress = "127.0.0.1"' in source, (
        "the translation proxy must stay on the loopback interface, since it holds the plan's API key and requires no client authentication"
    )


def test_the_proxy_forwards_to_the_console_go_openai_endpoint():
    assert f'baseUrl = "{CONSOLE_GO_BASE_URL}"' in provider_source(), (
        "the shared provider must define the Console Go endpoint"
    )
    assert 'upstreamBaseUrl = "${opencodeGo.baseUrl}/v1"' in module_source(), (
        "the proxy must forward to Console Go's OpenAI path, which is the one that keeps tool names intact"
    )
    assert (
        'base-url: "${upstreamBaseUrl}"' in TRANSLATION_PROXY_CONFIGURATION.read_text()
    ), "the generated config must place that upstream on the provider's base-url"


def test_the_api_key_never_reaches_the_nix_store():
    source = module_source()
    assert API_KEY_PLACEHOLDER in source, (
        "the store-readable config template must carry a placeholder, never the key itself"
    )
    assert "builtins.readFile ./scripts/" in source, (
        "only the renderer script and the launcher body may be read at evaluation time"
    )
    assert "opencodeGo.apiKeyFile" in source, (
        "the service must take the key from the agenix-deployed file at runtime"
    )
    assert OPENCODE_GO_SECRET_PATH_FRAGMENT in provider_source(), (
        "the shared provider must reference the agenix-deployed API key"
    )


def test_the_launcher_carries_no_credential_of_its_own():
    source = launcher_source()
    assert "unset ANTHROPIC_API_KEY" in source, (
        "the proxy authenticates upstream, so Claude Code must not carry the plan key in its environment"
    )
    assert 'ANTHROPIC_API_KEY="$(cat' not in source, (
        "reading the key into the launcher would spread the credential past the proxy that needs it"
    )


def test_the_model_tiers_come_from_the_shared_provider():
    assert model_definitions("models") == CONSOLE_GO_MODELS, (
        "claude-go and native OpenCode must stay on one DeepSeek and Kimi selection"
    )
    for alias in CONSOLE_GO_MODELS:
        assert (
            f"ANTHROPIC_DEFAULT_{alias.upper()}_MODEL = opencodeGo.models.{alias};"
            in module_source()
        ), (
            f"the {alias} alias must resolve through the shared provider, not a local literal"
        )


def test_every_advertised_model_is_translated_by_the_proxy():
    source = module_source()
    assert (
        "translatedModelNames = lib.unique (builtins.attrValues opencodeGo.models)"
        in source
    ), (
        "the proxy must advertise exactly the shared provider's models, so adding a tier cannot leave it unroutable"
    )


def test_the_launch_default_and_the_exec_line_share_one_model_binding():
    assert '--model "$CLAUDE_GO_LAUNCHER_MODEL"' in launcher_exec_line(), (
        "the launcher must pass the model the wrapper supplied, not a literal of its own"
    )
    assert "CLAUDE_GO_LAUNCHER_MODEL = opencodeGo.models.sonnet;" in module_source(), (
        "the launch default must use the shared provider's sonnet model"
    )


def test_the_default_model_flag_precedes_caller_arguments():
    assert '--model "$CLAUDE_GO_LAUNCHER_MODEL" "$@"' in launcher_exec_line(), (
        "the default must precede caller arguments so a later --model still wins"
    )


def test_the_launcher_reports_a_proxy_that_is_not_listening():
    source = launcher_source()
    probe = 'exec 3<>"/dev/tcp/$CLAUDE_GO_LAUNCHER_PROXY_LISTEN_ADDRESS'
    assert probe in source, (
        "claude-go must probe the proxy before starting, because without it every tool-carrying request 400s"
    )
    assert (
        "Inspect the service: ${CLAUDE_GO_LAUNCHER_PROXY_INSPECTION_COMMAND" in source
    ), "the failure must name the service inspection command for the running platform"
    assert source.index(probe) < source.index(
        'exec "$CLAUDE_GO_LAUNCHER_CLAUDE_BINARY"'
    ), "the proxy probe must run before claude is started"
