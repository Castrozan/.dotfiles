import json
import os
import subprocess
import textwrap
from pathlib import Path


def test_ctrl_shift_e_focuses_dashboard_and_preserves_other_picker_navigation(
    tmp_path,
):
    repository_root = Path(__file__).resolve().parents[5]
    file_explorer_config_path = (
        repository_root / ".config/nvim/lua/config/file_explorer.lua"
    )
    lua_script_path = tmp_path / "file_explorer_focus.lua"
    lua_script_path.write_text(
        textwrap.dedent(
            f"""
            local dashboard_window_id = vim.api.nvim_get_current_win()
            vim.bo.filetype = "snacks_dashboard"

            vim.cmd("vnew")
            vim.bo.filetype = "snacks_picker_input"

            vim.cmd("vnew")
            vim.bo.filetype = "snacks_picker_list"

            local active_explorer_pickers
            local explorer_picker = {{
              main = dashboard_window_id,
              focus = function() end,
            }}
            active_explorer_pickers = {{ explorer_picker }}

            _G.Snacks = {{
              explorer = function() end,
              picker = {{
                get = function()
                  return active_explorer_pickers
                end,
              }},
            }}

            dofile({json.dumps(str(file_explorer_config_path))})
            local mapping = vim.fn.maparg("<C-S-e>", "n", false, true)
            mapping.callback()
            assert(
              vim.api.nvim_get_current_win() == dashboard_window_id,
              "Ctrl-Shift-E did not focus the dashboard"
            )

            vim.cmd("tabnew")
            local editor_window_id = vim.api.nvim_get_current_win()
            vim.api.nvim_buf_set_name(0, "/tmp/open-file.lua")
            vim.cmd("vnew")
            vim.bo.filetype = "snacks_picker_list"
            active_explorer_pickers = {{}}
            mapping.callback()
            assert(
              vim.api.nvim_get_current_win() == editor_window_id,
              "Ctrl-Shift-E did not return from another picker to the editor"
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


def test_explorer_dims_gitignored_entries_only_and_not_every_dot_prefixed_entry(
    tmp_path,
):
    repository_root = Path(__file__).resolve().parents[5]
    explorer_plugin_path = (
        repository_root / ".config/nvim/lua/plugins/snacks-explorer.lua"
    )
    lua_script_path = tmp_path / "explorer_dimming.lua"
    lua_script_path.write_text(
        textwrap.dedent(
            f"""
            local explorer = dofile({json.dumps(str(explorer_plugin_path))})[1].opts.picker.sources.explorer

            local tracked_dot_directory = {{ file = "/repo/.husky", dir = true, hidden = true }}
            assert(
              explorer.transform(tracked_dot_directory) ~= false,
              "the explorer transform dropped a dot-prefixed entry from the tree"
            )
            assert(
              not tracked_dot_directory.hidden,
              "a tracked dot-prefixed entry is still flagged hidden and renders dimmed"
            )

            local gitignored_dot_directory = {{ file = "/repo/.logs", dir = true, hidden = true, ignored = true }}
            explorer.transform(gitignored_dot_directory)
            assert(
              gitignored_dot_directory.ignored,
              "a gitignored entry lost the flag that renders it dimmed"
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
