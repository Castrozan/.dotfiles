import json
import os
import subprocess
import textwrap
from pathlib import Path

KEYMAPS_MODULE_RELATIVE_PATH = (
    "machine-configuration/editors/neovim/program-configuration/lua/config/keymaps.lua"
)


def run_headless_lua(tmp_path, script_name, lua_body):
    repository_root = Path(__file__).resolve().parents[5]
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


def keymaps_module_path():
    return Path(__file__).resolve().parents[5] / KEYMAPS_MODULE_RELATIVE_PATH


def test_ctrl_shift_e_returns_focus_from_the_explorer_back_to_the_editor_window(
    tmp_path,
):
    result = run_headless_lua(
        tmp_path,
        "file_explorer_focus_returns_to_editor.lua",
        f"""
        local editor_window_id = vim.api.nvim_get_current_win()
        vim.bo.filetype = "snacks_dashboard"

        vim.cmd("vnew")
        vim.bo.filetype = "snacks_picker_input"

        vim.cmd("vnew")
        vim.bo.filetype = "snacks_picker_list"

        local active_explorer_pickers = {{
          {{ main = editor_window_id, focus = function() end }},
        }}
        _G.Snacks = {{
          explorer = function() end,
          picker = {{
            get = function()
              return active_explorer_pickers
            end,
          }},
        }}

        dofile({json.dumps(str(keymaps_module_path()))})
        local mapping = vim.fn.maparg("<C-S-e>", "n", false, true)
        assert(mapping.callback ~= nil, "Ctrl-Shift-E is not mapped in normal mode")

        mapping.callback()
        assert(
          vim.api.nvim_get_current_win() == editor_window_id,
          "Ctrl-Shift-E did not jump from the explorer to the window it was opened from"
        )

        vim.cmd("tabnew")
        local other_editor_window_id = vim.api.nvim_get_current_win()
        vim.cmd("vnew")
        vim.bo.filetype = "snacks_picker_list"
        active_explorer_pickers = {{}}
        mapping.callback()
        assert(
          vim.api.nvim_get_current_win() == other_editor_window_id,
          "Ctrl-Shift-E did not fall back to the previous window when no explorer picker was open"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_ctrl_shift_e_focuses_an_open_explorer_and_opens_one_when_none_is_open(
    tmp_path,
):
    result = run_headless_lua(
        tmp_path,
        "file_explorer_focus_enters_explorer.lua",
        f"""
        local explorer_was_opened = false
        local explorer_was_focused = false
        local active_explorer_pickers = {{}}
        _G.Snacks = {{
          explorer = function()
            explorer_was_opened = true
          end,
          picker = {{
            get = function()
              return active_explorer_pickers
            end,
          }},
        }}

        dofile({json.dumps(str(keymaps_module_path()))})
        local mapping = vim.fn.maparg("<C-S-e>", "n", false, true)

        mapping.callback()
        assert(explorer_was_opened, "Ctrl-Shift-E did not open the explorer while none was open")

        explorer_was_opened = false
        active_explorer_pickers = {{
          {{
            main = vim.api.nvim_get_current_win(),
            focus = function()
              explorer_was_focused = true
            end,
          }},
        }}
        mapping.callback()
        assert(explorer_was_focused, "Ctrl-Shift-E did not focus the explorer that was already open")
        assert(not explorer_was_opened, "Ctrl-Shift-E opened a second explorer instead of focusing the open one")
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
