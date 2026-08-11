import json


def test_the_import_chord_applies_the_action_that_adds_an_import(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "missing_imports.lua")
    result = run_headless_lua(
        "missing_imports.lua",
        f"""
        local missing_imports = dofile({json.dumps(str(module_path))})

        local requested_options = nil
        vim.lsp.buf.code_action = function(options)
          requested_options = options
        end

        missing_imports.add()
        assert(
          requested_options and requested_options.apply == true,
          "the import chord asked the user to pick instead of applying the single import action"
        )

        local accepted_titles = {{
          "Import 'ArrayList' (java.util)",
          "Add import from pathlib",
        }}
        for _, title in ipairs(accepted_titles) do
          assert(
            requested_options.filter({{ title = title }}),
            "the import chord filtered out " .. title
          )
        end

        local rejected_titles = {{
          "Remove unused import",
          "Delete import",
          "Add all missing imports",
          "Organize imports",
          "Extract to method",
          "Generate getters",
        }}
        for _, title in ipairs(rejected_titles) do
          assert(
            not requested_options.filter({{ title = title }}),
            "the import chord would have applied " .. title
          )
        end

        assert(
          not requested_options.filter({{}}),
          "an action with no title passed the import filter"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_import_chord_asks_only_about_the_symbol_under_the_cursor(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "missing_imports.lua")
    result = run_headless_lua(
        "missing_imports_context.lua",
        f"""
        local missing_imports = dofile({json.dumps(str(module_path))})

        local requested_options = nil
        vim.lsp.buf.code_action = function(options)
          requested_options = options
        end

        vim.api.nvim_buf_set_lines(0, 0, -1, false, {{
          "        List<Integer> first = new ArrayList<>();",
        }})
        vim.diagnostic.set(vim.api.nvim_create_namespace("test"), 0, {{
          {{ lnum = 0, col = 8, end_lnum = 0, end_col = 21, message = "List cannot be resolved" }},
          {{ lnum = 0, col = 34, end_lnum = 0, end_col = 43, message = "ArrayList cannot be resolved" }},
        }})

        vim.api.nvim_win_set_cursor(0, {{ 1, 34 }})
        missing_imports.add()
        assert(
          requested_options.context and #requested_options.context.diagnostics == 1,
          "the import chord asked about "
            .. #((requested_options.context or {{}}).diagnostics or {{}})
            .. " diagnostics instead of the one under the cursor"
        )
        assert(
          requested_options.context.diagnostics[1].message == "ArrayList cannot be resolved",
          "the import chord asked about " .. requested_options.context.diagnostics[1].message
        )

        vim.api.nvim_win_set_cursor(0, {{ 1, 25 }})
        missing_imports.add()
        assert(
          requested_options.context == nil,
          "the import chord narrowed the request to no diagnostics at all away from a symbol"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
