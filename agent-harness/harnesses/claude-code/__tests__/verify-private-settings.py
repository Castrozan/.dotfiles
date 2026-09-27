import json
import sys
from pathlib import Path


settings = json.loads(Path(sys.argv[1]).read_text())
expected = json.loads(Path(sys.argv[2]).read_text())
for key in ("extraKnownMarketplaces", "enabledPlugins"):
    if key in expected:
        assert settings.get(key, {}) == expected[key], key
