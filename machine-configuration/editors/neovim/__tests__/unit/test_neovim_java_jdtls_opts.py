import json

LAZYVIM_JAVA_EXTRA_DEFAULTS = """
local lazyvim_java_extra_defaults = {
  cmd = { "jdtls" },
  root_dir = function(path)
    return vim.fs.root(path, { "pom.xml", "build.gradle", ".git" })
  end,
  project_name = function(root_dir)
    return root_dir and vim.fs.basename(root_dir)
  end,
  jdtls_config_dir = function(project_name)
    return vim.fn.stdpath("cache") .. "/jdtls/" .. project_name .. "/config"
  end,
  jdtls_workspace_dir = function(project_name)
    return vim.fn.stdpath("cache") .. "/jdtls/" .. project_name .. "/workspace"
  end,
  settings = {
    java = { inlayHints = { parameterNames = { enabled = "all" } } },
  },
  full_cmd = function(opts)
    local buffer_file_name = vim.api.nvim_buf_get_name(0)
    local root_dir = opts.root_dir(buffer_file_name)
    local project_name = opts.project_name(root_dir)
    local cmd = vim.deepcopy(opts.cmd)
    if project_name then
      vim.list_extend(cmd, {
        "-configuration",
        opts.jdtls_config_dir(project_name),
        "-data",
        opts.jdtls_workspace_dir(project_name),
      })
    end
    return cmd
  end,
}
"""


def merged_opts_lua(java_plugin_path):
    return (
        LAZYVIM_JAVA_EXTRA_DEFAULTS
        + f"""
        local java_plugin_spec = dofile({json.dumps(str(java_plugin_path))})[1]
        local merged_opts = java_plugin_spec.opts(java_plugin_spec, lazyvim_java_extra_defaults)
        """
    )


def test_java_override_keeps_lazyvim_jdtls_opts_and_resolves_project_root(
    run_headless_lua, neovim_lua_path, tmp_path
):
    java_plugin_path = neovim_lua_path("plugins", "java.lua")
    java_project_path = tmp_path / "billing-service"
    java_source_path = java_project_path / "src/main/java/Application.java"
    java_source_path.parent.mkdir(parents=True)
    (java_project_path / "pom.xml").write_text("<project/>\n")
    java_source_path.write_text("public class Application {}\n")

    result = run_headless_lua(
        "java_jdtls_opts.lua",
        merged_opts_lua(java_plugin_path)
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
        local resolved_root_dir = merged_opts.root_dir(vim.api.nvim_buf_get_name(0))
        assert(
          vim.fs.basename(resolved_root_dir) == "billing-service",
          "root_dir resolved to " .. tostring(resolved_root_dir) .. " instead of the maven project root"
        )

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


def test_java_scopes_a_file_with_no_build_file_to_the_directory_holding_it(
    run_headless_lua, neovim_lua_path, tmp_path
):
    java_plugin_path = neovim_lua_path("plugins", "java.lua")
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
        "java_jdtls_invisible_project.lua",
        merged_opts_lua(java_plugin_path)
        + f"""
        vim.cmd.edit({json.dumps(str(first_drill_source_path))})
        local resolved_root_dir = merged_opts.root_dir(vim.api.nvim_buf_get_name(0))
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
