import importlib
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def todo_modules(monkeypatch):
    directory = Path(__file__).resolve().parents[2] / "scripts" / "todo_cli"
    names = ("api", "render", "commands", "todo")
    monkeypatch.syspath_prepend(str(directory))
    for name in names:
        monkeypatch.delitem(sys.modules, name, raising=False)
    modules = {name: importlib.import_module(name) for name in names}
    yield SimpleNamespace(**modules)
    for name in names:
        sys.modules.pop(name, None)
