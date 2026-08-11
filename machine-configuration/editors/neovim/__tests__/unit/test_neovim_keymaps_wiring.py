import json

EXPECTED_NORMAL_MODE_DESCRIPTIONS = {
    "<C-S-e>": "Toggle file explorer focus",
    "<C-S-Down>": "Jump 10 lines down",
    "<C-S-Up>": "Jump 10 lines up",
    "<C-S-j>": "Increase window width",
    "<C-S-k>": "Decrease window width",
    "<C-Up>": "Scroll view up one line",
    "<C-Down>": "Scroll view down one line",
    "<C-n>": "Create file in current directory",
    "<C-S-b>": "Toggle file explorer",
    "<C-w>": "Close buffer (focus next or prev)",
    "<C-`>": "Toggle terminal",
    "<C-p>": "Find files",
    "<S-F12>": "Find references",
    "<C-PageUp>": "Previous open file",
    "<C-PageDown>": "Next open file",
    "<C-;>": "Toggle comment",
    "<C-Left>": "Jump to previous word in the line",
    "<C-Right>": "Jump to next word in the line",
    "<C-.>": "Show symbol information",
    "<C-CR>": "Import the symbol under the cursor",
}

EXPECTED_VISUAL_MODE_DESCRIPTIONS = {
    "<C-;>": "Toggle comment (visual)",
    "<C-/>": "Toggle comment (visual)",
    "<C-Left>": "Jump to previous word in the line",
    "<C-Right>": "Jump to next word in the line",
}

EXPECTED_INSERT_MODE_DESCRIPTIONS = {
    "<C-S-j>": "Increase window width",
    "<C-S-k>": "Decrease window width",
    "<C-Up>": "Scroll view up one line",
    "<C-Down>": "Scroll view down one line",
    "<C-PageUp>": "Previous open file",
    "<C-PageDown>": "Next open file",
    "<C-Left>": "Jump to previous word in the line",
    "<C-Right>": "Jump to next word in the line",
}

EXPECTED_OPEN_FILE_CYCLE_COMMANDS = {
    "<C-PageUp>": "BufferLineCyclePrev",
    "<C-PageDown>": "BufferLineCycleNext",
}

EXPECTED_WIDTH_RESIZE_COMMANDS = {
    "<C-S-j>": "vertical resize +2",
    "<C-S-k>": "vertical resize -2",
}


def test_every_owned_chord_reaches_the_module_that_implements_it(
    run_headless_lua, neovim_lua_path, neovim_lua_directory
):
    keymaps_path = neovim_lua_path("config", "keymaps.lua")
    result = run_headless_lua(
        "keymaps_wiring.lua",
        f"""
        package.path = {json.dumps(str(neovim_lua_directory) + "/?.lua")} .. ";" .. package.path
        vim.keymap.set("n", "<C-Up>", "<cmd>resize +2<cr>", {{ desc = "Increase Window Height" }})
        vim.keymap.set("n", "<C-Down>", "<cmd>resize -2<cr>", {{ desc = "Decrease Window Height" }})
        dofile({json.dumps(str(keymaps_path))})

        local expected_descriptions =
          vim.fn.json_decode({json.dumps(json.dumps(EXPECTED_NORMAL_MODE_DESCRIPTIONS))})
        for chord, expected_description in pairs(expected_descriptions) do
          local mapping = vim.fn.maparg(chord, "n", false, true)
          assert(
            mapping and mapping.desc == expected_description,
            chord .. " is mapped to " .. vim.inspect(mapping and mapping.desc) .. " in normal mode"
          )
        end

        local expected_insert_descriptions =
          vim.fn.json_decode({json.dumps(json.dumps(EXPECTED_INSERT_MODE_DESCRIPTIONS))})
        for chord, expected_description in pairs(expected_insert_descriptions) do
          local mapping = vim.fn.maparg(chord, "i", false, true)
          assert(
            mapping and mapping.desc == expected_description,
            chord .. " is mapped to " .. vim.inspect(mapping and mapping.desc) .. " in insert mode"
          )
        end

        for _, chord in ipairs({{ "<C-Up>", "<C-Down>" }}) do
          local mapping = vim.fn.maparg(chord, "v", false, true)
          assert(
            mapping and mapping.desc ~= nil,
            chord .. " lost its scroll mapping in visual mode"
          )
        end

        local expected_visual_descriptions =
          vim.fn.json_decode({json.dumps(json.dumps(EXPECTED_VISUAL_MODE_DESCRIPTIONS))})
        for chord, expected_description in pairs(expected_visual_descriptions) do
          local mapping = vim.fn.maparg(chord, "v", false, true)
          assert(
            mapping and mapping.desc == expected_description,
            chord .. " is mapped to " .. vim.inspect(mapping and mapping.desc) .. " in visual mode"
          )
        end

        local expected_resize_commands =
          vim.fn.json_decode({json.dumps(json.dumps(EXPECTED_WIDTH_RESIZE_COMMANDS))})
        for chord, expected_command in pairs(expected_resize_commands) do
          local mapping = vim.fn.maparg(chord, "n", false, true)
          assert(
            mapping and mapping.rhs and mapping.rhs:find(expected_command, 1, true) ~= nil,
            chord .. " runs " .. vim.inspect(mapping and mapping.rhs) .. " instead of " .. expected_command
          )
        end

        local expected_cycle_commands =
          vim.fn.json_decode({json.dumps(json.dumps(EXPECTED_OPEN_FILE_CYCLE_COMMANDS))})
        for chord, expected_command in pairs(expected_cycle_commands) do
          local mapping = vim.fn.maparg(chord, "n", false, true)
          assert(
            mapping and mapping.rhs and mapping.rhs:find(expected_command, 1, true) ~= nil,
            chord .. " runs " .. vim.inspect(mapping and mapping.rhs) .. " instead of " .. expected_command
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

        local insert_mode_buffer_close = vim.fn.maparg("<C-w>", "i", false, true)
        assert(
          insert_mode_buffer_close and insert_mode_buffer_close.callback ~= nil,
          "<C-w> lost its mapping in insert mode"
        )

        for _, mode in ipairs({{ "n", "i" }}) do
          assert(
            vim.fn.maparg("<C-w>", mode, false, true).nowait == 1,
            "<C-w> waits for a window command key in " .. mode .. " mode instead of closing the buffer"
          )
        end

        assert(
          vim.fn.execute("cabbrev Wq"):find("wq", 1, true) ~= nil,
          "the command line abbreviations were never installed"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
