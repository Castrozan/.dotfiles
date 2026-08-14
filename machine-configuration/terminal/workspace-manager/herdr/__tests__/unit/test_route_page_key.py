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
