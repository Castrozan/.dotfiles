import subprocess
import sys


def run_jira_command(arguments, expect_output=True):
    command = ["jira"] + arguments
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        if expect_output:
            sys.exit(1)
    return result
