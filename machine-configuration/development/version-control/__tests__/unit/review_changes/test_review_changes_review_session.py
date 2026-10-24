import json
from unittest.mock import MagicMock, patch

import review_session
from change_requests import ChangeRequest
from review_target import ReviewTarget

REVIEW_TARGET = ReviewTarget("388", "head", "merge-base", None)


def test_review_unzooms_then_moves_into_a_focused_tab_labelled_with_its_selector(
    monkeypatch,
):
    monkeypatch.setenv("HERDR_PANE_ID", "w1:p5")
    with patch("review_session.run_command") as run_command:
        review_session.move_review_into_its_own_tab(REVIEW_TARGET)
    unzoom_call, move_call = run_command.call_args_list
    assert unzoom_call.args[0] == ["herdr", "pane", "zoom", "w1:p5", "--off"]
    assert move_call.args[0] == (
        [
            "herdr",
            "pane",
            "move",
            "w1:p5",
            "--new-tab",
            "--label",
            "review 388",
            "--focus",
        ]
    )


def test_review_outside_herdr_stays_in_the_current_terminal(monkeypatch):
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
    with patch("review_session.run_command") as run_command:
        review_session.move_review_into_its_own_tab(REVIEW_TARGET)
        assert review_session.open_description_pane(review_session.Path("/x")) is None
    run_command.assert_not_called()


def test_description_pane_splits_the_review_pane_and_pages_the_description(
    monkeypatch,
):
    monkeypatch.setenv("HERDR_PANE_ID", "w1:p5")
    split_output = json.dumps({"result": {"pane": {"pane_id": "w1:p6"}}})
    with patch(
        "review_session.run_command",
        side_effect=[MagicMock(returncode=0, stdout=split_output), MagicMock()],
    ) as run_command:
        description_pane = review_session.open_description_pane(
            review_session.Path("/review/description.md")
        )
    assert description_pane == "w1:p6"
    split_call, page_call = run_command.call_args_list
    assert split_call.args[0][:4] == ["herdr", "pane", "split", "w1:p5"]
    assert page_call.args[0] == ["herdr", "pane", "run", "w1:p6", "less description.md"]


def test_forge_review_key_runs_this_cli_for_the_request_with_quoted_branch():
    change_request = ChangeRequest(
        title="Title",
        description="",
        web_url="https://gitlab.example/group/project/-/merge_requests/7",
        base_branch="main",
        head_branch="topic with space",
        head_fetch_reference="merge-requests/7/head",
    )
    lazygit_config = review_session.forge_review_lazygit_config(change_request)
    assert "  - key: I\n" in lazygit_config
    assert "    output: terminal\n" in lazygit_config
    forge_review_command = json.loads(lazygit_config.split("command: ", 1)[1])
    assert forge_review_command.endswith(
        "review_changes_cli.py --forge-review"
        " https://gitlab.example/group/project/-/merge_requests/7"
        " 'topic with space'"
    )


def test_lazygit_layers_the_review_config_over_the_user_config(tmp_path):
    user_config_file = tmp_path / "config.yml"
    user_config_file.write_text("gui: {}\n")
    review_config_file = tmp_path / "forge-review.yml"
    with patch(
        "review_session.run_command",
        return_value=MagicMock(stdout=f"{tmp_path}\n"),
    ):
        arguments = review_session.lazygit_arguments(review_config_file)
    assert arguments == [
        "lazygit",
        "--use-config-file",
        f"{user_config_file},{review_config_file}",
    ]


def test_branch_review_runs_plain_lazygit():
    assert review_session.lazygit_arguments(None) == ["lazygit"]
