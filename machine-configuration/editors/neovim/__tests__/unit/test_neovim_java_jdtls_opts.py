import json


def test_java_registers_the_nix_java_eight_runtime(
    run_headless_lua, merged_java_opts_lua
):
    result = run_headless_lua(
        "java_jdtls_runtimes.lua",
        'vim.env.JAVA_8_HOME = "/nix/store/stub-jdk8"\n'
        + merged_java_opts_lua()
        + """
        local runtimes = merged_opts.settings.java.configuration.runtimes
        assert(
          runtimes and runtimes[1] and runtimes[1].name == "JavaSE-1.8",
          "jdtls got no JavaSE-1.8 runtime, so it compiles a project pinned to 1.8 with its own"
            .. " jdk21 and reports errors the project's own build never sees"
        )
        assert(
          runtimes[1].path == "/nix/store/stub-jdk8",
          "the JavaSE-1.8 runtime points at " .. tostring(runtimes[1].path) .. " instead of the nix jdk8"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_java_omits_the_runtime_when_nix_exports_no_java_eight_home(
    run_headless_lua, merged_java_opts_lua
):
    result = run_headless_lua(
        "java_jdtls_no_runtimes.lua",
        "vim.env.JAVA_8_HOME = nil\n"
        + merged_java_opts_lua()
        + """
        assert(
          vim.tbl_isempty(merged_opts.settings.java.configuration or {}),
          "java.lua invented a runtime entry with no java 8 home to point it at"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_java_override_keeps_lazyvim_jdtls_opts(
    run_headless_lua, merged_java_opts_lua, tmp_path
):
    java_project_path = tmp_path / "billing-service"
    java_source_path = java_project_path / "src/main/java/Application.java"
    java_source_path.parent.mkdir(parents=True)
    (java_project_path / "pom.xml").write_text("<project/>\n")
    java_source_path.write_text("public class Application {}\n")

    result = run_headless_lua(
        "java_jdtls_opts.lua",
        merged_java_opts_lua()
        + f"""
        assert(
          type(merged_opts) == "table",
          "the nvim-jdtls opts override returned no table for lazy.nvim to use"
        )
        for _, preserved_field in ipairs({{
          "full_cmd",
          "project_name",
          "jdtls_config_dir",
          "jdtls_workspace_dir",
        }}) do
          assert(
            type(merged_opts[preserved_field]) == "function",
            "the nvim-jdtls opts override dropped LazyVim's " .. preserved_field
          )
        end
        assert(
          type(merged_opts.root_dir) == "function",
          "LazyVim calls root_dir as a function, so the override must not replace it with a value"
        )
        assert(
          merged_opts.settings.java.inlayHints.parameterNames.enabled == "all",
          "the java settings override replaced LazyVim's settings instead of merging into them"
        )
        assert(
          vim.tbl_contains(merged_opts.settings.java.import.exclusions, "**/.devenv/**"),
          "the java server would import the nix store symlinks under .devenv"
        )

        vim.cmd.edit({json.dumps(str(java_source_path))})
        local launch_command = merged_opts.full_cmd(merged_opts)
        assert(
          vim.tbl_contains(launch_command, "-configuration") and vim.tbl_contains(launch_command, "-data"),
          "full_cmd produced no jdtls configuration and workspace directories: "
            .. table.concat(launch_command, " ")
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
