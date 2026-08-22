import re
from pathlib import Path

GPT_PROXY_MODULE = Path(__file__).resolve().parents[2] / "default.nix"
LAUNCHER_EXEC_LINE = re.compile(r"^\s*exec \S+/bin/claude .*$", re.M)


def module_source() -> str:
    return GPT_PROXY_MODULE.read_text()


def test_claudex_pins_the_declared_proxy_model():
    source = module_source()
    matched = LAUNCHER_EXEC_LINE.search(source)
    assert matched, "claudex no longer execs Claude Code"
    launcher_exec_line = matched.group(0)
    assert "--model" in launcher_exec_line, (
        "claudex must pass --model explicitly: the deployed settings.json pins a "
        "concrete model, so the ANTHROPIC_DEFAULT_OPUS_MODEL alias never takes effect "
        "and the launcher would silently run on the Anthropic model instead of the proxy"
    )
    declared = re.search(r'gptModelForOpusTier = "([^"]+)"', source)
    assert declared, "gptModelForOpusTier is no longer declared in the module"
    assert "${gptModelForOpusTier}" in launcher_exec_line, (
        "the launcher passes a model other than the declared opus tier binding, "
        "so the exported alias and the passed model can drift apart silently"
    )
    assert declared.group(1).startswith("gpt-"), (
        f"the opus tier is pinned to {declared.group(1)}, which is not a proxy model, "
        f"so claudex would bill the Anthropic subscription instead of the ChatGPT one"
    )
