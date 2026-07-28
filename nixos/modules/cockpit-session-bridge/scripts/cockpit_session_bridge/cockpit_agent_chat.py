import asyncio
import json

COCKPIT_AGENT_CHAT_PATH = "/cockpit/agent-chat"
MESSAGE_PLACEHOLDER = "{message}"
SESSION_KEY_PLACEHOLDER = "{sessionKey}"
DEFAULT_SESSION_KEY = "cockpit"
AGENT_REPLY_TIMEOUT_SECONDS = 180


def decode_agent_chat_request(raw_request_message):
    if not isinstance(raw_request_message, str):
        return None
    try:
        decoded_request = json.loads(raw_request_message)
    except (ValueError, TypeError):
        return None
    if not isinstance(decoded_request, dict):
        return None
    requested_text = decoded_request.get("text")
    if not isinstance(requested_text, str) or not requested_text.strip():
        return None
    requested_session_key = decoded_request.get("sessionKey")
    if not isinstance(requested_session_key, str) or not requested_session_key:
        requested_session_key = DEFAULT_SESSION_KEY
    return {"text": requested_text.strip(), "sessionKey": requested_session_key}


def build_agent_chat_command(agent_chat_command, agent_chat_request):
    return [
        command_argument.replace(
            MESSAGE_PLACEHOLDER, agent_chat_request["text"]
        ).replace(SESSION_KEY_PLACEHOLDER, agent_chat_request["sessionKey"])
        for command_argument in agent_chat_command
    ]


def read_agent_reply_text(raw_agent_output):
    decoded_output = raw_agent_output.strip()
    if not decoded_output:
        return ""
    try:
        decoded_reply = json.loads(decoded_output)
    except (ValueError, TypeError):
        return decoded_output
    if isinstance(decoded_reply, dict):
        for reply_field_name in ("text", "message", "reply", "content"):
            reply_field = decoded_reply.get(reply_field_name)
            if isinstance(reply_field, str) and reply_field:
                return reply_field
    return decoded_output


async def run_agent_chat_command(agent_chat_command, subprocess_runner):
    agent_process = await subprocess_runner(*agent_chat_command)
    standard_output, standard_error = await asyncio.wait_for(
        agent_process.communicate(), AGENT_REPLY_TIMEOUT_SECONDS
    )
    if agent_process.returncode != 0:
        return {
            "type": "error",
            "text": standard_error.decode(errors="replace").strip()
            or "the agent command failed",
        }
    return {
        "type": "reply",
        "text": read_agent_reply_text(standard_output.decode(errors="replace")),
    }


async def build_agent_chat_reply(
    agent_chat_command, raw_request_message, subprocess_runner
):
    if not agent_chat_command:
        return {"type": "error", "text": "no agent chat command is configured"}
    agent_chat_request = decode_agent_chat_request(raw_request_message)
    if agent_chat_request is None:
        return {"type": "error", "text": "invalid request"}
    try:
        return await run_agent_chat_command(
            build_agent_chat_command(agent_chat_command, agent_chat_request),
            subprocess_runner,
        )
    except TimeoutError:
        return {"type": "error", "text": "the agent did not reply in time"}
    except OSError as command_failure:
        return {"type": "error", "text": str(command_failure)}


async def stream_agent_chat_over_websocket(
    websocket_connection, agent_chat_command, subprocess_runner
):
    from websockets.exceptions import ConnectionClosed

    async for raw_request_message in websocket_connection:
        agent_chat_reply = await build_agent_chat_reply(
            agent_chat_command, raw_request_message, subprocess_runner
        )
        try:
            await websocket_connection.send(json.dumps(agent_chat_reply))
        except ConnectionClosed:
            return
