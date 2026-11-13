import base64
import json
import shutil
import subprocess
from pathlib import Path

import pytest

CHOICE = Path(__file__).resolve().parents[3] / "scripts/wake/page/microphone-choice.js"


def input_device(device_id, label):
    return {"kind": "audioinput", "deviceId": device_id, "label": label}


BUILT_IN = input_device("abc", "MacBook Pro Microphone (Built-in)")
BUILT_IN_DEFAULT = input_device(
    "default", "Default - MacBook Pro Microphone (Built-in)"
)
AIRPODS = input_device("def", "AirPods Pro (Bluetooth)")
AIRPODS_DEFAULT = input_device("default", "Default - AirPods Pro (Bluetooth)")
USB = input_device("ghi", "USB Microphone")
SPEAKERS = {"kind": "audiooutput", "deviceId": "xyz", "label": "Built-in Output"}


def chosen(devices):
    source = base64.b64encode(CHOICE.read_bytes()).decode()
    program = f"""
    import("data:text/javascript;base64,{source}").then((choice) => {{
      console.log(JSON.stringify(choice.chooseMicrophone({json.dumps(devices)})));
    }});
    """
    completed = subprocess.run(
        ["node", "-e", program], capture_output=True, text=True, check=True, timeout=30
    )
    return json.loads(completed.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is unavailable")
@pytest.mark.parametrize(
    ("devices", "expected"),
    [
        ([BUILT_IN_DEFAULT, BUILT_IN, USB], None),
        ([input_device("default", "Default - USB Microphone"), USB, BUILT_IN], None),
        ([AIRPODS_DEFAULT, BUILT_IN_DEFAULT, AIRPODS, BUILT_IN], "abc"),
        ([AIRPODS_DEFAULT, AIRPODS, USB], None),
        ([AIRPODS_DEFAULT, SPEAKERS, AIRPODS, BUILT_IN], "abc"),
        ([SPEAKERS], None),
        ([], None),
        ([input_device("default", "Default - AirPods (bluetooth)"), BUILT_IN], "abc"),
        ([AIRPODS, BUILT_IN], "abc"),
        ([input_device("default", ""), input_device("abc", "")], None),
    ],
)
def test_the_default_input_is_kept_unless_it_is_bluetooth_and_a_built_in_exists(
    devices, expected
):
    assert chosen(devices) == expected
