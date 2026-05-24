"""GitLab REST API request helpers and project/user identifier encoding."""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

from glab_harness_gitlab_host_and_token import GITLAB_HOST_COATES


def gitlab_api_base_for_host(host):
    return f"https://{host}/api/v4"


def gitlab_api_request(method, endpoint, token, body=None, host=GITLAB_HOST_COATES):
    url = f"{gitlab_api_base_for_host(host)}/{endpoint}"
    headers = {"PRIVATE-TOKEN": token}

    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
            if response_body.strip():
                return json.loads(response_body)
            return {}
    except urllib.error.HTTPError as http_error:
        error_body = http_error.read().decode("utf-8")
        print(f"API error ({http_error.code}): {error_body}", file=sys.stderr)
        sys.exit(1)


def encoded_project_path(project_path):
    return urllib.parse.quote(project_path, safe="")


def resolve_username_to_id(username, token, host):
    encoded_username = urllib.parse.quote(username.strip())
    users = gitlab_api_request(
        "GET", f"users?username={encoded_username}", token, host=host
    )
    if users:
        return users[0]["id"]
    print(f"Warning: user '{username}' not found", file=sys.stderr)
    return None


def resolve_comma_separated_usernames_to_ids(usernames_string, token, host):
    user_ids = []
    for username in usernames_string.split(","):
        user_id = resolve_username_to_id(username, token, host)
        if user_id:
            user_ids.append(user_id)
    return user_ids
