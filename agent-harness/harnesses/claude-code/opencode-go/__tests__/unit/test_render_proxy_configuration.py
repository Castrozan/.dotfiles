import importlib.util
import stat
from pathlib import Path

import pytest

RENDERER_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "render_proxy_configuration_and_exec.py"
)
RENDERER_SPECIFICATION = importlib.util.spec_from_file_location(
    "render_proxy_configuration_and_exec", RENDERER_PATH
)
assert RENDERER_SPECIFICATION
assert RENDERER_SPECIFICATION.loader
RENDERER = importlib.util.module_from_spec(RENDERER_SPECIFICATION)
RENDERER_SPECIFICATION.loader.exec_module(RENDERER)

CONFIGURATION_TEMPLATE = 'api-key-entries:\n  - api-key: "@OPENCODE_GO_API_KEY@"\n'


class RecordedExec:
    def __init__(self):
        self.invocations = []

    def __call__(self, program_path, arguments):
        self.invocations.append((program_path, arguments))


def write_template_and_key(
    tmp_path: Path, api_key_text: str
) -> tuple[Path, Path, Path]:
    template_path = tmp_path / "template.yaml"
    template_path.write_text(CONFIGURATION_TEMPLATE)
    api_key_path = tmp_path / "opencode-api-key"
    api_key_path.write_text(api_key_text)
    return template_path, api_key_path, tmp_path / "state" / "config.yaml"


def test_the_rendered_configuration_carries_the_key_and_the_template_never_does(
    tmp_path,
):
    template_path, api_key_path, rendered_path = write_template_and_key(
        tmp_path, "sk-console-go-key\n"
    )
    recorded_exec = RecordedExec()

    exit_code = RENDERER.render_configuration_then_exec_proxy(
        template_path,
        api_key_path,
        rendered_path,
        ["/usr/bin/cli-proxy-api", "--config", str(rendered_path)],
        exec_program=recorded_exec,
    )

    assert exit_code == 0
    assert "sk-console-go-key" in rendered_path.read_text()
    assert RENDERER.API_KEY_PLACEHOLDER not in rendered_path.read_text()
    assert RENDERER.API_KEY_PLACEHOLDER in template_path.read_text()


def test_the_rendered_configuration_is_readable_only_by_its_owner(tmp_path):
    template_path, api_key_path, rendered_path = write_template_and_key(
        tmp_path, "sk-console-go-key\n"
    )

    RENDERER.render_configuration_then_exec_proxy(
        template_path,
        api_key_path,
        rendered_path,
        ["/usr/bin/cli-proxy-api"],
        exec_program=RecordedExec(),
    )

    assert stat.S_IMODE(rendered_path.stat().st_mode) == 0o600, (
        "the rendered file holds the plan's API key, so no other account may read it"
    )


def test_the_proxy_is_started_only_after_the_configuration_exists(tmp_path):
    template_path, api_key_path, rendered_path = write_template_and_key(
        tmp_path, "sk-console-go-key\n"
    )
    observed_configuration_at_exec = []

    def exec_program(program_path, arguments):
        observed_configuration_at_exec.append(rendered_path.is_file())

    RENDERER.render_configuration_then_exec_proxy(
        template_path,
        api_key_path,
        rendered_path,
        ["/usr/bin/cli-proxy-api"],
        exec_program=exec_program,
    )

    assert observed_configuration_at_exec == [True], (
        "the proxy reads its config at startup, so rendering must complete first"
    )


@pytest.mark.parametrize("api_key_text", ["", "   \n"])
def test_an_empty_key_fails_before_the_proxy_starts(tmp_path, api_key_text):
    template_path, api_key_path, rendered_path = write_template_and_key(
        tmp_path, api_key_text
    )
    recorded_exec = RecordedExec()

    exit_code = RENDERER.render_configuration_then_exec_proxy(
        template_path,
        api_key_path,
        rendered_path,
        ["/usr/bin/cli-proxy-api"],
        exec_program=recorded_exec,
    )

    assert exit_code == RENDERER.UNUSABLE_API_KEY_EXIT_CODE
    assert recorded_exec.invocations == [], (
        "a proxy started without a key answers every request with an upstream authentication failure"
    )


def test_a_missing_key_file_fails_before_the_proxy_starts(tmp_path):
    template_path, _, rendered_path = write_template_and_key(tmp_path, "unused")
    recorded_exec = RecordedExec()

    exit_code = RENDERER.render_configuration_then_exec_proxy(
        template_path,
        tmp_path / "absent-key",
        rendered_path,
        ["/usr/bin/cli-proxy-api"],
        exec_program=recorded_exec,
    )

    assert exit_code == RENDERER.UNUSABLE_API_KEY_EXIT_CODE
    assert recorded_exec.invocations == []


def test_a_template_without_the_placeholder_is_rejected(tmp_path):
    template_path = tmp_path / "template.yaml"
    template_path.write_text('api-key-entries:\n  - api-key: ""\n')
    api_key_path = tmp_path / "opencode-api-key"
    api_key_path.write_text("sk-console-go-key\n")

    with pytest.raises(ValueError):
        RENDERER.render_configuration_then_exec_proxy(
            template_path,
            api_key_path,
            tmp_path / "config.yaml",
            ["/usr/bin/cli-proxy-api"],
            exec_program=RecordedExec(),
        )
