import yaml


def executable_workflow_jobs(path, repository_root, prefix="", visited=None):
    visited = set() if visited is None else visited
    assert path not in visited, "Reusable workflow cycle"
    workflow = yaml.safe_load(path.read_text())
    for name, job in workflow["jobs"].items():
        identifier = f"{prefix}{name}"
        reusable = job.get("uses", "")
        if reusable.startswith("./.github/workflows/"):
            yield from executable_workflow_jobs(
                repository_root / reusable,
                repository_root,
                f"{identifier}/",
                visited | {path},
            )
        else:
            yield identifier, job
