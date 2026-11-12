import sys
from pathlib import Path

HOOK_ROOT = Path(__file__).resolve().parents[3]
for directory in (
    "common",
    "common/personal-tooling",
    "__tests__",
    "__tests__/support",
):
    sys.path.insert(0, str(HOOK_ROOT / directory))
