from pathlib import Path

THEME_NAME_FILE = Path.home() / ".config" / "hypr-theme" / "current" / "theme.name"


def read_current_theme_name() -> str:
    try:
        return THEME_NAME_FILE.read_text().strip()
    except FileNotFoundError:
        return "none"


def main() -> None:
    print(read_current_theme_name())


if __name__ == "__main__":
    main()
