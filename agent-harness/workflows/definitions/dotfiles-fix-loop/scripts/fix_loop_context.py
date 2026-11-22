import argparse
import json
import sys
from pathlib import Path

from fix_loop_checkout import changed_paths, git, run_shell, tail

FAILURE_TAIL_LINES = 80


def context_document(
    task: str, test_command: str, base_revision: str, failure: str
) -> str:
    return f"""### Task

{task}

### Scoped test

`{test_command}` runs from the checkout root and fails at base revision {base_revision}.
Its latest output is in the file `test.log` beside this one; its first failure ends with:

```text
{tail(failure, FAILURE_TAIL_LINES)}
```

### Rules

Edit only what the task needs. The workflow formats changed files, runs the lint gate and the scoped test after
every edit, and owns staging, committing and pushing, so never run git add, git commit, git stash or a formatter.
"""


def parse_command_line(command_line_arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fix-loop-context",
        description=(
            "Refuse a dirty checkout or an already green scoped test, then write the "
            "fix loop's context and first failing test output as artifacts."
        ),
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--test-command", required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    return parser.parse_args(command_line_arguments)


def main() -> int:
    arguments = parse_command_line(sys.argv[1:])
    if changed_paths(arguments.root):
        raise SystemExit(
            f"{arguments.root} has uncommitted changes: start the fix loop from a "
            "clean checkout or a worktree so its commit holds only the fix"
        )
    initial = run_shell(arguments.root, arguments.test_command)
    if initial.exit_code == 0:
        raise SystemExit(
            "the scoped test already passes: give the fix loop a failing reproducer"
        )
    base_revision = git(arguments.root, "rev-parse", "HEAD").strip()
    artifacts = arguments.artifacts
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "test.log").write_text(initial.output)
    (artifacts / "task.txt").write_text(arguments.task)
    (artifacts / "base-revision").write_text(base_revision)
    context_path = artifacts / "context.md"
    context_path.write_text(
        context_document(
            arguments.task, arguments.test_command, base_revision, initial.output
        )
    )
    print(
        json.dumps({"context_path": str(context_path), "base_revision": base_revision})
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
