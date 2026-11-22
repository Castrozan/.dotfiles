import pytest
from wake_fakes import UNREACHABLE, answered, armed_listener, boundaries, deciding
from wake_phrase import LiveSession

ANASTASIA = LiveSession("Anastasia", "wW:pAN")


def test_calling_a_servant_by_name_wakes_it_without_a_greeting():
    fakes = boundaries(
        heard="Anastasia, can you hear me?",
        sessions=(ANASTASIA,),
        decide=deciding(answered("Anastasia")),
    )
    armed_listener(fakes).hear(b"segment")
    pane, text, _ = fakes.prompt_now.call_args.args
    assert pane == ANASTASIA.pane and "Anastasia, can you hear me " in text
    fakes.open_conversation.assert_called_once_with()
    input_messages, questions = fakes.decide.call_args.args
    assert [message["role"] for message in input_messages] == ["developer", "user"]
    assert [choice["value"] for choice in questions[0]["choices"]] == [
        "Anastasia",
        "nobody",
    ]


def test_wake_speech_about_a_servant_wakes_nobody():
    fakes = boundaries(
        heard="I think Anastasia broke the build",
        sessions=(ANASTASIA,),
        decide=deciding(answered("nobody")),
    )
    armed_listener(fakes).hear(b"segment")
    fakes.prompt_now.assert_not_called()
    fakes.claim_wake.assert_not_called()
    assert "no live servant addressed" in fakes.report.call_args.args[0]


@pytest.mark.parametrize(
    ("heard", "woken"), [("hey Voyager, status", True), ("Voyager, status", False)]
)
def test_without_the_decisions_api_the_greeting_rule_wakes(heard, woken):
    fakes = boundaries(heard=heard, decide=deciding(UNREACHABLE))
    armed_listener(fakes).hear(b"segment")
    assert fakes.prompt_now.called is woken


def test_wake_speech_naming_no_live_servant_never_reaches_the_api():
    fakes = boundaries(heard="check the build", decide=deciding(answered("Voyager")))
    armed_listener(fakes).hear(b"segment")
    fakes.decide.assert_not_called()
    assert "no unique live servant" in fakes.report.call_args.args[0]
