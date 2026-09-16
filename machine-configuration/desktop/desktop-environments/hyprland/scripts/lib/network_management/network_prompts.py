import subprocess


def show_fuzzel_menu(prompt: str, options: str, lines: int = 5) -> str:
    result = subprocess.run(
        [
            "hypr-fuzzel",
            "--dmenu",
            "--width",
            "40",
            "--lines",
            str(lines),
            "--prompt",
            f"{prompt}> ",
        ],
        input=options,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def notify(message: str) -> None:
    subprocess.run(
        ["notify-send", "-t", "2000", "Network", message],
        capture_output=True,
    )


def prompt_fuzzel_input(prompt_text: str) -> str:
    result = subprocess.run(
        [
            "hypr-fuzzel",
            "--dmenu",
            "--width",
            "30",
            "--lines",
            "0",
            "--prompt",
            f"{prompt_text}> ",
        ],
        input="",
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
