import subprocess


def main() -> None:
    subprocess.run(
        [
            "wezterm",
            "--config",
            "window_background_opacity=0.85",
            "start",
            "--class",
            "clipse",
            "--",
            "clipse",
        ]
    )


if __name__ == "__main__":
    main()
