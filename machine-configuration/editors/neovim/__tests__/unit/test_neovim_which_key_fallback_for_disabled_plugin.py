import json
import os
import subprocess
import textwrap
from pathlib import Path

FALLBACK_MODULE_RELATIVE_PATH = (
    "machine-configuration/editors/neovim/program-configuration/lua/config/"
    "which_key_fallback_for_disabled_plugin.lua"
)


def run_headless_lua(tmp_path, script_name, lua_body):
    repository_root = Path(__file__).resolve().parents[5]
    lua_script_path = tmp_path / script_name
    lua_script_path.write_text(textwrap.dedent(lua_body).strip())
    environment = dict(os.environ, XDG_STATE_HOME=str(tmp_path / "state"))
    return subprocess.run(
        ["nvim", "--headless", "-u", "NONE", "-l", str(lua_script_path)],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_which_key_fallback_sets_the_java_refactor_keymaps_a_disabled_plugin_would_drop(
    tmp_path,
):
    repository_root = Path(__file__).resolve().parents[5]
    fallback_module_path = repository_root / FALLBACK_MODULE_RELATIVE_PATH
    result = run_headless_lua(
        tmp_path,
        "which_key_fallback_java_keymaps.lua",
        f"""
        vim.g.mapleader = " "
        package.loaded["lazy.core.config"] = {{ spec = {{ plugins = {{}} }} }}
        dofile({json.dumps(str(fallback_module_path))}).install()

        local which_key = require("which-key")
        local extract_variable_was_called = false
        which_key.add({{
          {{
            mode = "n",
            buffer = 0,
            {{ "<leader>cx", group = "extract" }},
            {{
              "<leader>cxv",
              function()
                extract_variable_was_called = true
              end,
              desc = "Extract Variable",
            }},
            {{ "<leader>co", function() end, desc = "Organize Imports" }},
          }},
        }})
        which_key.add({{
          {{
            mode = "x",
            buffer = 0,
            {{ "<leader>cx", group = "extract" }},
            {{
              "<leader>cxm",
              [[<ESC><CMD>lua require('jdtls').extract_method(true)<CR>]],
              desc = "Extract Method",
            }},
          }},
        }})

        local mappings_by_description = {{}}
        for _, mode in ipairs({{ "n", "x" }}) do
          for _, mapping in ipairs(vim.api.nvim_buf_get_keymap(0, mode)) do
            mappings_by_description[mapping.desc or ""] = mapping
          end
        end

        for _, expected_description in ipairs({{ "Extract Variable", "Organize Imports", "Extract Method" }}) do
          assert(
            mappings_by_description[expected_description] ~= nil,
            "the which-key fallback never set the buffer mapping for " .. expected_description
          )
        end
        assert(
          mappings_by_description["Extract Variable"].lhs == " cxv",
          "the extract variable mapping landed on "
            .. tostring(mappings_by_description["Extract Variable"].lhs)
        )
        assert(
          mappings_by_description["Extract Method"].rhs:find("extract_method", 1, true) ~= nil,
          "the visual mode mapping lost its right hand side: "
            .. tostring(mappings_by_description["Extract Method"].rhs)
        )

        for _, mapping in ipairs(vim.api.nvim_buf_get_keymap(0, "n")) do
          assert(
            mapping.lhs ~= " cx",
            "a which-key group label was turned into a keymap instead of being skipped"
          )
        end

        mappings_by_description["Extract Variable"].callback()
        assert(extract_variable_was_called, "the mapped callback was not the one which-key was given")
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_which_key_fallback_stands_down_when_the_real_plugin_is_enabled(tmp_path):
    repository_root = Path(__file__).resolve().parents[5]
    fallback_module_path = repository_root / FALLBACK_MODULE_RELATIVE_PATH
    result = run_headless_lua(
        tmp_path,
        "which_key_fallback_stands_down.lua",
        f"""
        package.loaded["lazy.core.config"] = {{
          spec = {{ plugins = {{ ["which-key.nvim"] = {{ name = "which-key.nvim" }} }} }},
        }}
        dofile({json.dumps(str(fallback_module_path))}).install()
        assert(
          package.preload["which-key"] == nil,
          "the fallback shadowed the real which-key plugin while it was enabled"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
