import sys
import types
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))


class HIDException(Exception):
    pass


sys.modules.setdefault(
    "hid",
    types.SimpleNamespace(enumerate=None, Device=None, HIDException=HIDException),
)
