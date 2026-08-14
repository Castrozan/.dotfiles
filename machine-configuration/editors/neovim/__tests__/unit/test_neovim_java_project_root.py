import json


def resolved_root_dir_lua(merged_java_opts_lua, java_source_path):
    return (
        merged_java_opts_lua()
        + f"""
        vim.cmd.edit({json.dumps(str(java_source_path))})
        local resolved_root_dir = merged_opts.root_dir(vim.api.nvim_buf_get_name(0))
        """
    )


def test_java_roots_a_single_module_maven_project_at_its_own_pom(
    run_headless_lua, merged_java_opts_lua, tmp_path
):
    java_project_path = tmp_path / "billing-service"
    java_source_path = java_project_path / "src/main/java/Application.java"
    java_source_path.parent.mkdir(parents=True)
    (java_project_path / "pom.xml").write_text("<project/>\n")
    java_source_path.write_text("public class Application {}\n")

    result = run_headless_lua(
        "java_root_single_module.lua",
        resolved_root_dir_lua(merged_java_opts_lua, java_source_path)
        + """
        assert(
          vim.fs.basename(resolved_root_dir) == "billing-service",
          "root_dir resolved to " .. tostring(resolved_root_dir) .. " instead of the maven project root"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_java_roots_a_maven_submodule_at_the_reactor_root(
    run_headless_lua, merged_java_opts_lua, tmp_path
):
    reactor_path = tmp_path / "orders-platform"
    reactor_path.mkdir()
    (reactor_path / "pom.xml").write_text(
        "<project><modules><module>orders-model</module>"
        "<module>orders-consumer</module></modules></project>\n"
    )
    for module_name in ("orders-model", "orders-consumer"):
        module_path = reactor_path / module_name
        (module_path / "src/main/java").mkdir(parents=True)
        (module_path / "pom.xml").write_text("<project/>\n")
    consumer_source_path = reactor_path / "orders-consumer/src/main/java/Consumer.java"
    consumer_source_path.write_text("public class Consumer {}\n")

    result = run_headless_lua(
        "java_root_maven_reactor.lua",
        resolved_root_dir_lua(merged_java_opts_lua, consumer_source_path)
        + """
        assert(
          vim.fs.basename(resolved_root_dir) == "orders-platform",
          "root_dir resolved to "
            .. tostring(resolved_root_dir)
            .. ", so the sibling modules stay out of the workspace, their artifacts never resolve"
            .. " and the maven import gives up before configuring the java nature"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_java_roots_a_gradle_submodule_at_the_settings_root(
    run_headless_lua, merged_java_opts_lua, tmp_path
):
    settings_root_path = tmp_path / "payments-platform"
    settings_root_path.mkdir()
    (settings_root_path / "settings.gradle").write_text("include 'ledger'\n")
    ledger_path = settings_root_path / "ledger"
    (ledger_path / "src/main/java").mkdir(parents=True)
    (ledger_path / "build.gradle").write_text("plugins { id 'java' }\n")
    ledger_source_path = ledger_path / "src/main/java/Ledger.java"
    ledger_source_path.write_text("public class Ledger {}\n")

    result = run_headless_lua(
        "java_root_gradle_reactor.lua",
        resolved_root_dir_lua(merged_java_opts_lua, ledger_source_path)
        + """
        assert(
          vim.fs.basename(resolved_root_dir) == "payments-platform",
          "root_dir resolved to "
            .. tostring(resolved_root_dir)
            .. " instead of the directory holding settings.gradle"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_java_scopes_a_file_with_no_build_file_to_the_directory_holding_it(
    run_headless_lua, merged_java_opts_lua, tmp_path
):
    drill_repository_path = tmp_path / "coding-drills"
    (drill_repository_path / ".git").mkdir(parents=True)
    for drill_name in ("01-tree-height", "02-level-order"):
        drill_path = drill_repository_path / "practice" / drill_name
        drill_path.mkdir(parents=True)
        (drill_path / "Solution.java").write_text("public class Solution {}\n")
    first_drill_source_path = (
        drill_repository_path / "practice/01-tree-height/Solution.java"
    )

    result = run_headless_lua(
        "java_root_invisible_project.lua",
        resolved_root_dir_lua(merged_java_opts_lua, first_drill_source_path)
        + """
        assert(
          vim.fs.basename(resolved_root_dir) == "01-tree-height",
          "root_dir resolved to "
            .. tostring(resolved_root_dir)
            .. ", so every Solution class in the repository lands in one project and collides"
        )

        local cwd_root_dir = merged_opts.root_dir("")
        assert(
          cwd_root_dir == vim.uv.cwd(),
          "a buffer with no file of its own resolved to " .. tostring(cwd_root_dir) .. " instead of the cwd"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
