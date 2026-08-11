import json


def test_word_jumps_stop_at_the_first_and_last_column_of_the_line(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "navigation", "word_jumping.lua")
    result = run_headless_lua(
        "word_jumping.lua",
        f"""
        local word_jumping = dofile({json.dumps(str(module_path))})

        vim.api.nvim_buf_set_lines(0, 0, -1, false, {{
          "def level_order(root):",
          "    return [[root.value]]",
          "",
        }})

        local function cursor_position()
          return vim.fn.line(".") .. ":" .. vim.fn.col(".")
        end

        local function assert_position(expected_position, what_was_pressed)
          assert(
            cursor_position() == expected_position,
            what_was_pressed .. " landed on " .. cursor_position() .. " instead of " .. expected_position
          )
        end

        vim.api.nvim_win_set_cursor(0, {{ 2, 11 }})
        word_jumping.jump_left()
        assert_position("2:5", "a jump left from the bracket")

        word_jumping.jump_left()
        assert_position("2:1", "a jump left from the first word of the line")

        word_jumping.jump_left()
        assert_position("2:1", "a jump left from the first column")

        vim.api.nvim_win_set_cursor(0, {{ 2, 0 }})
        word_jumping.jump_right()
        assert_position("2:5", "a jump right from the first column")

        word_jumping.jump_right()
        assert_position("2:12", "a jump right from the first word")

        word_jumping.jump_right()
        assert_position("2:25", "a jump right from the last word of the line")

        word_jumping.jump_right()
        assert_position("2:25", "a jump right from the last column")

        vim.api.nvim_win_set_cursor(0, {{ 3, 0 }})
        word_jumping.jump_right()
        assert_position("3:1", "a jump right on an empty line")

        word_jumping.jump_left()
        assert_position("3:1", "a jump left on an empty line")
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
