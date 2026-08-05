import json
import os
import subprocess
import textwrap
from pathlib import Path

MODULE_RELATIVE_PATH = (
    "machine-configuration/editors/neovim/program-configuration/lua/config/"
    "goto_definition_prefers_file_under_cursor.lua"
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


def build_nix_tree(tmp_path):
    importing_file = tmp_path / "outputs.nix"
    imported_file = tmp_path / "nixos-configurations.nix"
    imported_directory = tmp_path / "nix-checks"
    imported_directory.mkdir()
    (imported_directory / "default.nix").write_text("{ }\n")
    imported_file.write_text("{ }\n")
    importing_file.write_text(
        "{\n"
        "  configurations = import ./nixos-configurations.nix { };\n"
        "  checks = import ./nix-checks { };\n"
        "  plain = someIdentifier;\n"
        "}\n"
    )
    return importing_file, imported_file, imported_directory


def test_goto_definition_opens_the_imported_file_and_directory_entry_point(tmp_path):
    repository_root = Path(__file__).resolve().parents[5]
    module_path = repository_root / MODULE_RELATIVE_PATH
    importing_file, imported_file, imported_directory = build_nix_tree(tmp_path)
    result = run_headless_lua(
        tmp_path,
        "goto_file_under_cursor.lua",
        f"""
        local goto_definition = dofile({json.dumps(str(module_path))})

        vim.cmd.edit({json.dumps(str(importing_file))})
        vim.api.nvim_win_set_cursor(0, {{ 2, 35 }})
        local fallback_was_used = false
        local jumped = goto_definition.jump_to_file_under_cursor_or(function()
          fallback_was_used = true
        end)
        assert(jumped, "the cursor sat on an imported file and no jump happened")
        assert(not fallback_was_used, "the definition fallback ran even though the path resolved")
        assert(
          vim.api.nvim_buf_get_name(0) == {json.dumps(str(imported_file))},
          "landed on " .. vim.api.nvim_buf_get_name(0)
        )

        vim.cmd.edit({json.dumps(str(importing_file))})
        vim.api.nvim_win_set_cursor(0, {{ 3, 25 }})
        goto_definition.jump_to_file_under_cursor_or(function() end)
        assert(
          vim.api.nvim_buf_get_name(0) == {json.dumps(str(imported_directory / "default.nix"))},
          "an imported directory did not resolve to its default.nix, landed on "
            .. vim.api.nvim_buf_get_name(0)
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_goto_definition_falls_back_when_the_cursor_is_not_on_a_path(tmp_path):
    repository_root = Path(__file__).resolve().parents[5]
    module_path = repository_root / MODULE_RELATIVE_PATH
    importing_file, _, _ = build_nix_tree(tmp_path)
    result = run_headless_lua(
        tmp_path,
        "goto_definition_fallback.lua",
        f"""
        local goto_definition = dofile({json.dumps(str(module_path))})

        vim.cmd.edit({json.dumps(str(importing_file))})
        vim.api.nvim_win_set_cursor(0, {{ 4, 12 }})
        local fallback_was_used = false
        local jumped = goto_definition.jump_to_file_under_cursor_or(function()
          fallback_was_used = true
        end)
        assert(not jumped, "an identifier was treated as a file path")
        assert(fallback_was_used, "the language server definition fallback never ran")
        assert(
          vim.api.nvim_buf_get_name(0) == {json.dumps(str(importing_file))},
          "the fallback path moved the buffer"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
