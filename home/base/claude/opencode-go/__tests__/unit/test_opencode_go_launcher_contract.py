import re
from pathlib import Path

OPENCODE_GO_MODULE = Path(__file__).resolve().parents[2] / "default.nix"
OPENCODE_GO_MODEL = "qwen3.7-plus"
OPENCODE_GO_BASE_URL = "https://opencode.ai/zen/go"
OPENCODE_GO_SECRET_PATH_FRAGMENT = ".secrets/opencode-api-key"
LAUNCHER_EXEC_LINE = re.compile(r"^\s*exec \S+/bin/claude .*$", re.M)


def module_source() -> str:
    return OPENCODE_GO_MODULE.read_text()


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
    assert f'opencodeGoBaseUrl = "{OPENCODE_GO_BASE_URL}"' in source, (
        "the module must declare the opencode-go endpoint as its base URL binding"
    )
    assert 'ANTHROPIC_BASE_URL="${opencodeGoBaseUrl}"' in source, (
        "claude-go must point ANTHROPIC_BASE_URL at the declared opencode-go endpoint"
    )


def test_the_api_key_variable_is_exported_from_the_secret_file_at_runtime():
    source = module_source()
    assert 'ANTHROPIC_API_KEY="$(cat' in source, (
        "claude-go must read the API key from a file at runtime; a literal value would leak it into the Nix store"
    )
    assert OPENCODE_GO_SECRET_PATH_FRAGMENT in source, (
        "claude-go must reference the agenix-deployed ~/.secrets/opencode-api-key"
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


def test_all_three_model_aliases_resolve_to_the_opencode_go_model():
    source = module_source()
    assert f'opencodeGoModel = "{OPENCODE_GO_MODEL}"' in source, (
        "the module must declare the opencode-go model binding"
    )
    for alias in ("OPUS", "SONNET", "HAIKU"):
        assert f'ANTHROPIC_DEFAULT_{alias}_MODEL="${{opencodeGoModel}}"' in source, (
            f"the {alias.lower()} alias must resolve to the declared opencode-go model"
        )


def test_the_aliases_and_the_exec_line_share_one_model_binding():
    source = module_source()
    declared = re.search(r'opencodeGoModel = "([^"]+)"', source)
    assert declared, "opencodeGoModel is no longer declared in the module"
    assert f'--model "${{opencodeGoModel}}"' in launcher_exec_line(), (
        "the exec line passes a model other than the declared binding, so the aliases and the pinned model can drift apart silently"
    )


def test_the_default_model_flag_precedes_caller_arguments():
    assert '--model "${opencodeGoModel}" "$@"' in launcher_exec_line(), (
        "claude-go must pass --model qwen3.7-plus before the caller arguments so a caller's later --model still wins"
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
