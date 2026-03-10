import subprocess


def main() -> None:
    result = subprocess.run(
        ["hypr-all-tiled-windows-are-in-single-group"], capture_output=True
    )
    if result.returncode != 0:
        subprocess.run(["hypr-toggle-group-for-all-workspace-windows"])


if __name__ == "__main__":
    main()
