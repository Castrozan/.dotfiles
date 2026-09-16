import os
import sys
from pathlib import Path

BASE_CONFIG_PATH = Path.home() / ".config" / "fuzzel" / "fuzzel.ini"
THEME_COLORS_PATH = (
    Path.home() / ".config" / "hypr-theme" / "current" / "theme" / "fuzzel.ini"
)
MERGED_CONFIG_PATH = Path.home() / ".cache" / "hypr-theme" / "fuzzel-merged.ini"


def merge_fuzzel_configs() -> Path | None:
    if not THEME_COLORS_PATH.is_file():
        return None

    MERGED_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    base_content = BASE_CONFIG_PATH.read_text() if BASE_CONFIG_PATH.is_file() else ""
    theme_content = THEME_COLORS_PATH.read_text()

    MERGED_CONFIG_PATH.write_text(base_content + "\n" + theme_content)
    return MERGED_CONFIG_PATH


def main() -> None:
    merged_config = merge_fuzzel_configs()
    extra_args = sys.argv[1:]

    if merged_config is not None:
        os.execvp("fuzzel", ["fuzzel", f"--config={merged_config}", *extra_args])
    else:
        os.execvp("fuzzel", ["fuzzel", *extra_args])


if __name__ == "__main__":
    main()
