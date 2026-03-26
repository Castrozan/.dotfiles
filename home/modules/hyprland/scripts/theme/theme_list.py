from pathlib import Path

USER_THEMES_PATH = Path.home() / ".config" / "hypr-theme" / "user-themes"


def format_theme_name_for_display(raw_name: str) -> str:
    return " ".join(word.capitalize() for word in raw_name.split("-"))


def collect_all_theme_names() -> list[str]:
    if not USER_THEMES_PATH.is_dir():
        return []
    return sorted(entry.name for entry in USER_THEMES_PATH.iterdir() if entry.is_dir())


def main() -> None:
    for name in collect_all_theme_names():
        print(format_theme_name_for_display(name))


if __name__ == "__main__":
    main()
