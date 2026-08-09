import json


def test_window_navigation_no_longer_expands_into_the_buffer_close_chord(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "lazyvim_defaults.lua")
    result = run_headless_lua(
        "lazyvim_defaults_window_navigation.lua",
        f"""
        local buffer_was_closed = false
        vim.keymap.set("n", "<C-w>", function()
          buffer_was_closed = true
        end, {{ nowait = true }})
        vim.keymap.set("n", "<C-h>", "<C-w>h", {{ desc = "Go to Left Window", remap = true }})

        local function press_go_to_left_window()
          vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes("<C-h>", true, false, true), "x", false)
        end

        vim.cmd("vsplit")
        local left_window_id = vim.api.nvim_get_current_win()
        vim.cmd("wincmd l")
        local right_window_id = vim.api.nvim_get_current_win()

        press_go_to_left_window()
        assert(
          buffer_was_closed,
          "a remapped <C-w>h no longer reaches the <C-w> mapping, so this guard has nothing left to fix"
        )
        assert(
          vim.api.nvim_get_current_win() == right_window_id,
          "the unfixed navigation moved windows, so it never went through the buffer close chord"
        )

        local lazyvim_defaults = dofile({json.dumps(str(module_path))})
        lazyvim_defaults.rebind_window_navigation_to_bypass_the_buffer_close_chord()

        buffer_was_closed = false
        press_go_to_left_window()
        assert(not buffer_was_closed, "window navigation still closes the buffer instead of moving windows")
        assert(
          vim.api.nvim_get_current_win() == left_window_id,
          "window navigation did not reach the window on the left"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_lazyvim_window_resize_defaults_are_deleted(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "lazyvim_defaults.lua")
    result = run_headless_lua(
        "lazyvim_defaults_removal.lua",
        f"""
        vim.keymap.set("n", "<C-Left>", "<cmd>vertical resize -2<cr>", {{ desc = "Decrease Window Width" }})
        vim.keymap.set("n", "<C-Right>", "<cmd>vertical resize +2<cr>", {{ desc = "Increase Window Width" }})
        vim.keymap.set("n", "<C-Up>", "<cmd>resize +2<cr>", {{ desc = "Increase Window Height" }})
        vim.keymap.set("n", "<C-Down>", "<cmd>resize -2<cr>", {{ desc = "Decrease Window Height" }})

        local lazyvim_defaults = dofile({json.dumps(str(module_path))})
        lazyvim_defaults.remove_window_resize_keymaps()

        for _, chord in ipairs({{ "<C-Left>", "<C-Right>", "<C-Up>", "<C-Down>" }}) do
          local mapping = vim.fn.maparg(chord, "n", false, true)
          assert(
            mapping == nil or vim.tbl_isempty(mapping),
            chord .. " still resizes the window after the resize defaults were removed"
          )
        end

        lazyvim_defaults.remove_window_resize_keymaps()
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_height_resize_default_no_longer_walks_the_statusline_up_the_screen(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "lazyvim_defaults.lua")
    result = run_headless_lua(
        "lazyvim_defaults_statusline_displacement.lua",
        f"""
        vim.o.laststatus = 3
        vim.keymap.set("n", "<C-Down>", "<cmd>resize -2<cr>", {{ desc = "Decrease Window Height" }})

        local function press_decrease_window_height()
          vim.api.nvim_feedkeys(vim.api.nvim_replace_termcodes("<C-Down>", true, false, true), "x", false)
        end

        local resting_command_line_height = vim.o.cmdheight
        press_decrease_window_height()
        assert(
          vim.o.cmdheight > resting_command_line_height,
          "shrinking the only window no longer grows the command line, so this guard has nothing left to fix"
        )
        vim.o.cmdheight = resting_command_line_height

        local lazyvim_defaults = dofile({json.dumps(str(module_path))})
        lazyvim_defaults.remove_window_resize_keymaps()

        press_decrease_window_height()
        assert(
          vim.o.cmdheight == resting_command_line_height,
          "the height resize chord still pushes the statusline up the screen"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
