from orchestrator_cli.releases.released_sessions import (
    release_directory,
    standing_releases,
)
from release_test_support import ORCHESTRATOR, RELEASED_PANE, records


def test_the_session_is_told_before_its_pane_moves_and_a_placed_pane_stays(
    scenario, moved_panes
):
    assert scenario.handover("--no-move") == 0
    assert moved_panes == []
    ((target, sender, notice),) = scenario.notifications
    assert (target, sender) == (RELEASED_PANE, ORCHESTRATOR)
    assert "replaces your brief's Contract" in notice
    assert "no more reports, decision cards or notifications" in notice
    scenario.notifications.clear()
    assert scenario.handover() == 0
    assert moved_panes == [(RELEASED_PANE, RELEASED_PANE)]
    assert len(scenario.notifications) == 1
    output = scenario.capsys.readouterr().out
    assert output.rindex("told worker-pane") < output.rindex("moved worker-pane")


def test_a_release_records_every_pane_and_the_conversation_of_the_session(
    scenario, live_panes
):
    session = {"kind": "id", "value": "conversation-1"}
    live_panes[RELEASED_PANE] = {"pane_id": "wL:p4", "agent_session": session}
    assert scenario.handover() == 0
    (release,) = records(release_directory())
    assert release["panes"] == ["wL:p4", RELEASED_PANE]
    assert release["session_identifier"] == "conversation-1"
    assert (release["pane"], release["orchestrator"]) == (RELEASED_PANE, ORCHESTRATOR)


def test_taking_a_session_back_lets_it_file_again_and_restores_its_report(scenario):
    assert scenario.file_report(state="working") == 0
    assert scenario.handover() == 0
    assert scenario.handover() == 0
    assert scenario.handover("--take-back") == 0
    assert "orchestrates you again" in scenario.notifications[-1][2]
    assert standing_releases() == [] and len(records(release_directory())) == 1
    assert [report["state"] for report in records(scenario.reports)] == ["working"]
    assert "worker-session" in scenario.round_output()
    assert scenario.file_report() == 0
    assert "worker-session is done" in scenario.notifications[-1][2]
    assert scenario.handover("--take-back") == 1
    assert "worker-pane is not released" in scenario.errors()


def test_a_release_and_a_take_back_cannot_be_asked_together(scenario):
    assert scenario.handover("--no-move", "--take-back") == 2
    assert records(release_directory()) == []
