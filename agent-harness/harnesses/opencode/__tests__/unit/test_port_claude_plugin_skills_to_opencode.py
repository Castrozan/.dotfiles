import pytest

import port_claude_plugin_skills_to_opencode as porter


def write_plugin_skill(skills_directory, skill_name):
    skill_directory = skills_directory / skill_name
    skill_directory.mkdir(parents=True)
    (skill_directory / "SKILL.md").write_text(f"name: {skill_name}")
    return skill_directory


@pytest.fixture
def opencode_home(tmp_path, monkeypatch):
    skills_directory = tmp_path / "opencode" / "skills"
    ports_root = tmp_path / "opencode" / "claude-plugin-ports"
    monkeypatch.setattr(porter, "opencode_skills_directory", skills_directory)
    monkeypatch.setattr(porter, "ported_skills_root", ports_root)
    return skills_directory, ports_root


def test_every_plugin_skill_reaches_the_opencode_skill_tier(opencode_home, tmp_path):
    skills_directory, ports_root = opencode_home
    plugin_skills = tmp_path / "plugin" / "skills"
    write_plugin_skill(plugin_skills, "mcd-ca-jira")
    write_plugin_skill(plugin_skills, "mcd-ca-deploy")

    porter.link_ported_skills_into_the_opencode_skill_tier(
        porter.copy_plugin_skills_into_the_ports_root({"mcd-ca": plugin_skills})
    )

    assert (skills_directory / "mcd-ca-jira" / "SKILL.md").read_text() == (
        "name: mcd-ca-jira"
    )
    assert (ports_root / "mcd-ca" / "mcd-ca-deploy" / "SKILL.md").is_file()


def test_a_directory_without_a_skill_file_is_not_ported(opencode_home, tmp_path):
    skills_directory, _ = opencode_home
    plugin_skills = tmp_path / "plugin" / "skills"
    (plugin_skills / "not-a-skill").mkdir(parents=True)
    write_plugin_skill(plugin_skills, "mcd-ca-jira")

    porter.link_ported_skills_into_the_opencode_skill_tier(
        porter.copy_plugin_skills_into_the_ports_root({"mcd-ca": plugin_skills})
    )

    assert not (skills_directory / "not-a-skill").exists()


def test_a_skill_the_nix_tier_already_deploys_is_never_replaced(
    opencode_home, tmp_path
):
    skills_directory, _ = opencode_home
    nix_deployed_skill = tmp_path / "nix-store-skill"
    nix_deployed_skill.mkdir()
    (nix_deployed_skill / "SKILL.md").write_text("name: deployed-by-nix")
    skills_directory.mkdir(parents=True)
    (skills_directory / "mcd-ca-jira").symlink_to(
        nix_deployed_skill, target_is_directory=True
    )
    plugin_skills = tmp_path / "plugin" / "skills"
    write_plugin_skill(plugin_skills, "mcd-ca-jira")

    porter.link_ported_skills_into_the_opencode_skill_tier(
        porter.copy_plugin_skills_into_the_ports_root({"mcd-ca": plugin_skills})
    )

    assert (skills_directory / "mcd-ca-jira" / "SKILL.md").read_text() == (
        "name: deployed-by-nix"
    )


def test_a_skill_the_plugin_dropped_stops_being_linked(opencode_home, tmp_path):
    skills_directory, _ = opencode_home
    plugin_skills = tmp_path / "plugin" / "skills"
    write_plugin_skill(plugin_skills, "mcd-ca-jira")
    write_plugin_skill(plugin_skills, "mcd-ca-retired")
    porter.link_ported_skills_into_the_opencode_skill_tier(
        porter.copy_plugin_skills_into_the_ports_root({"mcd-ca": plugin_skills})
    )

    (plugin_skills / "mcd-ca-retired" / "SKILL.md").unlink()
    (plugin_skills / "mcd-ca-retired").rmdir()
    porter.link_ported_skills_into_the_opencode_skill_tier(
        porter.copy_plugin_skills_into_the_ports_root({"mcd-ca": plugin_skills})
    )

    assert (skills_directory / "mcd-ca-jira").is_symlink()
    assert not (skills_directory / "mcd-ca-retired").is_symlink()
