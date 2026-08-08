import json
import os
import subprocess
import textwrap
from pathlib import Path

NEOVIM_LUA_RELATIVE_PATH = (
    "machine-configuration/editors/neovim/program-configuration/lua"
)


def repository_root():
    return Path(__file__).resolve().parents[5]


def neovim_lua_path(*module_path_parts):
    return repository_root() / NEOVIM_LUA_RELATIVE_PATH / Path(*module_path_parts)


def run_headless_lua(tmp_path, script_name, lua_body):
    lua_script_path = tmp_path / script_name
    lua_script_path.write_text(textwrap.dedent(lua_body).strip())
    environment = dict(os.environ, XDG_STATE_HOME=str(tmp_path / "state"))
    return subprocess.run(
        ["nvim", "--headless", "-u", "NONE", "-l", str(lua_script_path)],
        cwd=repository_root(),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_toggle_returns_focus_from_the_explorer_back_to_the_editor_window(tmp_path):
    module_path = neovim_lua_path("config", "navigation", "file_explorer_focus.lua")
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

        local file_explorer_focus = dofile({json.dumps(str(module_path))})
        file_explorer_focus.toggle_between_editor_and_file_explorer()
        assert(
          vim.api.nvim_get_current_win() == editor_window_id,
          "the toggle did not jump from the explorer to the window it was opened from"
        )

        vim.cmd("tabnew")
        local other_editor_window_id = vim.api.nvim_get_current_win()
        vim.cmd("vnew")
        vim.bo.filetype = "snacks_picker_list"
        active_explorer_pickers = {{}}
        file_explorer_focus.toggle_between_editor_and_file_explorer()
        assert(
          vim.api.nvim_get_current_win() == other_editor_window_id,
          "the toggle did not fall back to the previous window when no explorer picker was open"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_toggle_focuses_an_open_explorer_and_opens_one_when_none_is_open(tmp_path):
    module_path = neovim_lua_path("config", "navigation", "file_explorer_focus.lua")
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

        local file_explorer_focus = dofile({json.dumps(str(module_path))})
        file_explorer_focus.toggle_between_editor_and_file_explorer()
        assert(explorer_was_opened, "the toggle did not open the explorer while none was open")

        explorer_was_opened = false
        active_explorer_pickers = {{
          {{
            main = vim.api.nvim_get_current_win(),
            focus = function()
              explorer_was_focused = true
            end,
          }},
        }}
        file_explorer_focus.toggle_between_editor_and_file_explorer()
        assert(explorer_was_focused, "the toggle did not focus the explorer that was already open")
        assert(not explorer_was_opened, "the toggle opened a second explorer instead of focusing the open one")
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_keymaps_wire_the_owned_navigation_chords_to_the_extracted_modules(tmp_path):
    lua_directory = repository_root() / NEOVIM_LUA_RELATIVE_PATH
    keymaps_path = neovim_lua_path("config", "keymaps.lua")
    result = run_headless_lua(
        tmp_path,
        "navigation_keymap_wiring.lua",
        f"""
        package.path = {json.dumps(str(lua_directory) + "/?.lua")} .. ";" .. package.path
        dofile({json.dumps(str(keymaps_path))})

        local expected_descriptions = {{
          ["<C-S-e>"] = "Toggle file explorer focus",
          ["<C-S-Down>"] = "Jump 10 lines down",
          ["<C-S-Up>"] = "Jump 10 lines up",
        }}
        for chord, expected_description in pairs(expected_descriptions) do
          local mapping = vim.fn.maparg(chord, "n", false, true)
          assert(
            mapping and mapping.desc == expected_description,
            chord .. " is mapped to " .. vim.inspect(mapping and mapping.desc) .. " in normal mode"
          )
        end

        for _, mode in ipairs({{ "i", "v" }}) do
          for _, chord in ipairs({{ "<C-S-Down>", "<C-S-Up>" }}) do
            local mapping = vim.fn.maparg(chord, mode, false, true)
            assert(
              mapping and mapping.callback ~= nil,
              chord .. " lost its mapping in " .. mode .. " mode"
            )
          end
        end
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
