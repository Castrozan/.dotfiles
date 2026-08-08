import json


def test_closing_focuses_the_buffer_to_the_right_then_falls_back_to_the_left(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "buffer_closing.lua")
    result = run_headless_lua(
        "buffer_closing_focus_order.lua",
        f"""
        _G.Snacks = {{ dashboard = function() end }}
        local buffer_closing = dofile({json.dumps(str(module_path))})

        vim.cmd("edit first.txt")
        local first_buffer_id = vim.api.nvim_get_current_buf()
        vim.cmd("edit second.txt")
        local second_buffer_id = vim.api.nvim_get_current_buf()
        vim.cmd("edit third.txt")
        local third_buffer_id = vim.api.nvim_get_current_buf()

        vim.api.nvim_set_current_buf(second_buffer_id)
        buffer_closing.close()
        assert(
          vim.fn.buflisted(second_buffer_id) == 0,
          "the buffer under the cursor stayed on the buffer list"
        )
        assert(
          vim.api.nvim_get_current_buf() == third_buffer_id,
          "closing a middle buffer did not focus the one to its right"
        )

        buffer_closing.close()
        assert(
          vim.api.nvim_get_current_buf() == first_buffer_id,
          "closing the rightmost buffer did not fall back to the one on its left"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_closing_the_last_file_buffer_lands_on_the_dashboard(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "buffer_closing.lua")
    result = run_headless_lua(
        "buffer_closing_last_buffer.lua",
        f"""
        local dashboard_was_opened = false
        _G.Snacks = {{
          dashboard = function()
            dashboard_was_opened = true
          end,
        }}
        local buffer_closing = dofile({json.dumps(str(module_path))})

        vim.cmd("edit only.txt")
        local only_buffer_id = vim.api.nvim_get_current_buf()
        buffer_closing.close()
        assert(dashboard_was_opened, "closing the last file buffer did not open the dashboard")
        assert(
          vim.fn.buflisted(only_buffer_id) == 0,
          "the last file buffer stayed on the buffer list"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_closing_leaves_a_buffer_that_holds_no_file_alone(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "buffer_closing.lua")
    result = run_headless_lua(
        "buffer_closing_ignores_non_file_buffers.lua",
        f"""
        _G.Snacks = {{ dashboard = function() end }}
        local buffer_closing = dofile({json.dumps(str(module_path))})

        vim.cmd("enew")
        local scratch_buffer_id = vim.api.nvim_get_current_buf()
        buffer_closing.close()
        assert(
          vim.api.nvim_get_current_buf() == scratch_buffer_id,
          "closing a buffer that holds no file moved the cursor somewhere else"
        )
        assert(
          vim.fn.buflisted(scratch_buffer_id) == 1,
          "a buffer that holds no file was closed anyway"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
