import shutil
from pathlib import Path

import pytest

from build_plugin import build_plugin, deliver_package


FIXTURE = Path(__file__).parents[1] / "fixtures/portable-plugin"


@pytest.mark.parametrize("targets", [(), ("pi", "hermes")])
def test_complete_package_needs_no_renderer(tmp_path, monkeypatch, targets):
    monkeypatch.delenv("DOTAGENTS_PLUGIN_BUILDER", raising=False)
    source = Path(shutil.copytree(FIXTURE, tmp_path / "source"))
    (source / "arbitrary-artifact.bin").write_bytes(bytes(range(256)))
    output = tmp_path / "output"
    build_plugin(source, output, targets)
    for path in source.rglob("*"):
        if path.is_file():
            assert (
                output / "plugin" / path.relative_to(source)
            ).read_bytes() == path.read_bytes()
    assert not (output / ".agents/skills").exists()


def test_authored_manifests_survive_renderer_changes(tmp_path):
    source = tmp_path / "source"
    native = source / ".claude-plugin"
    native.mkdir(parents=True)
    authored = '{"name":"example","hooks":"./custom-hooks.json"}'
    (native / "plugin.json").write_text(authored)
    output = tmp_path / "output"
    generated = output / ".agents/plugins/example/.claude-plugin"
    generated.mkdir(parents=True)
    (generated / "plugin.json").write_text('{"name":"example"}')
    deliver_package(source, output, "example", ())
    assert (generated / "plugin.json").read_text() == authored


def test_renderer_file_links_are_materialized_on_source_restoration(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "asset").write_bytes(b"opaque")
    (source / "link").symlink_to("asset")
    output = tmp_path / "output"
    generated = output / ".agents/plugins/example"
    generated.mkdir(parents=True)
    (generated / "asset").write_bytes(b"opaque")
    (generated / "link").symlink_to("asset")
    deliver_package(source, output, "example", ())
    assert not (generated / "link").is_symlink()
    assert (generated / "link").read_bytes() == b"opaque"
