import dataclasses
import enum

QUESTION = "addressee"
HOLDER = "holder"
NOBODY = "nobody"
CONFIDENCE_FLOOR = 0.8
SPEECH = (
    "Every utterance is a speech-to-text transcript of the person, so names and words "
    "may be misheard."
)
QUESTION_INSTRUCTIONS = (
    "Whom does the person speak to in their latest utterance, the last message, "
    "expecting that agent to answer or act right now? An agent counts only when the "
    "person calls it by name as the one they are talking to. Hearing a name does not "
    "make its agent the addressee: mentioning or talking about an agent, asking "
    "someone to tell, ask, contact or write to an agent, doing something for or "
    "about an agent, quoting or singing its name, or repeating the name while "
    "discussing names all leave that agent out."
)


@dataclasses.dataclass(frozen=True)
class Turn:
    speaker: str | None
    text: str


class Route(enum.StrEnum):
    CANDIDATE = "candidate"
    KEEP = "keep"
    NOBODY = "nobody"


@dataclasses.dataclass(frozen=True)
class Verdict:
    route: Route
    choice: object = None
    confidence: float | None = None


def listed(names):
    return ", ".join(names)


def developer_context(holder, candidates):
    if holder is None:
        return (
            "A room microphone hears a person near voice-activated AI agents named "
            f"{listed(candidates)}. Nobody is in a conversation with them yet; an "
            f"agent wakes only when the person calls it to speak with it. {SPEECH}"
        )
    return (
        f"A person is talking by voice with an AI agent named {holder}. Other live AI "
        f"agents named {listed(candidates)} can take over the conversation when the "
        f"person turns to address them. {SPEECH}"
    )


def turn_message(turn):
    said = f"{turn.speaker}: {turn.text}" if turn.speaker else turn.text
    return {"role": "user", "content": f"(earlier) {said}"}


def input_messages(utterance, turns, holder, candidates):
    return [
        {"role": "developer", "content": developer_context(holder, candidates)},
        *(turn_message(turn) for turn in turns),
        {"role": "user", "content": utterance},
    ]


def holder_choice(holder):
    return {
        "value": HOLDER,
        "description": (
            f"The person keeps talking to {holder}, the agent already in the "
            "conversation, including when other agents are only mentioned, talked "
            f"about, or to be contacted through {holder}."
        ),
    }


def candidate_choice(name):
    return {
        "value": name,
        "description": (
            f"The person calls {name} by name to talk to {name} now, so {name} should "
            f"answer; not when {name} is only the topic, someone to be told, asked or "
            "written to, or a name being sung or discussed."
        ),
    }


NOBODY_CHOICE = {
    "value": NOBODY,
    "description": (
        "The speech is not directed at any agent: singing, thinking aloud, reading "
        "aloud, or talking to another person."
    ),
}


def choices(holder, candidates):
    holding = [holder_choice(holder)] if holder is not None else []
    return [*holding, *(candidate_choice(name) for name in candidates), NOBODY_CHOICE]


def questions(holder, candidates):
    return [
        {
            "type": "choice",
            "name": QUESTION,
            "instructions": QUESTION_INSTRUCTIONS,
            "choices": choices(holder, candidates),
        }
    ]


def request(utterance, turns, holder, candidates):
    return (
        input_messages(utterance, turns, holder, candidates),
        questions(holder, candidates),
    )


def addressee_answer(answers):
    return next(
        (
            answer
            for answer in answers
            if isinstance(answer, dict) and answer.get("name") == QUESTION
        ),
        {},
    )


def confidence_of(answer):
    confidence = answer.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, int | float):
        return None
    return confidence if 0.0 <= confidence <= 1.0 else None


def chosen_value(answer):
    return answer.get("choice") if answer.get("type") == "choice" else None


def confident(confidence):
    return confidence is not None and confidence >= CONFIDENCE_FLOOR


def verdict(answers, candidates):
    answer = addressee_answer(answers)
    choice = chosen_value(answer)
    confidence = confidence_of(answer)
    if choice == NOBODY:
        return Verdict(Route.NOBODY, choice, confidence)
    if choice in candidates and confident(confidence):
        return Verdict(Route.CANDIDATE, choice, confidence)
    return Verdict(Route.KEEP, choice, confidence)
