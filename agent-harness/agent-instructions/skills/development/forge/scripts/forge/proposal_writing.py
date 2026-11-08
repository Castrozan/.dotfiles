import subprocess

from forge.native import capture_json, project_endpoint
from forge.proposal_reading import merge_request_endpoint


def run_text(command, standard_input=None, timeout=60):
    return subprocess.run(
        command,
        input=standard_input,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    ).stdout.strip()


def gitlab_write(repository, method, endpoint, fields):
    field_arguments = [
        argument
        for name, value in fields.items()
        for argument in ("-f", f"{name}={value}")
    ]
    return capture_json(
        [
            "glab",
            "api",
            "-X",
            method,
            endpoint,
            *field_arguments,
            "--hostname",
            repository.hostname,
        ]
    )


def open_change_request(repository, source_branch, target_branch, title, body):
    if repository.provider == "github":
        url = run_text(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                repository.url,
                "--head",
                source_branch,
                "--base",
                target_branch,
                "--title",
                title,
                "--body-file",
                "-",
            ],
            standard_input=body,
        )
        return {"number": int(url.rstrip("/").rsplit("/", 1)[-1]), "url": url}
    created = gitlab_write(
        repository,
        "POST",
        f"{project_endpoint(repository)}/merge_requests",
        {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": body,
        },
    )
    return {"number": created["iid"], "url": created["web_url"]}


def comment_on_change_request(repository, number, body):
    if repository.provider == "github":
        run_text(
            [
                "gh",
                "pr",
                "comment",
                str(number),
                "--repo",
                repository.url,
                "--body-file",
                "-",
            ],
            standard_input=body,
        )
        return
    gitlab_write(
        repository,
        "POST",
        f"{merge_request_endpoint(repository, number)}/notes",
        {"body": body},
    )


def replace_change_request_body(repository, number, body):
    if repository.provider == "github":
        run_text(
            [
                "gh",
                "pr",
                "edit",
                str(number),
                "--repo",
                repository.url,
                "--body-file",
                "-",
            ],
            standard_input=body,
        )
        return
    gitlab_write(
        repository,
        "PUT",
        merge_request_endpoint(repository, number),
        {"description": body},
    )


def merge_change_request(repository, number):
    if repository.provider == "github":
        run_text(
            ["gh", "pr", "merge", str(number), "--repo", repository.url, "--merge"]
        )
        return
    gitlab_write(
        repository, "PUT", f"{merge_request_endpoint(repository, number)}/merge", {}
    )
