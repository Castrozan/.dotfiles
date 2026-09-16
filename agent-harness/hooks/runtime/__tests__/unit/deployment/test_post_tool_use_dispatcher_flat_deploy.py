import json

from flat_deploy_test_support import (
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)


def test_post_tool_use_dispatcher_imports_shared_modules_after_flat_deploy(tmp_path):
    runtime_directory = tmp_path / "hooks"
    runtime_directory.mkdir()
    flatten_into_single_runtime_directory(runtime_directory)

    over_threshold_file = tmp_path / "too_long.py"
    over_threshold_file.write_text("\n".join(f"line_{n}" for n in range(250)) + "\n")
    blocked = run_flattened_hook(
        runtime_directory,
        "post-tool-use-dispatcher.py",
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": str(over_threshold_file)},
        },
        {"TMPDIR": str(tmp_path)},
    )
    assert blocked.returncode == 0
    payload = json.loads(blocked.stdout)
    assert payload["decision"] == "block"
