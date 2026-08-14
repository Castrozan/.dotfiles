import json

FLOAT_HIGHLIGHT_GROUPS = (
    "NormalFloat",
    "FloatBorder",
    "FloatTitle",
    "NoiceScrollbar",
)


def test_transparency_clears_the_background_behind_floating_windows(
    run_headless_lua, neovim_lua_directory
):
    program_configuration_path = neovim_lua_directory.parent
    float_highlight_groups_lua = ", ".join(
        json.dumps(group_name) for group_name in FLOAT_HIGHLIGHT_GROUPS
    )

    result = run_headless_lua(
        "float_transparency.lua",
        f"""
        vim.opt.runtimepath:prepend({json.dumps(str(program_configuration_path))})

        local float_highlight_groups = {{ {float_highlight_groups_lua} }}
        for _, group_name in ipairs(float_highlight_groups) do
          vim.api.nvim_set_hl(0, group_name, {{ bg = "#041c38", fg = "#f7f7f5" }})
        end

        require("config.theme.transparency").clear_backgrounds_to_let_terminal_show_through()

        for _, group_name in ipairs(float_highlight_groups) do
          local highlight = vim.api.nvim_get_hl(0, {{ name = group_name, link = false }})
          assert(
            highlight.bg == nil,
            group_name .. " keeps its background, so the lsp hover popup draws a flat black slab"
              .. " over an editor that is transparent everywhere else"
          )
          assert(
            highlight.fg ~= nil,
            group_name .. " lost its foreground along with its background, which leaves the popup"
              .. " unreadable"
          )
        end

        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_transparency_keeps_the_scrollbar_thumb_visible(
    run_headless_lua, neovim_lua_directory
):
    program_configuration_path = neovim_lua_directory.parent

    result = run_headless_lua(
        "scrollbar_thumb_transparency.lua",
        f"""
        vim.opt.runtimepath:prepend({json.dumps(str(program_configuration_path))})

        vim.api.nvim_set_hl(0, "NoiceScrollbarThumb", {{ bg = "#4f5c58" }})

        require("config.theme.transparency").clear_backgrounds_to_let_terminal_show_through()

        local thumb = vim.api.nvim_get_hl(0, {{ name = "NoiceScrollbarThumb", link = false }})
        assert(
          thumb.bg ~= nil,
          "the scrollbar thumb lost its background, which is the only thing that marks how far"
            .. " down a long popup the view sits"
        )

        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
