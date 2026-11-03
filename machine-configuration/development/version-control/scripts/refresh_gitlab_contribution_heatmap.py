import argparse
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

EXPORTER_REPOSITORY = "git@github.com:Castrozan/private-gitlab-heatmap-exporter.git"
PROFILE_REPOSITORY = "Castrozan/Castrozan"
PROFILE_RECORDING_WORKFLOW = "update-readme.yml"
GENERATED_GRAPHS = ["gitlab-graph.svg", "gitlab-snk.svg", "gitlab-snk-light.svg"]
COMMITTER_NAME = "Castrozan"
COMMITTER_EMAIL = "castro.lucas290@gmail.com"
REFRESH_COMMIT_SUBJECT = "chore(graph): refresh GitLab contribution graph and snake"


def run_command(command, working_directory=None, environment=None):
    subprocess.run(command, cwd=working_directory, env=environment, check=True)


def synchronize_exporter_checkout(checkout):
    if not (checkout / ".git").is_dir():
        checkout.parent.mkdir(parents=True, exist_ok=True)
        run_command(["git", "clone", "--quiet", EXPORTER_REPOSITORY, str(checkout)])
    git = ["git", "-C", str(checkout)]
    run_command([*git, "fetch", "--quiet", "origin", "master"])
    run_command([*git, "reset", "--quiet", "--hard", "origin/master"])
    run_command([*git, "config", "user.name", COMMITTER_NAME])
    run_command([*git, "config", "user.email", COMMITTER_EMAIL])


def require_reachable_gitlab(gitlab_url, gitlab_token):
    if not gitlab_url.startswith("https://"):
        raise ValueError(f"GitLab URL must use https: {gitlab_url}")
    request = Request(
        f"{gitlab_url}/api/v4/user", headers={"PRIVATE-TOKEN": gitlab_token}
    )
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"GitLab answered {response.status}")


def generate_graphs(checkout, gitlab_url, gitlab_token):
    run_command(["npm", "ci", "--ignore-scripts", "--silent"], checkout)
    environment = {
        **os.environ,
        "GITLAB_URL": gitlab_url,
        "GITLAB_TOKEN": gitlab_token,
        "PYTHONPATH": str(checkout / ".github" / "scripts"),
    }
    run_command(
        [sys.executable, ".github/scripts/generate_all_contribution_graphs.py"],
        checkout,
        environment,
    )


def graphs_changed(checkout):
    difference = subprocess.run(
        ["git", "-C", str(checkout), "diff", "--quiet", "--", *GENERATED_GRAPHS],
        check=False,
    )
    return difference.returncode != 0


def publish_graphs(checkout):
    git = ["git", "-C", str(checkout)]
    run_command([*git, "add", "--", *GENERATED_GRAPHS])
    run_command([*git, "commit", "--quiet", "-m", REFRESH_COMMIT_SUBJECT])
    run_command([*git, "push", "--quiet", "origin", "HEAD:master"])


def request_profile_recording():
    run_command(
        [
            "gh",
            "workflow",
            "run",
            PROFILE_RECORDING_WORKFLOW,
            "--repo",
            PROFILE_REPOSITORY,
            "--ref",
            "master",
        ]
    )


def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--gitlab-url", required=True)
    parser.add_argument("--gitlab-token-file", required=True, type=Path)
    parser.add_argument("--checkout", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv=None):
    arguments = parse_arguments(argv)
    gitlab_token = arguments.gitlab_token_file.read_text().strip()
    require_reachable_gitlab(arguments.gitlab_url, gitlab_token)
    synchronize_exporter_checkout(arguments.checkout)
    generate_graphs(arguments.checkout, arguments.gitlab_url, gitlab_token)
    if not graphs_changed(arguments.checkout):
        print("GitLab contribution graphs are already current")
        return
    publish_graphs(arguments.checkout)
    request_profile_recording()
    print("Published GitLab contribution graphs and requested a profile recording")


if __name__ == "__main__":
    main()
