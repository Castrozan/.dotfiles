import re
from pathlib import Path

GPT_PROXY_MODULE = Path(__file__).resolve().parents[2] / "default.nix"
GPT_PROXY_LAUNCHER_SCRIPT = GPT_PROXY_MODULE.parent / "scripts" / "claudex"
LAUNCHER_EXEC_LINE = re.compile(
    r'^\s*exec "\$CLAUDEX_LAUNCHER_CLAUDE_BINARY" .*$', re.M
)


def module_source() -> str:
    return GPT_PROXY_MODULE.read_text()


def launcher_source() -> str:
    return GPT_PROXY_LAUNCHER_SCRIPT.read_text()


def test_claudex_pins_the_declared_proxy_model():
    source = module_source()
    matched = LAUNCHER_EXEC_LINE.search(launcher_source())
    assert matched, "claudex no longer execs Claude Code"
    launcher_exec_line = matched.group(0)
    assert "--model" in launcher_exec_line, (
        "claudex must pass --model explicitly: the deployed settings.json carries the "
        "model the user last switched to, so the ANTHROPIC_DEFAULT_OPUS_MODEL alias never "
        "takes effect and the launcher would silently run on the Anthropic model instead of the proxy"
    )
    declared = re.search(r'gptModelForOpusTier = "([^"]+)"', source)
    assert declared, "gptModelForOpusTier is no longer declared in the module"
    assert '--model "$CLAUDEX_LAUNCHER_MODEL"' in launcher_exec_line, (
        "the launcher must pass the model the wrapper supplied, not a literal of its own"
    )
    assert "CLAUDEX_LAUNCHER_MODEL = gptModelForOpusTier;" in source, (
        "the launcher passes a model other than the declared opus tier binding, "
        "so the exported alias and the passed model can drift apart silently"
    )
    assert declared.group(1).startswith("gpt-"), (
        f"the opus tier is pinned to {declared.group(1)}, which is not a proxy model, "
        f"so claudex would bill the Anthropic subscription instead of the ChatGPT one"
    )
