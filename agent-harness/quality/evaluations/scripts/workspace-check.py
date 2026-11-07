import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from workspace_checks.comments import check_workspace_file_no_comments_assertion  # noqa: E402
from workspace_checks.naming import check_workspace_file_descriptive_names_assertion  # noqa: E402

CHECKS = {
    "sem-comentarios": check_workspace_file_no_comments_assertion,
    "nomes-descritivos": check_workspace_file_descriptive_names_assertion,
}


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in CHECKS:
        print(
            f"uso: workspace-check.py {{{'|'.join(CHECKS)}}} <arquivo>", file=sys.stderr
        )
        return 2
    result = CHECKS[sys.argv[1]](Path.cwd(), sys.argv[2])
    print(f"{'OK' if result.passed else 'FALHA'} {result.name}: {result.detail}")
    return 0 if result.passed else 1


sys.exit(main())
