import json


def test_toggle_returns_focus_from_the_explorer_back_to_the_editor_window(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "navigation", "file_explorer.lua")
    result = run_headless_lua(
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

        local file_explorer = dofile({json.dumps(str(module_path))})
        file_explorer.toggle_focus()
        assert(
          vim.api.nvim_get_current_win() == editor_window_id,
          "the toggle did not jump from the explorer to the window it was opened from"
        )

        vim.cmd("tabnew")
        local other_editor_window_id = vim.api.nvim_get_current_win()
        vim.cmd("vnew")
        vim.bo.filetype = "snacks_picker_list"
        active_explorer_pickers = {{}}
        file_explorer.toggle_focus()
        assert(
          vim.api.nvim_get_current_win() == other_editor_window_id,
          "the toggle did not fall back to the previous window when no explorer picker was open"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_toggle_focuses_an_open_explorer_and_opens_one_when_none_is_open(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "navigation", "file_explorer.lua")
    result = run_headless_lua(
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

        local file_explorer = dofile({json.dumps(str(module_path))})
        file_explorer.toggle_focus()
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
        file_explorer.toggle_focus()
        assert(explorer_was_focused, "the toggle did not focus the explorer that was already open")
        assert(not explorer_was_opened, "the toggle opened a second explorer instead of focusing the open one")
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
