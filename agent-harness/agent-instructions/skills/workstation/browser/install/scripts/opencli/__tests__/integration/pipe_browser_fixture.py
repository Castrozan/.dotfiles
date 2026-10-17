import json
import os
import sys
from pathlib import Path

directory = Path(sys.argv[1])
(directory / "browser-ready").touch()
message = bytearray()
while (value := os.read(3, 1)) != b"\x00":
    if not value:
        raise SystemExit(1)
    message.extend(value)
command = json.loads(message)
assert command["method"] == "Browser.close"
(directory / "persisted").write_text("retained")
os.write(4, b'{"id":1,"result":{}}\x00')
