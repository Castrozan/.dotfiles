import json


def test_noice_draws_a_border_around_hover_and_signature_docs(
    run_headless_lua, neovim_lua_path
):
    noice_plugin_path = neovim_lua_path("plugins", "noice.lua")

    result = run_headless_lua(
        "noice_hover_border.lua",
        f"""
        local noice_plugin_spec = dofile({json.dumps(str(noice_plugin_path))})[1]
        assert(
          noice_plugin_spec[1] == "folke/noice.nvim",
          "the override no longer targets noice, which is what renders the lsp hover float"
        )
        assert(
          noice_plugin_spec.opts.presets.lsp_doc_border == true,
          "noice renders hover and signature docs with no frame, so they read as text floating"
            .. " loose over the buffer"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
