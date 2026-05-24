from jira_helper_subprocess_runner import run_jira_command


def list_sprints(current_only=False):
    arguments = ["sprint", "list", "--plain", "--no-input"]
    if current_only:
        arguments.append("--current")
    result = run_jira_command(arguments)
    print(result.stdout)
    return result
