from pathlib import Path

USER_THEMES_PATH = Path.home() / ".config" / "hypr-theme" / "user-themes"
HYPR_THEMES_PATH = Path.home() / ".config" / "hypr" / "themes"


def format_theme_name_for_display(raw_name: str) -> str:
    return " ".join(word.capitalize() for word in raw_name.split("-"))


def collect_all_theme_names() -> list[str]:
    names = set()
    for themes_dir in [USER_THEMES_PATH, HYPR_THEMES_PATH]:
        if themes_dir.is_dir():
            for entry in themes_dir.iterdir():
                if entry.is_dir():
                    names.add(entry.name)
    return sorted(names)


def main() -> None:
    for name in collect_all_theme_names():
        print(format_theme_name_for_display(name))


if __name__ == "__main__":
    main()
