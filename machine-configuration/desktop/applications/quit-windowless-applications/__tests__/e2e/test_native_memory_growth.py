import json
import plistlib
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "darwin", reason="Requires the macOS Cocoa bridge")
def test_repeated_window_number_conversion_has_bounded_retained_memory():
    launch_agent_path = (
        Path.home()
        / "Library/LaunchAgents/com.dotfiles.quit-windowless-applications.plist"
    )
    if not launch_agent_path.exists():
        pytest.skip("The windowless-applications daemon is not deployed")
    launch_agent = plistlib.loads(launch_agent_path.read_bytes())
    probe = """
import gc
import json
import tracemalloc

from Foundation import NSNumber

number = NSNumber.numberWithInt_(27)
for iteration in range(1000):
    number.objCType()
gc.collect()
tracemalloc.start()
before = tracemalloc.get_traced_memory()[0]
for iteration in range(100000):
    number.objCType()
gc.collect()
print(json.dumps({"retained_bytes": tracemalloc.get_traced_memory()[0] - before}))
"""
    result = subprocess.run(
        [launch_agent["ProgramArguments"][0], "-c", probe],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    retained_bytes = json.loads(result.stdout)["retained_bytes"]

    assert retained_bytes < 64 * 1024, (
        f"100,000 window-number conversions retained {retained_bytes} bytes"
    )
