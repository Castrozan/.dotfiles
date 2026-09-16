import subprocess


def main() -> None:
    subprocess.run(
        [
            "wezterm",
            "start",
            "--",
            "clipse",
        ]
    )


if __name__ == "__main__":
    main()
