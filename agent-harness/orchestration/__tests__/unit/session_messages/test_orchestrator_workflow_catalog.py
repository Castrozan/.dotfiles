import json

from orchestrator_cli.session_messages.workflow_catalog import (
    installed_workflow_purposes,
)


def test_the_installed_catalog_maps_each_command_to_its_purpose(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    catalog = tmp_path / "dotfiles/workflow-commands.json"
    catalog.parent.mkdir()
    catalog.write_text(
        json.dumps([{"command": "dotfiles-fix-loop", "purpose": "Fix a change"}])
    )
    assert installed_workflow_purposes() == {"dotfiles-fix-loop": "Fix a change"}


def test_a_machine_without_a_readable_catalog_has_no_installed_workflows(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert installed_workflow_purposes() == {}
    catalog = tmp_path / "dotfiles/workflow-commands.json"
    catalog.parent.mkdir()
    catalog.write_text("not json")
    assert installed_workflow_purposes() == {}
