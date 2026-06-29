import json
import os
import time
import urllib.request

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_OPERATION_POLL_SECONDS = 10
GEMINI_OPERATION_TIMEOUT_SECONDS = 600


OPENAI_API_BASE_URL = "https://api.openai.com/v1"


def _resolve_api_key(environment_variables, secret_filename):
    for environment_variable in environment_variables:
        value = os.environ.get(environment_variable)
        if value and value.strip():
            return value.strip()
    secret_path = os.path.expanduser(f"~/.secrets/{secret_filename}")
    if os.path.exists(secret_path):
        with open(secret_path) as secret_file:
            value = secret_file.read().strip()
        if value:
            return value
    return None


def resolve_gemini_api_key():
    return _resolve_api_key(("GEMINI_API_KEY", "GOOGLE_API_KEY"), "gemini-api-key")


def resolve_openai_api_key():
    return _resolve_api_key(("OPENAI_API_KEY",), "openai-api-key")


def post_json(url, headers, payload):
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def get_json(url, headers):
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def download_to_file(url, headers, output_path):
    request = urllib.request.Request(url, headers=headers, method="GET")
    with (
        urllib.request.urlopen(request) as response,
        open(output_path, "wb") as output_file,
    ):
        output_file.write(response.read())


def generate_with_gemini_veo(model_spec, prompt, parameters, output_path, api_key):
    model = model_spec["repository"]
    json_headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    key_only_headers = {"x-goog-api-key": api_key}

    request_body = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "aspectRatio": parameters["aspect_ratio"],
            "resolution": parameters["resolution"],
            "durationSeconds": parameters["duration_seconds"],
            "personGeneration": "allow_all",
        },
    }

    operation = post_json(
        f"{GEMINI_API_BASE_URL}/models/{model}:predictLongRunning",
        json_headers,
        request_body,
    )
    operation_name = operation["name"]

    deadline = time.monotonic() + GEMINI_OPERATION_TIMEOUT_SECONDS
    status = get_json(f"{GEMINI_API_BASE_URL}/{operation_name}", key_only_headers)
    while not status.get("done"):
        if time.monotonic() > deadline:
            raise RuntimeError("Veo generation timed out while polling the operation")
        time.sleep(GEMINI_OPERATION_POLL_SECONDS)
        status = get_json(f"{GEMINI_API_BASE_URL}/{operation_name}", key_only_headers)

    if "error" in status:
        raise RuntimeError(f"Veo generation failed: {status['error']}")

    video_uri = status["response"]["generateVideoResponse"]["generatedSamples"][0][
        "video"
    ]["uri"]
    download_to_file(video_uri, key_only_headers, output_path)


def generate_with_openai_sora(model_spec, prompt, parameters, output_path, api_key):
    model = model_spec["repository"]
    json_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    auth_headers = {"Authorization": f"Bearer {api_key}"}

    request_body = {
        "model": model,
        "prompt": prompt,
        "seconds": str(parameters["duration_seconds"]),
        "size": parameters["size"],
    }

    video = post_json(f"{OPENAI_API_BASE_URL}/videos", json_headers, request_body)
    video_id = video["id"]

    deadline = time.monotonic() + GEMINI_OPERATION_TIMEOUT_SECONDS
    while video.get("status") not in ("completed", "failed"):
        if time.monotonic() > deadline:
            raise RuntimeError("Sora generation timed out while polling the video job")
        time.sleep(GEMINI_OPERATION_POLL_SECONDS)
        video = get_json(f"{OPENAI_API_BASE_URL}/videos/{video_id}", auth_headers)

    if video.get("status") == "failed":
        raise RuntimeError(f"Sora generation failed: {video.get('error')}")

    download_to_file(
        f"{OPENAI_API_BASE_URL}/videos/{video_id}/content", auth_headers, output_path
    )
