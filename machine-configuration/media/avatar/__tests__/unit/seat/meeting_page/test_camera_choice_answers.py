import pathlib


def test_the_camera_choice_answers_do_not_end_another_agents_command():
    command_client = (
        pathlib.Path(__file__).resolve().parents[4] / "scripts/command.js"
    ).read_text()
    identified = command_client.split("IDENTIFIED_RESPONSES = [")[1].split("]")[0]
    assert '"cameraList"' in identified
    assert '"cameraResult"' in identified
