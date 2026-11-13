from datetime import datetime, timezone


def read_current_produced_at():
    stamped_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    return stamped_at.replace("+00:00", "Z")


def resolve_event_source(environment):
    repository = environment.get("GITHUB_REPOSITORY")
    commit = environment.get("GITHUB_SHA")
    if not repository or not commit:
        return None
    event_source = {"repository": repository, "commit": commit}
    server_url = environment.get("GITHUB_SERVER_URL")
    run_identifier = environment.get("GITHUB_RUN_ID")
    if server_url and run_identifier:
        event_source["runUrl"] = (
            f"{server_url}/{repository}/actions/runs/{run_identifier}"
        )
    return event_source
