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


def test_buffer_jump_moves_ten_lines_and_stops_at_the_first_and_last_line(tmp_path):
    module_path = neovim_lua_path("config", "navigation", "ten_line_jumping.lua")
    result = run_headless_lua(
        tmp_path,
        "ten_line_jumping_buffer.lua",
        f"""
        local ten_line_jumping = dofile({json.dumps(str(module_path))})

        local buffer_lines = {{}}
        for line_number = 1, 50 do
          buffer_lines[line_number] = "line " .. line_number
        end
        vim.api.nvim_buf_set_lines(0, 0, -1, false, buffer_lines)

        vim.api.nvim_win_set_cursor(0, {{ 1, 0 }})
        ten_line_jumping.jump_buffer_down()
        assert(vim.fn.line(".") == 11, "a jump down from line 1 landed on " .. vim.fn.line("."))

        ten_line_jumping.jump_buffer_up()
        assert(vim.fn.line(".") == 1, "a jump up from line 11 landed on " .. vim.fn.line("."))

        ten_line_jumping.jump_buffer_up()
        assert(vim.fn.line(".") == 1, "a jump up from the first line did not stop at the top")

        vim.api.nvim_win_set_cursor(0, {{ 45, 0 }})
        ten_line_jumping.jump_buffer_down()
        assert(
          vim.fn.line(".") == 50,
          "a jump down with fewer than ten lines left landed on " .. vim.fn.line(".") .. " instead of the last line"
        )

        ten_line_jumping.jump_buffer_down()
        assert(vim.fn.line(".") == 50, "a jump down from the last line did not stop at the bottom")

        vim.api.nvim_win_set_cursor(0, {{ 4, 0 }})
        ten_line_jumping.jump_buffer_up()
        assert(
          vim.fn.line(".") == 1,
          "a jump up with fewer than ten lines above landed on " .. vim.fn.line(".") .. " instead of the first line"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_snacks_selection_jump_moves_the_list_by_ten_entries(tmp_path):
    module_path = neovim_lua_path("config", "navigation", "ten_line_jumping.lua")
    result = run_headless_lua(
        tmp_path,
        "ten_line_jumping_snacks.lua",
        f"""
        local ten_line_jumping = dofile({json.dumps(str(module_path))})

        local requested_moves = {{}}
        local picker = {{
          list = {{
            move = function(_, entry_delta)
              table.insert(requested_moves, entry_delta)
            end,
          }},
        }}

        ten_line_jumping.jump_snacks_selection_down(picker)
        ten_line_jumping.jump_snacks_selection_up(picker)
        assert(requested_moves[1] == 10, "a snacks jump down asked for " .. tostring(requested_moves[1]))
        assert(requested_moves[2] == -10, "a snacks jump up asked for " .. tostring(requested_moves[2]))
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_telescope_selection_jump_shifts_the_selection_by_ten_entries(tmp_path):
    module_path = neovim_lua_path("config", "navigation", "ten_line_jumping.lua")
    result = run_headless_lua(
        tmp_path,
        "ten_line_jumping_telescope.lua",
        f"""
        local ten_line_jumping = dofile({json.dumps(str(module_path))})

        local requested_shifts = {{}}
        package.loaded["telescope.actions.set"] = {{
          shift_selection = function(prompt_buffer_number, entry_delta)
            table.insert(requested_shifts, {{ prompt_buffer_number, entry_delta }})
          end,
        }}

        ten_line_jumping.jump_telescope_selection_down(7)
        ten_line_jumping.jump_telescope_selection_up(7)
        assert(requested_shifts[1][1] == 7, "the prompt buffer number was not passed through")
        assert(requested_shifts[1][2] == 10, "a telescope jump down asked for " .. tostring(requested_shifts[1][2]))
        assert(requested_shifts[2][2] == -10, "a telescope jump up asked for " .. tostring(requested_shifts[2][2]))
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_picker_specs_stop_at_the_ends_instead_of_wrapping_around(tmp_path):
    lua_directory = repository_root() / NEOVIM_LUA_RELATIVE_PATH
    snacks_spec_path = neovim_lua_path("plugins", "snacks-picker.lua")
    telescope_spec_path = neovim_lua_path("plugins", "telescope.lua")
    result = run_headless_lua(
        tmp_path,
        "picker_specs_no_wrap.lua",
        f"""
        package.path = {json.dumps(str(lua_directory) + "/?.lua")} .. ";" .. package.path

        local snacks_spec = dofile({json.dumps(str(snacks_spec_path))})[1]
        assert(
          snacks_spec.opts.picker.layout.cycle == false,
          "the snacks picker still cycles past its first and last entry"
        )
        assert(
          snacks_spec.opts.picker.win.list.keys["<C-S-Down>"] == "jump_selection_down",
          "the snacks explorer list lost its ten entry jump"
        )
        assert(
          snacks_spec.opts.picker.win.input.keys["<C-S-Up>"][1] == "jump_selection_up",
          "the snacks picker input lost its ten entry jump"
        )

        local telescope_spec = dofile({json.dumps(str(telescope_spec_path))})[1]
        assert(
          telescope_spec.opts.defaults.scroll_strategy == "limit",
          "telescope still cycles past its first and last entry"
        )
        for _, mode in ipairs({{ "i", "n" }}) do
          assert(
            type(telescope_spec.opts.defaults.mappings[mode]["<C-S-Down>"]) == "function",
            "telescope lost its ten entry jump in " .. mode .. " mode"
          )
        end
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
