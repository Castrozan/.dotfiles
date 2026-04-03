import subprocess


def is_fuzzel_running() -> bool:
    result = subprocess.run(["pgrep", "-x", "fuzzel"], capture_output=True, text=True)
    return result.returncode == 0


def main() -> None:
    if is_fuzzel_running():
        subprocess.run(["pkill", "-x", "fuzzel"])
        return

    subprocess.run(["hypr-fuzzel"])


if __name__ == "__main__":
    main()
