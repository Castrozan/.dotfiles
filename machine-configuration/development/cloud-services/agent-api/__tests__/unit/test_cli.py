import json
import uuid

from agent_api.cli import main


def test_discovery_and_inspection_create_no_state(tmp_path, capsys):
    state = tmp_path / "state"
    assert main(["--state-directory", str(state), "discover", "transcribe"]) == 0
    assert (
        json.loads(capsys.readouterr().out)["capabilities"][0]["id"]
        == "audio.transcribe"
    )
    assert main(["--state-directory", str(state), "inspect", "web.extract"]) == 0
    assert "input_schema" in json.loads(capsys.readouterr().out)
    assert not state.exists()


def test_cli_reports_invalid_json_and_missing_operations(tmp_path, capsys):
    state = tmp_path / "state"
    assert (
        main(["--state-directory", str(state), "run", "web.extract", "--input", "{"])
        == 1
    )
    assert json.loads(capsys.readouterr().err)["error"] == "invalid_json"
    assert main(["--state-directory", str(state), "operation", str(uuid.uuid4())]) == 1
    assert json.loads(capsys.readouterr().err)["error"] == "operation_not_found"


def test_cli_prints_identity_and_passes_the_validated_request(
    tmp_path, capsys, monkeypatch
):
    operation_id = str(uuid.uuid4())

    def run(self, identifier, request):
        assert identifier == operation_id
        assert request.input == {"url": "https://example.com"}
        return {"status": "succeeded"}

    monkeypatch.setattr("agent_api.cli.CapabilityService.run", run)
    assert (
        main(
            [
                "--state-directory",
                str(tmp_path / "state"),
                "run",
                "web.extract",
                "--operation-id",
                operation_id,
                "--input",
                '{"url":"https://example.com"}',
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    assert json.loads(output.out)["status"] == "succeeded"
    assert json.loads(output.err)["operation_id"] == operation_id
