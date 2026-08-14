import json


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
