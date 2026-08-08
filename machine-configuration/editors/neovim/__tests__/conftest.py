import os
import subprocess
import textwrap
from pathlib import Path

import pytest

NEOVIM_LUA_RELATIVE_PATH = (
    "machine-configuration/editors/neovim/program-configuration/lua"
)


@pytest.fixture
def repository_root():
    return Path(__file__).resolve().parents[4]


@pytest.fixture
def neovim_lua_directory(repository_root):
    return repository_root / NEOVIM_LUA_RELATIVE_PATH


@pytest.fixture
def neovim_lua_path(neovim_lua_directory):
    def build_module_path(*module_path_parts):
        return neovim_lua_directory / Path(*module_path_parts)

    return build_module_path


@pytest.fixture
def run_headless_lua(repository_root, tmp_path):
    def run(script_name, lua_body):
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

    return run
