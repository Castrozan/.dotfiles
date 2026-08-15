import importlib.util
import pathlib

ROUTER_SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "route-page-key.py"
)


def _load_router_module():
    module_spec = importlib.util.spec_from_file_location(
        "route_page_key", ROUTER_SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


route_page_key = _load_router_module()


def _tab(tab_id, workspace_id, focused=False):
    return {"tab_id": tab_id, "workspace_id": workspace_id, "focused": focused}


def _process_info_response(*process_names):
    return {
        "result": {
            "process_info": {
                "foreground_processes": [{"name": name} for name in process_names]
            }
        }
    }


def _tab_list_response(tabs):
    return {"result": {"tabs": tabs}}


def _record_herdr_calls(monkeypatch, responses):
    """Replace the herdr CLI with canned responses and record every call made."""
    calls = []

    def fake_run_herdr(arguments):
        arguments = list(arguments)
        calls.append(arguments)
        for prefix, response in responses:
            if arguments[: len(prefix)] == list(prefix):
                return response
        return None

    monkeypatch.setattr(route_page_key, "run_herdr", fake_run_herdr)
    monkeypatch.setenv("HERDR_ACTIVE_PANE_ID", "w1:p1")
    monkeypatch.setenv("HERDR_ACTIVE_WORKSPACE_ID", "w1")
    return calls


def test_foreground_names_are_basenames_without_case():
    process_info = {
        "foreground_processes": [
            {"name": "NVIM", "argv0": "/nix/store/abc/bin/nvim"},
            {"name": "bash"},
        ]
    }

    assert route_page_key.foreground_process_names(process_info) == {"nvim", "bash"}


def test_pane_running_nvim_keeps_the_key():
    assert route_page_key.pane_is_owned_by_editor({"nvim", "git"})


def test_pane_without_nvim_releases_the_key():
    assert not route_page_key.pane_is_owned_by_editor({"claude", "bash"})


def test_missing_foreground_processes_release_the_key():
    assert not route_page_key.pane_is_owned_by_editor(
        route_page_key.foreground_process_names({})
    )


def test_previous_and_next_walk_the_workspace_tabs():
    tabs = [
        _tab("w1:t1", "w1"),
        _tab("w1:t2", "w1", focused=True),
        _tab("w1:t3", "w1"),
    ]

    assert route_page_key.neighbor_tab_id(tabs, "w1", "previous") == "w1:t1"
    assert route_page_key.neighbor_tab_id(tabs, "w1", "next") == "w1:t3"


def test_both_ends_wrap_around():
    first_focused = [_tab("w1:t1", "w1", focused=True), _tab("w1:t2", "w1")]
    last_focused = [_tab("w1:t1", "w1"), _tab("w1:t2", "w1", focused=True)]

    assert route_page_key.neighbor_tab_id(first_focused, "w1", "previous") == "w1:t2"
    assert route_page_key.neighbor_tab_id(last_focused, "w1", "next") == "w1:t1"


def test_tabs_of_other_workspaces_are_ignored():
    tabs = [
        _tab("w1:t1", "w1", focused=True),
        _tab("w1:t2", "w1"),
        _tab("w2:t1", "w2"),
        _tab("w2:t2", "w2", focused=True),
    ]

    assert route_page_key.neighbor_tab_id(tabs, "w1", "next") == "w1:t2"
    assert route_page_key.neighbor_tab_id(tabs, "w2", "next") == "w2:t1"


def test_a_lone_tab_stays_put():
    assert (
        route_page_key.neighbor_tab_id([_tab("w1:t1", "w1", True)], "w1", "next")
        is None
    )


def test_a_workspace_without_focus_stays_put():
    tabs = [_tab("w1:t1", "w1"), _tab("w1:t2", "w1")]

    assert route_page_key.neighbor_tab_id(tabs, "w1", "next") is None


def test_main_gives_the_key_to_a_pane_running_nvim(monkeypatch):
    calls = _record_herdr_calls(
        monkeypatch, [(("pane", "process-info"), _process_info_response("nvim"))]
    )

    assert route_page_key.main(["route-page-key", "next"]) == 0
    assert ["pane", "send-keys", "w1:p1", "ctrl+pagedown"] in calls
    assert not any(call[:2] == ["tab", "focus"] for call in calls)


def test_main_maps_previous_to_the_page_up_chord(monkeypatch):
    calls = _record_herdr_calls(
        monkeypatch, [(("pane", "process-info"), _process_info_response("nvim"))]
    )

    assert route_page_key.main(["route-page-key", "previous"]) == 0
    assert ["pane", "send-keys", "w1:p1", "ctrl+pageup"] in calls


def test_main_switches_the_tab_when_no_editor_owns_the_pane(monkeypatch):
    tabs = [_tab("w1:t1", "w1", focused=True), _tab("w1:t2", "w1")]
    calls = _record_herdr_calls(
        monkeypatch,
        [
            (("pane", "process-info"), _process_info_response("bash", "claude")),
            (("tab", "list"), _tab_list_response(tabs)),
        ],
    )

    assert route_page_key.main(["route-page-key", "next"]) == 0
    assert ["tab", "focus", "w1:t2"] in calls
    assert not any(call[:2] == ["pane", "send-keys"] for call in calls)


def test_main_keeps_todays_behavior_when_the_probe_fails(monkeypatch):
    calls = _record_herdr_calls(monkeypatch, [])

    assert route_page_key.main(["route-page-key", "next"]) == 0
    assert ["pane", "send-keys", "w1:p1", "ctrl+pagedown"] in calls


def test_main_stays_quiet_outside_a_herdr_pane(monkeypatch):
    calls = _record_herdr_calls(monkeypatch, [])
    monkeypatch.delenv("HERDR_ACTIVE_PANE_ID")

    assert route_page_key.main(["route-page-key", "next"]) == 0
    assert calls == []


def test_main_rejects_an_unknown_direction(monkeypatch):
    calls = _record_herdr_calls(monkeypatch, [])

    assert route_page_key.main(["route-page-key", "sideways"]) == 2
    assert calls == []
