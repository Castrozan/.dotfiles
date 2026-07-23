import re
from pathlib import Path

GPT_PROXY_MODULE = Path(__file__).resolve().parents[2] / "default.nix"
LAUNCHER_EXEC_LINE = re.compile(r"^\s*exec \S+/bin/claude .*$", re.M)


def module_source() -> str:
    return GPT_PROXY_MODULE.read_text()


def launcher_exec_line() -> str:
    matched = LAUNCHER_EXEC_LINE.search(module_source())
    return matched.group(0) if matched else ""


def test_the_gpt_proxy_module_still_defines_a_claude_launcher():
    assert GPT_PROXY_MODULE.is_file(), (
        f"{GPT_PROXY_MODULE} is gone, so this guard checks nothing"
    )
    assert launcher_exec_line(), (
        "the claude-gpt launcher no longer execs claude, so the model pin guard below is vacuous"
    )


def test_the_launcher_passes_an_explicit_model_flag():
    assert "--model" in launcher_exec_line(), (
        "claude-gpt must pass --model explicitly: the deployed settings.json pins a "
        "concrete model, so the ANTHROPIC_DEFAULT_OPUS_MODEL alias never takes effect "
        "and the launcher would silently run on the Anthropic model instead of the proxy"
    )


def test_the_pinned_model_is_the_declared_opus_tier_model():
    declared = re.search(r'gptModelForOpusTier = "([^"]+)"', module_source())
    assert declared, "gptModelForOpusTier is no longer declared in the module"
    assert "${gptModelForOpusTier}" in launcher_exec_line(), (
        "the launcher passes a model other than the declared opus tier binding, "
        "so the exported alias and the passed model can drift apart silently"
    )
    assert declared.group(1).startswith("gpt-"), (
        f"the opus tier is pinned to {declared.group(1)}, which is not a proxy model, "
        f"so claude-gpt would bill the Anthropic subscription instead of the ChatGPT one"
    )
