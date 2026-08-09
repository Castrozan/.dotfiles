import json


def test_a_new_file_lands_next_to_the_file_in_the_current_buffer(
    run_headless_lua, neovim_lua_path, tmp_path
):
    module_path = neovim_lua_path("config", "file_creation.lua")
    opened_directory = tmp_path / "practice" / "01-tree-height"
    opened_directory.mkdir(parents=True)
    opened_file = opened_directory / "solution.py"
    opened_file.write_text("raise NotImplementedError\n")
    result = run_headless_lua(
        "file_creation_beside_current_buffer.lua",
        f"""
        local file_creation = dofile({json.dumps(str(module_path))})
        vim.ui.input = function(_, on_confirm)
          on_confirm("notes.md")
        end

        vim.cmd.edit({json.dumps(str(opened_file))})
        file_creation.create()

        local created_path = {json.dumps(str(opened_directory / "notes.md"))}
        assert(vim.uv.fs_stat(created_path), "the new file was not created beside the open one")
        assert(
          vim.fs.normalize(vim.api.nvim_buf_get_name(0)) == vim.fs.normalize(created_path),
          "the new file was created but never opened, the buffer holds " .. vim.api.nvim_buf_get_name(0)
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_nested_name_creates_the_directories_it_needs(
    run_headless_lua, neovim_lua_path, tmp_path
):
    module_path = neovim_lua_path("config", "file_creation.lua")
    opened_file = tmp_path / "solution.py"
    opened_file.write_text("raise NotImplementedError\n")
    result = run_headless_lua(
        "file_creation_nested_name.lua",
        f"""
        local file_creation = dofile({json.dumps(str(module_path))})
        vim.ui.input = function(_, on_confirm)
          on_confirm("tests/unit/test_solution.py")
        end

        vim.cmd.edit({json.dumps(str(opened_file))})
        file_creation.create()

        local created_path = {json.dumps(str(tmp_path / "tests" / "unit" / "test_solution.py"))}
        assert(vim.uv.fs_stat(created_path), "a nested name did not create the directories it needs")
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_an_existing_file_is_never_overwritten(
    run_headless_lua, neovim_lua_path, tmp_path
):
    module_path = neovim_lua_path("config", "file_creation.lua")
    opened_file = tmp_path / "solution.py"
    opened_file.write_text("raise NotImplementedError\n")
    result = run_headless_lua(
        "file_creation_existing_file.lua",
        f"""
        local file_creation = dofile({json.dumps(str(module_path))})
        vim.ui.input = function(_, on_confirm)
          on_confirm("solution.py")
        end

        local warnings = {{}}
        vim.notify = function(message, level)
          table.insert(warnings, {{ message = message, level = level }})
        end

        vim.cmd.edit({json.dumps(str(opened_file))})
        file_creation.create()

        local kept_content = table.concat(vim.fn.readfile({json.dumps(str(opened_file))}), "\\n")
        assert(kept_content == "raise NotImplementedError", "an existing file was overwritten, it now holds " .. kept_content)
        assert(#warnings == 1 and warnings[1].level == vim.log.levels.WARN, "creating over an existing file warned nobody")
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_explorer_creates_inside_the_selected_entry_directory(
    run_headless_lua, neovim_lua_path
):
    spec_path = neovim_lua_path("plugins", "snacks-explorer.lua")
    result = run_headless_lua(
        "file_creation_explorer_spec.lua",
        f"""
        local explorer_spec = dofile({json.dumps(str(spec_path))})[1]
        local explorer_list_keys = explorer_spec.opts.picker.sources.explorer.win.list.keys
        assert(
          explorer_list_keys["<c-n>"] == "explorer_add",
          "the explorer list still moves the selection down instead of adding a file"
        )
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
