import json
from unittest.mock import MagicMock, patch

import review_session
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
