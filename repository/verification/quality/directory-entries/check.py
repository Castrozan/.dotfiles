import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
POLICY_DIRECTORY = (
    REPOSITORY_ROOT / "agent-harness/hooks/runtime/post-tool-use/directory-entries"
)
sys.path.insert(0, str(POLICY_DIRECTORY))

from directory_entry_policy import DIRECTORY_ENTRY_LIMIT, directory_entry_violations  # noqa: E402
from repository_directory_entries import (  # noqa: E402
    directory_entry_ceilings,
    repository_entry_counts,
)


def main():
    counts = repository_entry_counts(REPOSITORY_ROOT)
    ceilings = directory_entry_ceilings(REPOSITORY_ROOT)
    failures = [
        violation.describe()
        for violation in directory_entry_violations(counts, ceilings)
    ]
    for directory, ceiling in sorted(ceilings.items()):
        if directory == ".":
            continue
        count = counts.get(directory, 0)
        if count < ceiling:
            action = (
                "remove its baseline entry"
                if count <= DIRECTORY_ENTRY_LIMIT
                else f"lower its ceiling to {count}"
            )
            failures.append(f"{directory} shrank from {ceiling} to {count}; {action}.")
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        return 1
    print(
        f"Directory entry check: OK ({len(ceilings)} existing ceilings; limit {DIRECTORY_ENTRY_LIMIT} elsewhere)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
