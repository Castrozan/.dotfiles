import json

EXPECTED_NORMAL_MODE_DESCRIPTIONS = {
    "<C-S-e>": "Toggle file explorer focus",
    "<C-S-Down>": "Jump 10 lines down",
    "<C-S-Up>": "Jump 10 lines up",
    "<C-S-j>": "Decrease window width",
    "<C-S-k>": "Increase window width",
    "<C-b>": "Toggle file explorer",
    "<C-`>": "Toggle terminal",
    "<C-p>": "Find files",
    "<S-F12>": "Find references",
}


def test_every_owned_chord_reaches_the_module_that_implements_it(
    run_headless_lua, neovim_lua_path, neovim_lua_directory
):
    keymaps_path = neovim_lua_path("config", "keymaps.lua")
    result = run_headless_lua(
        "keymaps_wiring.lua",
        f"""
        package.path = {json.dumps(str(neovim_lua_directory) + "/?.lua")} .. ";" .. package.path
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

        for _, mode in ipairs({{ "i", "v" }}) do
          for _, chord in ipairs({{ "<C-S-Down>", "<C-S-Up>" }}) do
            local mapping = vim.fn.maparg(chord, mode, false, true)
            assert(
              mapping and mapping.callback ~= nil,
              chord .. " lost its mapping in " .. mode .. " mode"
            )
          end
        end

        assert(
          vim.fn.execute("cabbrev Wq"):find("wq", 1, true) ~= nil,
          "the command line abbreviations were never installed"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_replaced_lazyvim_width_defaults_are_deleted(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "lazyvim_defaults.lua")
    result = run_headless_lua(
        "lazyvim_defaults_removal.lua",
        f"""
        vim.keymap.set("n", "<C-Left>", "<cmd>vertical resize -2<cr>", {{ desc = "Decrease Window Width" }})
        vim.keymap.set("n", "<C-Right>", "<cmd>vertical resize +2<cr>", {{ desc = "Increase Window Width" }})

        local lazyvim_defaults = dofile({json.dumps(str(module_path))})
        lazyvim_defaults.remove_replaced_keymaps()

        for _, chord in ipairs({{ "<C-Left>", "<C-Right>" }}) do
          local mapping = vim.fn.maparg(chord, "n", false, true)
          assert(
            mapping == nil or vim.tbl_isempty(mapping),
            chord .. " still resizes the window after the replaced defaults were removed"
          )
        end

        lazyvim_defaults.remove_replaced_keymaps()
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
