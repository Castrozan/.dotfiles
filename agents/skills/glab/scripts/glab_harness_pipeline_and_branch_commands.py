"""Pipeline listing/jobs and branch deletion commands."""

import urllib.parse

from glab_harness_api_client import encoded_project_path, gitlab_api_request


def command_pipelines(args, token, project, host):
    project_encoded = encoded_project_path(project)
    endpoint = f"projects/{project_encoded}/pipelines?per_page={args.count}"
    if args.ref:
        endpoint += f"&ref={urllib.parse.quote(args.ref)}"
    pipelines = gitlab_api_request("GET", endpoint, token, host=host)
    for pipeline in pipelines:
        print(
            f"#{pipeline['id']} | {pipeline['status']:10s} | {pipeline['source']:20s} | {pipeline['created_at']}"
        )


def command_pipeline_jobs(args, token, project, host):
    project_encoded = encoded_project_path(project)
    jobs = gitlab_api_request(
        "GET",
        f"projects/{project_encoded}/pipelines/{args.pipeline_id}/jobs?per_page=50",
        token,
        host=host,
    )
    for job in jobs:
        finished = job.get("finished_at", "")
        print(f"  {job['name']:30s} {job['status']:12s} {job['stage']:15s} {finished}")


def command_delete_branch(args, token, project, host):
    project_encoded = encoded_project_path(project)
    encoded_branch = urllib.parse.quote(args.branch_name, safe="")
    gitlab_api_request(
        "DELETE",
        f"projects/{project_encoded}/repository/branches/{encoded_branch}",
        token,
        host=host,
    )
    print(f"Branch '{args.branch_name}' deleted")
