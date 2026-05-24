"""Fetch the authenticated user's GitLab events across both supported hosts."""

import datetime
import json
import sys

from glab_harness_api_client import gitlab_api_request
from glab_harness_gitlab_host_and_token import (
    GITLAB_HOST_COATES,
    GITLAB_HOST_PUBLIC,
    resolve_gitlab_token,
)

USER_EVENTS_HOST_ALIAS_TO_HOSTS = {
    "coates": [GITLAB_HOST_COATES],
    "public": [GITLAB_HOST_PUBLIC],
    "both": [GITLAB_HOST_COATES, GITLAB_HOST_PUBLIC],
}

USER_EVENTS_ENDPOINT_PAGE_SIZE = 100


def default_after_iso_date():
    return datetime.date.today().isoformat()


def fetch_user_events_for_host(host, after_iso_date):
    token = resolve_gitlab_token(host)
    endpoint = (
        f"events?after={after_iso_date}&per_page={USER_EVENTS_ENDPOINT_PAGE_SIZE}"
    )
    events = gitlab_api_request("GET", endpoint, token, host=host)
    return events or []


def fetch_user_events_for_alias(host_alias, after_iso_date):
    summary_by_host = {}
    for host in USER_EVENTS_HOST_ALIAS_TO_HOSTS[host_alias]:
        summary_by_host[host] = fetch_user_events_for_host(host, after_iso_date)
    return summary_by_host


def command_user_events(args, *_unused_repo_context):
    after_iso_date = args.after or default_after_iso_date()
    summary_by_host = fetch_user_events_for_alias(args.host, after_iso_date)
    json.dump(summary_by_host, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
