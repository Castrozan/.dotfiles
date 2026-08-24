import sys
from pathlib import Path

HEY_BOT_PACKAGE_DIRECTORY = Path(__file__).parent.parent / "scripts" / "hey_bot"

sys.path.insert(0, str(HEY_BOT_PACKAGE_DIRECTORY))
