import json

import pytest


@pytest.mark.parametrize(
    "origin_url",
    [
        "git@gitlab.example.com:group/project.git",
        "https://gitlab.example.com/group/project.git",
        "ssh://git@gitlab.example.com:2222/group/project",
    ],
)
def test_gitlab_authentication_asks_glab_for_the_origin_host_token(
    run_headless_lua, neovim_lua_path, origin_url
):
    module_path = neovim_lua_path("config", "code_review", "gitlab_authentication.lua")
    result = run_headless_lua(
        "gitlab_authentication_origin_host.lua",
        f"""
        local asked_hosts = {{}}
        vim.fn.system = function(command)
          if command[1] == "git" then
            return {json.dumps(origin_url)} .. "\\n"
          end
          table.insert(asked_hosts, command[#command])
          return "secret-token\\n"
        end
        local token, gitlab_url, problem = dofile({json.dumps(str(module_path))}).provide()
        assert(problem == nil, tostring(problem))
        assert(token == "secret-token", "token was " .. tostring(token))
        assert(gitlab_url == "https://gitlab.example.com", "url was " .. tostring(gitlab_url))
        assert(asked_hosts[1] == "gitlab.example.com", "glab was asked for " .. tostring(asked_hosts[1]))
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_gitlab_authentication_without_a_glab_token_says_how_to_log_in(
    run_headless_lua, neovim_lua_path
):
    module_path = neovim_lua_path("config", "code_review", "gitlab_authentication.lua")
    result = run_headless_lua(
        "gitlab_authentication_missing_token.lua",
        f"""
        vim.fn.system = function(command)
          if command[1] == "git" then
            return "git@gitlab.example.com:group/project.git\\n"
          end
          return ""
        end
        local token, _, problem = dofile({json.dumps(str(module_path))}).provide()
        assert(token == nil, "a token was returned without glab having one")
        assert(problem:find("glab auth login", 1, true), "problem was " .. tostring(problem))
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("pull_request_url", "octo_buffer_name"),
    [
        (
            "https://github.com/owner/repo/pull/12",
            "octo://owner/repo/pull/12",
        ),
        (
            "https://ghe.example.com/owner/repo/pull/3",
            "octo://ghe.example.com/owner/repo/pull/3",
        ),
    ],
)
def test_pull_request_review_starts_once_the_octo_buffer_has_loaded(
    run_headless_lua, neovim_lua_path, pull_request_url, octo_buffer_name
):
    module_path = neovim_lua_path("config", "code_review", "pull_request_review.lua")
    result = run_headless_lua(
        "pull_request_review_start.lua",
        f"""
        local edited_names = {{}}
        local review_starts = 0
        vim.cmd.edit = function(name)
          table.insert(edited_names, name)
        end
        package.loaded["octo.reviews"] = {{
          start_or_resume_review = function()
            review_starts = review_starts + 1
          end,
        }}
        _G.octo_buffers = {{}}

        dofile({json.dumps(str(module_path))}).open({json.dumps(pull_request_url)})
        assert(edited_names[1] == {json.dumps(octo_buffer_name)}, "edited " .. tostring(edited_names[1]))
        vim.wait(300)
        assert(review_starts == 0, "the review started before the pull request loaded")

        _G.octo_buffers[vim.api.nvim_get_current_buf()] = {{
          isPullRequest = function()
            return true
          end,
        }}
        assert(vim.wait(1000, function()
          return review_starts == 1
        end), "the review never started after the pull request loaded")
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
