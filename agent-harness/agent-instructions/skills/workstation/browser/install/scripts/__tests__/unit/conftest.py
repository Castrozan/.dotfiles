import importlib.machinery
import importlib.util
from pathlib import Path

import pytest

ENFORCER_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent.parent / "enforce_pinchtab_config.py"
)


def _load_enforcer_module():
    loader = importlib.machinery.SourceFileLoader(
        "enforce_pinchtab_config", str(ENFORCER_SCRIPT_PATH)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@pytest.fixture
def enforcer():
    return _load_enforcer_module()


@pytest.fixture
def config_path(enforcer, tmp_path):
    path = tmp_path / "config.json"
    enforcer.pinchtab_config_path = str(path)
    return path


@pytest.fixture
def compliant_config():
    def build(token="existingtoken"):
        return {
            "server": {
                "token": token,
                "port": "9867",
                "stateDir": "/home/someone/.pinchtab",
            },
            "browser": {"binary": "/machine/specific/chrome"},
            "security": {
                "allowEvaluate": True,
                "allowMacro": True,
                "allowScreencast": True,
                "allowDownload": True,
                "allowCookies": True,
                "allowNetworkIntercept": True,
                "allowUpload": True,
                "allowClipboard": True,
                "allowStateExport": True,
                "enableActionGuards": False,
                "allowedDomains": ["*"],
                "downloadAllowedDomains": ["*"],
                "maxRedirects": -1,
                "attach": {
                    "enabled": True,
                    "allowHosts": ["*"],
                    "allowSchemes": ["ws", "wss"],
                },
                "idpi": {
                    "enabled": False,
                    "strictMode": False,
                    "scanContent": False,
                    "wrapContent": False,
                },
            },
            "instanceDefaults": {"mode": "headed"},
        }

    return build
