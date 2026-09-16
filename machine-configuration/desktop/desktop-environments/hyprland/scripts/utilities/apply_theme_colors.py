from hyprland_runtime import ensure_hyprctl_connected
from hyprland_theme import apply_theme_border_colors_from_config


def main() -> None:
    if not ensure_hyprctl_connected():
        return
    apply_theme_border_colors_from_config()


if __name__ == "__main__":
    main()
