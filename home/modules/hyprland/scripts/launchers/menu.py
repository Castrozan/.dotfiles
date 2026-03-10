import subprocess
import sys


def show_fuzzel_menu(
    prompt: str, options: str, extra_args: str = "", preselect: str = ""
) -> str:
    command = [
        "hypr-fuzzel",
        "--dmenu",
        "--width",
        "30",
        "--lines",
        "10",
        "--prompt",
        f"{prompt}> ",
    ]

    if extra_args:
        command.extend(extra_args.split())

    if preselect:
        lines = options.split("\n")
        for index, line in enumerate(lines):
            if line.strip() == preselect.strip():
                command.extend(["-c", str(index + 1)])
                break

    result = subprocess.run(
        command,
        input=options,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def show_theme_menu(back_to_exit: bool) -> None:
    theme_list_result = subprocess.run(
        ["hypr-theme-list"], capture_output=True, text=True
    )
    current_theme_result = subprocess.run(
        ["hypr-theme-current"], capture_output=True, text=True
    )

    theme = show_fuzzel_menu(
        "Theme",
        theme_list_result.stdout.strip(),
        "--width 350",
        current_theme_result.stdout.strip(),
    )

    if not theme:
        if back_to_exit:
            return
        show_style_menu(back_to_exit=False)
    else:
        subprocess.run(["hypr-theme-set", theme])


def show_style_menu(back_to_exit: bool) -> None:
    selection = show_fuzzel_menu("Style", "󰸌  Theme\n  Background")

    if "Theme" in selection:
        show_theme_menu(back_to_exit)
    elif "Background" in selection:
        subprocess.run(["hypr-theme-bg-next"])
    elif not back_to_exit:
        show_main_menu(back_to_exit=False)


def show_system_menu(back_to_exit: bool) -> None:
    selection = show_fuzzel_menu("System", "  Lock\n󰜉  Restart\n󰐥  Shutdown")

    if "Lock" in selection:
        subprocess.run(["hyprlock"])
    elif "Restart" in selection:
        subprocess.run(["systemctl", "reboot"])
    elif "Shutdown" in selection:
        subprocess.run(["systemctl", "poweroff"])
    elif not back_to_exit:
        show_main_menu(back_to_exit=False)


def go_to_menu(selection: str, back_to_exit: bool) -> None:
    normalized = selection.lower()
    if "apps" in normalized:
        subprocess.run(["hypr-fuzzel"])
    elif "style" in normalized:
        show_style_menu(back_to_exit)
    elif "theme" in normalized:
        show_theme_menu(back_to_exit)
    elif "system" in normalized:
        show_system_menu(back_to_exit)


def show_main_menu(back_to_exit: bool) -> None:
    selection = show_fuzzel_menu("Go", "󰀻  Apps\n  Style\n  System")
    go_to_menu(selection, back_to_exit)


def main() -> None:
    if len(sys.argv) > 1:
        go_to_menu(sys.argv[1], back_to_exit=True)
    else:
        show_main_menu(back_to_exit=False)


if __name__ == "__main__":
    main()
