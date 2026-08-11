import json


def test_tab_accepts_the_completion_and_enter_stays_a_newline(
    run_headless_lua, neovim_lua_path
):
    blink_plugin_path = neovim_lua_path("plugins", "blink-cmp.lua")
    result = run_headless_lua(
        "blink_completion_keymap.lua",
        f"""
        local lazyvim_blink_extra_defaults = {{
          keymap = {{
            preset = "enter",
            ["<C-y>"] = {{ "select_and_accept" }},
          }},
        }}

        local blink_plugin_spec = dofile({json.dumps(str(blink_plugin_path))})[1]
        local merged_opts =
          vim.tbl_deep_extend("force", lazyvim_blink_extra_defaults, blink_plugin_spec.opts)

        assert(
          merged_opts.keymap.preset == "super-tab",
          "the completion keymap preset is " .. tostring(merged_opts.keymap.preset)
            .. " instead of the one that accepts on tab"
        )
        assert(
          merged_opts.keymap["<CR>"] == nil,
          "the completion keymap binds <CR>, so enter accepts instead of opening a line"
        )
        assert(
          merged_opts.keymap["<C-y>"] ~= nil,
          "the override dropped LazyVim's <C-y> accept"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
