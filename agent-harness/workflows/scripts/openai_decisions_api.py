import concurrent.futures
import http.client
import json
import pathlib

MODEL = "gpt-6-luna"
HOST = "api.openai.com"
ENDPOINT_PATH = "/v1/decisions"
KEY_FILE = pathlib.Path.home() / ".secrets" / "openai-api-key"
TIMEOUT_SECONDS = 8.0
HTTP_OK = 200


def headers_with_key() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KEY_FILE.read_text().strip()}",
    }


def posted(body: bytes, headers: dict[str, str], timeout_seconds: float) -> object:
    connection = http.client.HTTPSConnection(HOST, timeout=timeout_seconds)
    try:
        connection.request("POST", ENDPOINT_PATH, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read()
    except http.client.HTTPException as error:
        raise OSError(f"The Decisions API broke its reply: {error!r}") from error
    finally:
        connection.close()
    if response.status != HTTP_OK:
        raise OSError(f"The Decisions API answered HTTP {response.status}")
    return json.loads(payload)


def reply(
    input_messages: list[dict],
    questions: list[dict],
    timeout_seconds: float = TIMEOUT_SECONDS,
) -> object:
    headers = headers_with_key()
    body = json.dumps(
        {"model": MODEL, "input": input_messages, "questions": questions}
    ).encode()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        return executor.submit(posted, body, headers, timeout_seconds).result(
            timeout=timeout_seconds
        )
    finally:
        executor.shutdown(wait=False)
