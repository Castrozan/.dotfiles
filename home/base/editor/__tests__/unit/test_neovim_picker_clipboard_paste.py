import json
import os
import subprocess
import textwrap
from pathlib import Path


def test_ctrl_v_pastes_a_single_line_into_picker_prompts_instead_of_splitting(tmp_path):
    repository_root = Path(__file__).resolve().parents[5]
    neovim_lua_root = repository_root / ".config/nvim/lua"
    telescope_config_path = neovim_lua_root / "plugins/telescope.lua"
    snacks_picker_config_path = neovim_lua_root / "plugins/snacks-picker.lua"
    lua_script_path = tmp_path / "picker_clipboard_paste.lua"
    lua_script_path.write_text(
        textwrap.dedent(
            f"""
            package.path = {json.dumps(str(neovim_lua_root))} .. "/?.lua;" .. package.path

            local clipboard_lines = {{ "first line", "second line", "" }}
            vim.g.clipboard = {{
              name = "test-clipboard",
              copy = {{ ["+"] = function() end, ["*"] = function() end }},
              paste = {{
                ["+"] = function()
                  return clipboard_lines
                end,
                ["*"] = function()
                  return clipboard_lines
                end,
              }},
              cache_enabled = 0,
            }}

            local function paste_into_a_fresh_buffer(paste_callback)
              vim.cmd("enew!")
              paste_callback()
              return vim.api.nvim_buf_get_lines(0, 0, -1, false)
            end

            local telescope_mappings = dofile({json.dumps(str(telescope_config_path))})[1].opts.defaults.mappings
            for _, mode in ipairs({{ "i", "n" }}) do
              local pasted_lines = paste_into_a_fresh_buffer(telescope_mappings[mode]["<C-v>"])
              assert(#pasted_lines == 1, "telescope <C-v> pasted more than one line in mode " .. mode)
              assert(
                pasted_lines[1] == "first line second line",
                "telescope <C-v> pasted " .. vim.inspect(pasted_lines) .. " in mode " .. mode
              )
            end

            local picker_windows = dofile({json.dumps(str(snacks_picker_config_path))})[1].opts.picker.win
            local input_key = picker_windows.input.keys["<c-v>"]
            assert(vim.deep_equal(input_key.mode, {{ "i", "n" }}), "snacks input <c-v> is not mapped in insert and normal mode")
            local pasted_lines = paste_into_a_fresh_buffer(input_key[1])
            assert(
              #pasted_lines == 1 and pasted_lines[1] == "first line second line",
              "snacks input <c-v> pasted " .. vim.inspect(pasted_lines)
            )

            local untouched_lines = paste_into_a_fresh_buffer(picker_windows.list.keys["<c-v>"][1])
            assert(
              #untouched_lines == 1 and untouched_lines[1] == "",
              "snacks list <c-v> changed the buffer instead of doing nothing"
            )

            clipboard_lines = {{ "" }}
            local empty_clipboard_lines = paste_into_a_fresh_buffer(telescope_mappings.i["<C-v>"])
            assert(
              #empty_clipboard_lines == 1 and empty_clipboard_lines[1] == "",
              "an empty clipboard was pasted as " .. vim.inspect(empty_clipboard_lines)
            )
            vim.cmd("qa!")
            """
        ).strip()
    )
    environment = dict(os.environ, XDG_STATE_HOME=str(tmp_path / "state"))
    result = subprocess.run(
        ["nvim", "--headless", "-u", "NONE", "-l", str(lua_script_path)],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
