import subprocess


def main() -> None:
    subprocess.run(
        [
            "wezterm",
            "start",
            "--class",
            "clipse",
            "--",
            "clipse",
        ]
    )


if __name__ == "__main__":
    main()
