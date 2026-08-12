import pathlib
import shutil

from claude_plugin_discovery import read_skill_directories_of_every_enabled_plugin

home_directory = pathlib.Path.home()
opencode_skills_directory = home_directory / ".config" / "opencode" / "skills"
ported_skills_root = home_directory / ".config" / "opencode" / "claude-plugin-ports"


def previously_ported_skill_links():
    if not opencode_skills_directory.is_dir():
        return []
    return [
        skill_link
        for skill_link in opencode_skills_directory.iterdir()
        if skill_link.is_symlink()
        and ported_skills_root in pathlib.Path(skill_link.readlink()).parents
    ]


def copy_plugin_skills_into_the_ports_root(plugin_skill_directories):
    if ported_skills_root.exists():
        shutil.rmtree(ported_skills_root)
    ported_skill_directories = {}
    for plugin_name, skills_directory in plugin_skill_directories.items():
        for skill_directory in sorted(skills_directory.iterdir()):
            if not (skill_directory / "SKILL.md").is_file():
                continue
            destination = ported_skills_root / plugin_name / skill_directory.name
            shutil.copytree(skill_directory, destination)
            ported_skill_directories[skill_directory.name] = destination
    return ported_skill_directories


def link_ported_skills_into_the_opencode_skill_tier(ported_skill_directories):
    for stale_skill_link in previously_ported_skill_links():
        stale_skill_link.unlink()
    opencode_skills_directory.mkdir(parents=True, exist_ok=True)
    linked_skill_names = []
    for skill_name, ported_skill_directory in sorted(ported_skill_directories.items()):
        skill_link = opencode_skills_directory / skill_name
        if skill_link.is_symlink() or skill_link.exists():
            continue
        skill_link.symlink_to(ported_skill_directory, target_is_directory=True)
        linked_skill_names.append(skill_name)
    return linked_skill_names


def main():
    plugin_skill_directories = read_skill_directories_of_every_enabled_plugin()
    if not plugin_skill_directories:
        for stale_skill_link in previously_ported_skill_links():
            stale_skill_link.unlink()
        if ported_skills_root.exists():
            shutil.rmtree(ported_skills_root)
        return
    ported_skill_directories = copy_plugin_skills_into_the_ports_root(
        plugin_skill_directories
    )
    linked_skill_names = link_ported_skills_into_the_opencode_skill_tier(
        ported_skill_directories
    )
    if linked_skill_names:
        print(
            f"ported {len(linked_skill_names)} Claude plugin skill(s) into OpenCode: "
            + ", ".join(linked_skill_names)
        )


if __name__ == "__main__":
    main()
