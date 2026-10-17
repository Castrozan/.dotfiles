import json
import sys
from pathlib import Path


settings = json.loads(Path(sys.argv[1]).read_text())
expected = json.loads(Path(sys.argv[2]).read_text())
for key in ("extraKnownMarketplaces", "enabledPlugins"):
    for entry_name, entry_value in expected.get(key, {}).items():
        assert settings.get(key, {}).get(entry_name) == entry_value, (
            f"{key}.{entry_name}"
        )
