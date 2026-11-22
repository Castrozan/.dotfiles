import concurrent.futures
import http.client
import json
import pathlib
import urllib.request

MODEL = "gpt-6-luna"
KEY_FILE = pathlib.Path.home() / ".secrets" / "openai-api-key"
TIMEOUT_SECONDS = 1.5


def headers_with_key():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KEY_FILE.read_text().strip()}",
    }


def posted(body, headers):
    try:
        with urllib.request.urlopen(
            urllib.request.Request(
                "https://api.openai.com/v1/decisions",
                data=body,
                headers=headers,
                method="POST",
            ),
            timeout=TIMEOUT_SECONDS,
        ) as response:
            return json.load(response)
    except http.client.HTTPException as error:
        raise OSError(f"The Decisions API broke its reply: {error!r}") from error


def answers_in(reply):
    answered = reply.get("answers") if isinstance(reply, dict) else None
    if not isinstance(answered, list):
        raise ValueError("The Decisions API replied without a list of answers")
    return answered


def answers(input_messages, questions):
    headers = headers_with_key()
    body = {"model": MODEL, "input": input_messages, "questions": questions}
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        reply = executor.submit(posted, json.dumps(body).encode(), headers).result(
            timeout=TIMEOUT_SECONDS
        )
    finally:
        executor.shutdown(wait=False)
    return answers_in(reply)
