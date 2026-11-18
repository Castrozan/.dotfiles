import re


def resolve_producing_run(event, read_run):
    if "workflow_run" in event:
        return event["workflow_run"]
    inputs = event.get("inputs")
    identifier = inputs.get("producing_run_id") if isinstance(inputs, dict) else None
    if not isinstance(identifier, str) or not re.fullmatch(r"[1-9][0-9]*", identifier):
        raise ValueError("Invalid retained producing run identifier")
    run = read_run(identifier)
    if str(run["id"]) != identifier:
        raise ValueError("Requested producing run differs from returned metadata")
    return run


def write_producing_environment(workflow, target):
    values = {
        "SOURCE_RUN_ID": workflow["runId"],
        "SOURCE_RUN_ATTEMPT": workflow["runAttempt"],
        "SOURCE_REVISION": workflow["revision"],
    }
    with target.open("a") as output:
        output.write("".join(f"{name}={value}\n" for name, value in values.items()))
