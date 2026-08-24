from hey_bot.conversation_state import ConversationMode, ConversationState, MachineSettings

SETTINGS = MachineSettings(keywords_pattern="clever|jarvis")

EMPTY_CHUNK = ""
SHORT_CHUNK = "good morning"
KEYWORD_CHUNK = "hey clever"
LONG_CHUNK = "the coffee machine is running"

LISTENING = ConversationState()
COLLECTING = ConversationState(
    mode=ConversationMode.COMMAND, keyword_phrase=KEYWORD_CHUNK
)
FOLLOWING_UP = ConversationState(
    mode=ConversationMode.FOLLOWUP,
    followup_chunks_remaining=SETTINGS.followup_window_chunks,
)


def action_types(transition):
    return tuple(type(action) for action in transition.actions)
