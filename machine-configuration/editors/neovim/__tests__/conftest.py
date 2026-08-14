import json
import os
import subprocess
import textwrap
from pathlib import Path

import pytest

NEOVIM_LUA_RELATIVE_PATH = (
    "machine-configuration/editors/neovim/program-configuration/lua"
)

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


@pytest.fixture
def repository_root():
    return Path(__file__).resolve().parents[4]


@pytest.fixture
def neovim_lua_directory(repository_root):
    return repository_root / NEOVIM_LUA_RELATIVE_PATH


@pytest.fixture
def neovim_lua_path(neovim_lua_directory):
    def build_module_path(*module_path_parts):
        return neovim_lua_directory / Path(*module_path_parts)

    return build_module_path


@pytest.fixture
def merged_java_opts_lua(neovim_lua_path):
    """Lua prelude that merges java.lua's override into LazyVim's jdtls defaults."""

    def build_prelude():
        java_plugin_path = neovim_lua_path("plugins", "java.lua")
        return (
            LAZYVIM_JAVA_EXTRA_DEFAULTS
            + f"""
            local java_plugin_spec = dofile({json.dumps(str(java_plugin_path))})[1]
            local merged_opts = java_plugin_spec.opts(java_plugin_spec, lazyvim_java_extra_defaults)
            """
        )

    return build_prelude


@pytest.fixture
def run_headless_lua(repository_root, tmp_path):
    def run(script_name, lua_body):
        lua_script_path = tmp_path / script_name
        lua_script_path.write_text(textwrap.dedent(lua_body).strip())
        environment = dict(os.environ, XDG_STATE_HOME=str(tmp_path / "state"))
        return subprocess.run(
            ["nvim", "--headless", "-u", "NONE", "-l", str(lua_script_path)],
            cwd=repository_root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    return run
