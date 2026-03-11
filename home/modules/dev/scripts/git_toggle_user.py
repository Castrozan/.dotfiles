import subprocess
import sys

WORK_NAME = "Lucas de Castro Zanoni"
WORK_EMAIL = "lucas.zanoni@betha.com.br"

PERSONAL_NAME = "Castrozan"
PERSONAL_EMAIL = "castro.lucas290@gmail.com"

ANSI_RED = "\033[0;31m"
ANSI_GREEN = "\033[0;32m"
ANSI_YELLOW = "\033[1;33m"
ANSI_BLUE = "\033[0;34m"
ANSI_RESET = "\033[0m"


def run_git_command(args: list[str]) -> str:
    result = subprocess.run(["git"] + args, capture_output=True, text=True)
    return result.stdout.strip()


def is_inside_git_repository() -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def get_current_git_user() -> tuple[str, str, str]:
    local_name = run_git_command(["config", "--local", "user.name"])
    local_email = run_git_command(["config", "--local", "user.email"])

    if local_name and local_email:
        return "LOCAL", local_name, local_email

    global_name = run_git_command(["config", "--global", "user.name"]) or "Unknown"
    global_email = (
        run_git_command(["config", "--global", "user.email"]) or "unknown@example.com"
    )
    return "GLOBAL", global_name, global_email


def set_local_git_user(name: str, email: str) -> None:
    subprocess.run(["git", "config", "--local", "user.name", name])
    subprocess.run(["git", "config", "--local", "user.email", email])


def determine_target_user(current_email: str) -> tuple[str, str, str]:
    if current_email == WORK_EMAIL:
        return "PERSONAL", PERSONAL_NAME, PERSONAL_EMAIL
    if current_email == PERSONAL_EMAIL:
        return "WORK", WORK_NAME, WORK_EMAIL

    print(
        f"{ANSI_YELLOW}!{ANSI_RESET}"
        " Current user not recognized, defaulting to personal account"
    )
    return "PERSONAL", PERSONAL_NAME, PERSONAL_EMAIL


def print_current_status(config_level: str, name: str, email: str) -> None:
    print()
    print(f"{ANSI_BLUE}i{ANSI_RESET} Current git user configuration ({config_level}):")
    print(f"  Name:  {name}")
    print(f"  Email: {email}")
    print()


def get_repository_commit_count() -> int:
    output = run_git_command(["rev-list", "--count", "HEAD"])
    try:
        return int(output)
    except ValueError:
        return 0


def print_usage() -> None:
    print("Usage: git-toggle-user [OPTIONS]")
    print()
    print(
        "Toggle between work and personal git user"
        " configurations for the current repository."
    )
    print()
    print("Options:")
    print("  -s, --status    Show current git user configuration")
    print("  -h, --help      Show this help message")
    print()
    print("User configurations:")
    print(f"  Work:     {WORK_NAME} <{WORK_EMAIL}>")
    print(f"  Personal: {PERSONAL_NAME} <{PERSONAL_EMAIL}>")


def parse_arguments(argv: list[str]) -> bool:
    show_status_only = False

    for arg in argv:
        if arg in ("-s", "--status"):
            show_status_only = True
        elif arg in ("-h", "--help"):
            print_usage()
            raise SystemExit(0)
        else:
            print(f"{ANSI_RED}x{ANSI_RESET} Unknown option: {arg}")
            print("Use --help for usage information.")
            raise SystemExit(1)

    return show_status_only


def main() -> None:
    show_status_only = parse_arguments(sys.argv[1:])

    if not is_inside_git_repository():
        print(f"{ANSI_RED}x{ANSI_RESET} Not in a git repository!")
        raise SystemExit(1)

    config_level, current_name, current_email = get_current_git_user()
    print_current_status(config_level, current_name, current_email)

    if show_status_only:
        return

    target_type, target_name, target_email = determine_target_user(current_email)
    set_local_git_user(target_name, target_email)

    print(f"{ANSI_GREEN}v{ANSI_RESET} Switched to {target_type} account:")
    print(f"  Name:  {target_name}")
    print(f"  Email: {target_email}")
    print()
    print(
        f"{ANSI_BLUE}i{ANSI_RESET}"
        " This configuration is set locally for this repository only."
    )

    commit_count = get_repository_commit_count()
    if commit_count > 0:
        print()
        print(
            f"{ANSI_YELLOW}!{ANSI_RESET} Note: This change only affects future commits."
        )
        print(
            f"{ANSI_YELLOW}!{ANSI_RESET}"
            " Existing commits will keep their original author information."
        )


if __name__ == "__main__":
    main()
