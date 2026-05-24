import subprocess
import sys

from jira_helper_subprocess_runner import run_jira_command


def view_issue(issue_key):
    result = run_jira_command(["issue", "view", issue_key])
    print(result.stdout)
    return result


def list_issues(
    project=None,
    status=None,
    issue_type=None,
    assignee=None,
    label=None,
    jql_query=None,
    columns=None,
):
    arguments = ["issue", "list", "--plain", "--no-input"]
    if project:
        arguments.extend(["--project", project])
    if status:
        arguments.extend(["-s", status])
    if issue_type:
        arguments.extend(["--type", issue_type])
    if assignee:
        arguments.extend(["-a", assignee])
    if label:
        arguments.extend(["--label", label])
    if jql_query:
        arguments.extend(["-q", jql_query])
    if columns:
        arguments.extend(["--columns", columns])
    result = run_jira_command(arguments)
    print(result.stdout)
    return result


def create_issue(
    summary,
    issue_type="Task",
    description=None,
    assignee=None,
    priority=None,
    labels=None,
    parent=None,
):
    arguments = ["issue", "create", "--no-input", "-t", issue_type, "-s", summary]
    if description:
        arguments.extend(["-b", description])
    if assignee:
        arguments.extend(["-a", assignee])
    if priority:
        arguments.extend(["-y", priority])
    if labels:
        arguments.extend(["-l", labels])
    if parent:
        arguments.extend(["-P", parent])
    result = run_jira_command(arguments)
    print(result.stdout)
    return result


def move_issue(issue_key, target_status, comment=None, assignee=None):
    arguments = ["issue", "move", issue_key, target_status, "--no-input"]
    if comment:
        arguments.extend(["--comment", comment])
    if assignee:
        arguments.extend(["-a", assignee])
    result = run_jira_command(arguments)
    print(result.stdout)
    return result


def edit_issue(
    issue_key, summary=None, description=None, assignee=None, labels=None, priority=None
):
    arguments = ["issue", "edit", issue_key, "--no-input"]
    if summary:
        arguments.extend(["-s", summary])
    if description:
        arguments.extend(["-b", description])
    if assignee:
        arguments.extend(["-a", assignee])
    if labels:
        arguments.extend(["-l", labels])
    if priority:
        arguments.extend(["-y", priority])
    result = run_jira_command(arguments)
    print(result.stdout)
    return result


def add_comment(issue_key, comment_body):
    result = run_jira_command(
        ["issue", "comment", "add", issue_key, "-b", comment_body, "--no-input"]
    )
    print(result.stdout)
    return result


def log_work(issue_key, time_spent, comment=None):
    arguments = ["issue", "worklog", "add", issue_key, time_spent, "--no-input"]
    if comment:
        arguments.extend(["--comment", comment])
    result = run_jira_command(arguments)
    print(result.stdout)
    return result


def open_in_browser(issue_key):
    result = run_jira_command(["open", issue_key, "--no-browser"])
    print(result.stdout)
    return result


def my_issues(status=None):
    status_flag = f" -s {status}" if status else ""
    jira_command = f"jira issue list --plain --no-input -a $(jira me){status_flag}"
    result = subprocess.run(
        jira_command,
        capture_output=True,
        text=True,
        shell=True,
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(result.stdout)
    return result
