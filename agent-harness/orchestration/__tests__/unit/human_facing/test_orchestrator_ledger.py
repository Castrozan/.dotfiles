import json

from orchestration_test_support import PANE_SENDER_NAME, run_orchestrator


def ledger(monkeypatch, directory, *arguments):
    return run_orchestrator(monkeypatch, directory, *arguments, command="ledger")


def recorded_identifier(capsys):
    return capsys.readouterr().out.split()[1]


def round_output(monkeypatch, tmp_path, capsys):
    capsys.readouterr()
    exit_code = run_orchestrator(
        monkeypatch,
        tmp_path / "cards",
        "--for",
        PANE_SENDER_NAME,
        "--reports-dir",
        str(tmp_path / "reports"),
        "--ledger-dir",
        str(tmp_path / "ledger"),
        command="round",
    )
    assert exit_code == 0
    return capsys.readouterr().out


def test_an_ask_reaches_its_session_and_stays_in_the_round_until_closed(
    monkeypatch, tmp_path, capsys, notifications
):
    directory = tmp_path / "ledger"
    words = "merge these two mrs into one single"
    assert (
        ledger(monkeypatch, directory, "ask", "--words", words, "--to", "w3E:p1") == 0
    )
    identifier = recorded_identifier(capsys)
    assert notifications[-1][0] == "w3E:p1"
    assert f'Lucas\'s words: "{words}"' in notifications[-1][2]
    output = round_output(monkeypatch, tmp_path, capsys)
    assert "### Your asks still open" in output
    assert f"| 1 | {words} | w3E:p1 |" in output
    assert (
        ledger(monkeypatch, directory, "close", identifier, "--evidence", "one MR") == 0
    )
    assert "Your asks still open" not in round_output(monkeypatch, tmp_path, capsys)
    assert (
        ledger(monkeypatch, directory, "close", identifier, "--evidence", "again") == 1
    )
    assert "is not an open ask" in capsys.readouterr().err


def test_a_fact_stays_on_record_without_entering_the_round(
    monkeypatch, tmp_path, capsys, notifications
):
    directory = tmp_path / "ledger"
    assert (
        ledger(
            monkeypatch,
            directory,
            "fact",
            "--words",
            "i asked the reviewer to look at the infra change",
        )
        == 0
    )
    identifier = recorded_identifier(capsys)
    assert notifications == []
    record = json.loads((directory / f"{identifier}.json").read_text())
    assert record["state"] == "standing" and record["owner"] == "orchestrator"
    assert "Your asks still open" not in round_output(monkeypatch, tmp_path, capsys)
    assert ledger(monkeypatch, directory, "list") == 0
    assert "fact standing · orchestrator" in capsys.readouterr().out
    assert ledger(monkeypatch, directory, "close", identifier, "--evidence", "x") == 1


def test_the_round_shows_five_asks_and_points_to_the_rest(
    monkeypatch, tmp_path, capsys, notifications
):
    directory = tmp_path / "ledger"
    for index in range(7):
        assert (
            ledger(monkeypatch, directory, "ask", "--words", f"ask number {index}") == 0
        )
    output = round_output(monkeypatch, tmp_path, capsys)
    assert output.count("| ask number") == 5
    assert "2 more: `orchestrator ledger list`" in output


def test_an_ask_without_words_is_refused(monkeypatch, tmp_path, capsys, notifications):
    assert ledger(monkeypatch, tmp_path / "ledger", "ask", "--words", "  ") == 1
    assert "verbatim" in capsys.readouterr().err
    assert not (tmp_path / "ledger").exists()


def test_an_ask_for_an_ambiguous_session_is_not_recorded(
    monkeypatch, tmp_path, capsys, notifications
):
    reports = tmp_path / "reports"
    reports.mkdir()
    for name, pane in (("Archer-a", "w1:p1"), ("Archer-b", "w1:p2")):
        record = {"name": name, "requester": "Archer", "requester_pane": pane}
        (reports / f"{name}.json").write_text(json.dumps(record))
    arguments = ("ask", "--words", "ship it", "--to", "Archer")
    assert (
        ledger(
            monkeypatch, tmp_path / "ledger", *arguments, "--reports-dir", str(reports)
        )
        == 1
    )
    assert "matches several sessions" in capsys.readouterr().err
    assert not (tmp_path / "ledger").exists() and notifications == []
