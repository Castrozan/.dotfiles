import shutil
import stat
import subprocess
from pathlib import Path

import pytest

import build_plugin


FIXTURE = Path(__file__).parents[1] / "fixtures" / "portable-plugin"


def test_readonly_input_is_materialized_without_mutating_source(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    executable = source / "script"
    executable.write_text("preserve executable permissions")
    executable.chmod(0o555)
    output = tmp_path / "output"
    output.mkdir()
    build_plugin.prepare_workspace(source, output, "example", ("claude",))
    copied = output / "input/script"
    assert copied.stat().st_mode & stat.S_IWUSR
    assert copied.stat().st_mode & stat.S_IXUSR
    assert not executable.stat().st_mode & stat.S_IWUSR
    assert copied.read_bytes() == executable.read_bytes()


def test_existing_output_is_untouched(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    sentinel = output / "user-file"
    sentinel.write_text("preserve")
    with pytest.raises(FileExistsError):
        build_plugin.build_plugin(FIXTURE, output, ("claude",))
    assert sentinel.read_text() == "preserve"
    assert list(output.iterdir()) == [sentinel]


def test_output_inside_source_is_rejected(tmp_path):
    source = Path(shutil.copytree(FIXTURE, tmp_path / "plugin"))
    output = source / "generated"
    with pytest.raises(ValueError, match="outside the plugin source"):
        build_plugin.build_plugin(source, output, ("claude",))
    assert not output.exists()


def test_partial_build_is_removed_on_adapter_failure(tmp_path, monkeypatch):
    def fail_install(command, output, environment):
        (output / "partial").write_text("incomplete")
        raise ValueError("unsupported")

    monkeypatch.setattr(build_plugin, "run_dotagents", fail_install)
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="unsupported"):
        build_plugin.build_plugin(FIXTURE, output, ("claude",))
    assert not output.exists()


@pytest.mark.parametrize(
    ("exit_code", "diagnostic"), [(0, "  warn: MCP skipped"), (1, "failed")]
)
def test_adapter_warning_is_failure(tmp_path, monkeypatch, exit_code, diagnostic):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], exit_code, diagnostic, ""
        ),
    )
    with pytest.raises(ValueError, match="dotagents install failed"):
        build_plugin.run_dotagents(
            "install", tmp_path, {"DOTAGENTS_PLUGIN_BUILDER": "dotagents"}
        )
