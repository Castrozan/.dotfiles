import importlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

jira_helper = importlib.import_module("jira-helper")
jira_helper_authentication = importlib.import_module("jira_helper_authentication")


def make_successful_subprocess_result(stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=stdout, stderr=stderr
    )


def make_failed_subprocess_result(stderr="error"):
    return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=stderr)
