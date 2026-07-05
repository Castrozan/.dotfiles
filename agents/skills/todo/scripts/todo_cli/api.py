import json
import os
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://api.todoist.com/api/v1"
TOKEN_FILE = os.path.expanduser("~/.secrets/todoist-api-token")


def resolve_api_token():
    environment_token = os.environ.get("TODOIST_API_TOKEN")
    if environment_token:
        return environment_token.strip()
    if os.path.isfile(TOKEN_FILE):
        with open(TOKEN_FILE, encoding="utf-8") as token_file:
            return token_file.read().strip()
    raise SystemExit(
        "No Todoist token found. Set TODOIST_API_TOKEN or provide ~/.secrets/todoist-api-token."
    )


def send_request(method, path, token, query=None, body=None):
    url = API_BASE + path
    if query:
        url = url + "?" + urllib.parse.urlencode(query)
    payload = None
    headers = {"Authorization": "Bearer " + token}
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise SystemExit(f"Todoist API error {error.code}: {detail}")
    except urllib.error.URLError as error:
        raise SystemExit(f"Todoist request failed: {error.reason}")


def fetch_paginated(path, token, query=None):
    collected = []
    cursor = None
    while True:
        page_query = dict(query or {})
        if cursor:
            page_query["cursor"] = cursor
        payload = send_request("GET", path, token, query=page_query or None)
        collected.extend(payload.get("results", []))
        cursor = payload.get("next_cursor")
        if not cursor:
            return collected


def resolve_project_id(project, token):
    for project_entry in fetch_paginated("/projects", token):
        if (
            project_entry["id"] == project
            or project_entry["name"].lower() == project.lower()
        ):
            return project_entry["id"]
    raise SystemExit(f"Project not found: {project}")
