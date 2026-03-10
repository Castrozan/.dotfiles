import tomllib
from pathlib import Path

TEMPLATES_DIR = Path.home() / ".config" / "hypr" / "templates"
USER_TEMPLATES_DIR = Path.home() / ".config" / "hypr-theme" / "user-templates"
NEXT_THEME_DIR = Path.home() / ".config" / "hypr-theme" / "current" / "next-theme"
COLORS_FILE = NEXT_THEME_DIR / "colors.toml"


def hex_color_to_rgb_string(hex_color: str) -> str:
    hex_value = hex_color.lstrip("#")
    red = int(hex_value[0:2], 16)
    green = int(hex_value[2:4], 16)
    blue = int(hex_value[4:6], 16)
    return f"{red},{green},{blue}"


def load_color_substitutions(colors_file: Path) -> dict[str, str]:
    with colors_file.open("rb") as f:
        colors = tomllib.load(f)

    substitutions = {}
    for key, value in colors.items():
        value_str = str(value)
        substitutions[f"{{{{ {key} }}}}"] = value_str
        substitutions[f"{{{{ {key}_strip }}}}"] = value_str.lstrip("#")
        if value_str.startswith("#"):
            substitutions[f"{{{{ {key}_rgb }}}}"] = hex_color_to_rgb_string(value_str)

    return substitutions


def find_all_template_files() -> list[Path]:
    templates = []
    for directory in [TEMPLATES_DIR, USER_TEMPLATES_DIR]:
        if directory.is_dir():
            templates.extend(directory.rglob("*.tpl"))
    return templates


def apply_substitutions_to_template(
    template_content: str, substitutions: dict[str, str]
) -> str:
    result = template_content
    for pattern, replacement in substitutions.items():
        result = result.replace(pattern, replacement)
    return result


def process_all_templates() -> None:
    if not COLORS_FILE.is_file():
        return

    substitutions = load_color_substitutions(COLORS_FILE)
    template_files = find_all_template_files()

    for template_file in template_files:
        output_filename = template_file.stem
        output_path = NEXT_THEME_DIR / output_filename
        template_content = template_file.read_text()
        processed_content = apply_substitutions_to_template(
            template_content, substitutions
        )
        output_path.write_text(processed_content)


def main() -> None:
    process_all_templates()


if __name__ == "__main__":
    main()
