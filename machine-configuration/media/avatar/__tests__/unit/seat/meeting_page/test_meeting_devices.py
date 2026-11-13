import base64
import json
import shutil
import subprocess

import pytest
from page_devices import (
    BLACKHOLE_INPUT_FOR_THE_WRONG_DIRECTION,
    BLACKHOLE_OUTPUT_AS_DEFAULT,
    BUILT_IN_INPUT,
    BUILT_IN_OUTPUT,
    CALL_MICROPHONE,
    CALL_SPEAKER,
    MEETING_SEAT,
)
from renderer_module_runner import run_renderer_module


def evaluate(expression):
    source = base64.b64encode(MEETING_SEAT.read_bytes()).decode()
    program = f"""
    import("data:text/javascript;base64,{source}").then((meeting) => {{
      try {{
        console.log(JSON.stringify({{ value: ({expression}) }}));
      }} catch (error) {{
        console.log(JSON.stringify({{ error: error.message }}));
      }}
    }});
    """
    completed = subprocess.run(
        ["node", "-e", program], capture_output=True, text=True, check=True, timeout=30
    )
    return json.loads(completed.stdout)


def required(devices):
    return evaluate(f"meeting.requireCallDevices({json.dumps(devices)})")


pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is unavailable"
)


def test_the_call_devices_are_the_blackhole_output_and_input_by_label():
    result = required([BUILT_IN_OUTPUT, BUILT_IN_INPUT, CALL_SPEAKER, CALL_MICROPHONE])
    assert result["value"] == {
        "callMicrophone": CALL_MICROPHONE,
        "callSpeaker": CALL_SPEAKER,
    }


def test_the_two_channel_device_is_never_taken_for_the_sixteen_channel_one():
    result = required([BLACKHOLE_INPUT_FOR_THE_WRONG_DIRECTION, CALL_MICROPHONE])
    assert "BlackHole 16ch" in result["error"]
    assert "missing: BlackHole 16ch" in result["error"]


def test_a_missing_output_is_named_in_the_failure():
    result = required([BUILT_IN_OUTPUT, CALL_SPEAKER])
    assert result["error"].endswith("missing: BlackHole 2ch")


def test_both_missing_devices_are_named_in_the_failure():
    result = required([BUILT_IN_OUTPUT, BUILT_IN_INPUT])
    assert result["error"].endswith("missing: BlackHole 2ch, BlackHole 16ch")


def test_no_devices_at_all_fails_naming_both():
    assert "missing: BlackHole 2ch, BlackHole 16ch" in required([])["error"]


def test_the_system_default_entry_is_not_a_device_to_select():
    result = required([BLACKHOLE_OUTPUT_AS_DEFAULT, CALL_SPEAKER])
    assert result["error"].endswith("missing: BlackHole 2ch")
    found = evaluate(
        "meeting.findDevice("
        f"{json.dumps([BLACKHOLE_OUTPUT_AS_DEFAULT, CALL_MICROPHONE])},"
        ' "audiooutput", "BlackHole 2ch")'
    )
    assert found["value"] == CALL_MICROPHONE


def test_a_device_of_the_other_kind_does_not_match():
    found = evaluate(
        f'meeting.findDevice({json.dumps([CALL_SPEAKER])}, "audiooutput", "BlackHole")'
    )
    assert "value" not in found


@pytest.mark.parametrize(
    ("query", "hidden"),
    [
        ("", False),
        ("?viewer", False),
        ("?output", True),
        ("?bare", True),
        ("?viewer&bare", True),
    ],
)
def test_the_status_line_is_hidden_for_the_camera_output_and_for_a_bare_page(
    query, hidden
):
    result = run_renderer_module(
        "renderer-controls.js",
        f"""
        const pageOptions = new URLSearchParams({json.dumps(query)});
        console.log(JSON.stringify(rendererModule.statusIsHidden(pageOptions)));
        """,
    )
    assert result is hidden
