import json
import os
import subprocess
import textwrap
from pathlib import Path


def test_java_override_keeps_lazyvim_jdtls_opts_and_resolves_project_root(tmp_path):
    repository_root = Path(__file__).resolve().parents[5]
    java_plugin_path = (
        repository_root
        / "machine-configuration/editors/neovim/program-configuration/lua/plugins/java.lua"
    )
    java_project_path = tmp_path / "billing-service"
    java_source_path = java_project_path / "src/main/java/Application.java"
    java_source_path.parent.mkdir(parents=True)
    (java_project_path / "pom.xml").write_text("<project/>\n")
    java_source_path.write_text("public class Application {}\n")

    lua_script_path = tmp_path / "java_jdtls_opts.lua"
    lua_script_path.write_text(
        textwrap.dedent(
            f"""
            local lazyvim_java_extra_defaults = {{
              cmd = {{ "jdtls" }},
              root_dir = function(path)
                return vim.fs.root(path, {{ "pom.xml" }})
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
              full_cmd = function(opts)
                local buffer_file_name = vim.api.nvim_buf_get_name(0)
                local root_dir = opts.root_dir(buffer_file_name)
                local project_name = opts.project_name(root_dir)
                local cmd = vim.deepcopy(opts.cmd)
                if project_name then
                  vim.list_extend(cmd, {{
                    "-configuration",
                    opts.jdtls_config_dir(project_name),
                    "-data",
                    opts.jdtls_workspace_dir(project_name),
                  }})
                end
                return cmd
              end,
            }}

            local java_plugin_spec = dofile({json.dumps(str(java_plugin_path))})[1]
            local merged_opts = java_plugin_spec.opts(java_plugin_spec, lazyvim_java_extra_defaults)

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
            """
        ).strip()
    )
    environment = dict(os.environ, XDG_STATE_HOME=str(tmp_path / "state"))
    result = subprocess.run(
        ["nvim", "--headless", "-u", "NONE", "-l", str(lua_script_path)],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
