import subprocess


def main() -> None:
    subprocess.run(
        [
            "kitty",
            "--class",
            "clipse",
            "--override",
            "startup_session=none",
            "--override",
            "background_image=none",
            "--override",
            "background_opacity=0.85",
            "-e",
            "clipse",
        ]
    )


if __name__ == "__main__":
    main()
