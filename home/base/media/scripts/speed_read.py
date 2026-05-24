import os
import re
import sys
import time
import tty
import termios
import select
from pathlib import Path

ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_RESET = "\033[0m"

DEFAULT_WPM = 400
MIN_WPM = 50
MAX_WPM = 2000
WPM_STEP = 50
DEFAULT_FOCUS_COLOR = 1
DEFAULT_CENTER_WIDTH = 40
PUNCTUATION_DELAY_MULTIPLIER = 2.5

MARKDOWN_STRIP_PATTERN = re.compile(r"^[*_#\[\]`]+|[*_#\[\]`]+$")
PUNCTUATION_PATTERN = re.compile(r"[.!?,;:\u2014\u2013-]$")


def compute_optimal_recognition_point(word: str) -> int:
    length = len(word)
    if length <= 1:
        return 0
    if length <= 5:
        return 1
    if length <= 9:
        return 2
    if length <= 13:
        return 3
    return (length - 1) // 3


def format_word_with_orp_highlight(
    word: str, focus_color: int, center_width: int
) -> str:
    orp_position = compute_optimal_recognition_point(word)
    pad_left = max(0, (center_width // 2) - orp_position)

    before = word[:orp_position]
    focus = word[orp_position : orp_position + 1]
    after = word[orp_position + 1 :]

    focus_colored = f"\033[38;5;{focus_color}m{ANSI_BOLD}{focus}{ANSI_RESET}"

    return (
        " " * pad_left
        + f"{ANSI_DIM}{before}{ANSI_RESET}"
        + focus_colored
        + f"{ANSI_DIM}{after}{ANSI_RESET}"
    )


def format_pointer_line(center_width: int) -> str:
    pad = center_width // 2
    return " " * pad + "|"


def has_trailing_punctuation(word: str) -> bool:
    return bool(PUNCTUATION_PATTERN.search(word))


def strip_markdown_formatting(word: str) -> str:
    return MARKDOWN_STRIP_PATTERN.sub("", word)


def compute_word_delay_seconds(wpm: int) -> float:
    return 60.0 / wpm


def parse_arguments(argv: list[str]) -> tuple[int, int, bool, bool, str | None]:
    wpm = int(os.environ.get("SPEED_READ_WPM", str(DEFAULT_WPM)))
    focus_color = int(
        os.environ.get("SPEED_READ_FOCUS_COLOR", str(DEFAULT_FOCUS_COLOR))
    )
    show_pointer = os.environ.get("SPEED_READ_POINTER", "true").lower() == "true"
    pause_on_punctuation = (
        os.environ.get("SPEED_READ_PAUSE_PUNCT", "true").lower() == "true"
    )
    input_file = None

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("-w", "--wpm"):
            i += 1
            if i >= len(argv):
                print("Error: --wpm requires a number", file=sys.stderr)
                raise SystemExit(1)
            wpm = int(argv[i])
        elif arg in ("-c", "--color"):
            i += 1
            if i >= len(argv):
                print("Error: --color requires a number", file=sys.stderr)
                raise SystemExit(1)
            focus_color = int(argv[i])
        elif arg in ("-p", "--no-pointer"):
            show_pointer = False
        elif arg in ("-P", "--no-pause"):
            pause_on_punctuation = False
        elif arg == "--help":
            print_usage()
            raise SystemExit(0)
        elif arg.startswith("-"):
            print(f"Unknown option: {arg}", file=sys.stderr)
            raise SystemExit(1)
        else:
            input_file = arg
        i += 1

    if not (MIN_WPM <= wpm <= MAX_WPM):
        print(f"Error: WPM must be between {MIN_WPM} and {MAX_WPM}", file=sys.stderr)
        raise SystemExit(1)

    return wpm, focus_color, show_pointer, pause_on_punctuation, input_file


def print_usage() -> None:
    print(f"""Usage: speed-read [OPTIONS] [FILE]
       echo "text" | speed-read [OPTIONS]

RSVP speed reader with ORP (Optimal Recognition Point) highlighting.
Reads text one word at a time for faster reading (up to 900+ WPM).

Options:
    -w, --wpm N         Words per minute (default: {DEFAULT_WPM})\
 Range: {MIN_WPM}-{MAX_WPM}
    -c, --color N       ANSI 256 focus color (default: {DEFAULT_FOCUS_COLOR}/red)
    -p, --no-pointer    Hide the focus pointer
    -P, --no-pause      Don't pause on punctuation
    --help              Show this help message

Keyboard Controls:
    SPACE / p           Pause/resume
    q / ESC             Quit
    + / =               Increase speed by {WPM_STEP} WPM
    - / _               Decrease speed by {WPM_STEP} WPM
    r                   Restart from beginning

Examples:
    speed-read document.txt
    echo "This is a test sentence for speed reading." | speed-read
    cat article.md | speed-read --wpm 600
    speed-read --wpm 300 --color 2""")


def read_input_text(input_file: str | None) -> str:
    if input_file:
        path = Path(input_file)
        if not path.is_file():
            print(f"Error: File not found: {input_file}", file=sys.stderr)
            raise SystemExit(1)
        return path.read_text()

    if sys.stdin.isatty():
        print("Error: No input provided. Pipe text or provide a file.", file=sys.stderr)
        print_usage()
        raise SystemExit(1)

    return sys.stdin.read()


def split_text_into_words(text: str) -> list[str]:
    return text.split()


def hide_cursor() -> None:
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor() -> None:
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def clear_current_line() -> None:
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def read_keypress_nonblocking(stdin_fd: int) -> str | None:
    ready, _, _ = select.select([stdin_fd], [], [], 0.01)
    if ready:
        try:
            return os.read(stdin_fd, 1).decode("utf-8", errors="ignore")
        except OSError:
            return None
    return None


def wait_for_unpause(stdin_fd: int) -> str | None:
    while True:
        ready, _, _ = select.select([stdin_fd], [], [], 0.1)
        if ready:
            try:
                key = os.read(stdin_fd, 1).decode("utf-8", errors="ignore")
            except OSError:
                continue
            if key in (" ", "p", "P"):
                return None
            if key in ("q", "Q", "\x1b"):
                return "quit"
    return None


def display_speed_reader(
    words: list[str],
    initial_wpm: int,
    focus_color: int,
    show_pointer: bool,
    pause_on_punctuation: bool,
    center_width: int = DEFAULT_CENTER_WIDTH,
) -> None:
    total_words = len(words)
    current_wpm = initial_wpm

    print()
    estimated_seconds = total_words * 60 // current_wpm
    print(
        f"Speed Reader - {current_wpm} WPM"
        f" | {total_words} words | ~{estimated_seconds}s"
    )
    print("Controls: [SPACE] pause | [+/-] speed | [q] quit | [r] restart")
    print()

    if show_pointer:
        print(format_pointer_line(center_width))

    hide_cursor()

    stdin_fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(stdin_fd)

    try:
        tty.setraw(stdin_fd)

        word_index = 0
        while word_index < total_words:
            key = read_keypress_nonblocking(stdin_fd)
            if key:
                if key in (" ", "p", "P"):
                    clear_current_line()
                    pause_message = (
                        f"  [PAUSED - {current_wpm} WPM"
                        f" - Word {word_index + 1}/{total_words}"
                        f" - Press SPACE to continue]"
                    )
                    sys.stdout.write(pause_message)
                    sys.stdout.flush()
                    result = wait_for_unpause(stdin_fd)
                    if result == "quit":
                        return
                    continue
                elif key in ("+", "="):
                    current_wpm = min(current_wpm + WPM_STEP, MAX_WPM)
                    continue
                elif key in ("-", "_"):
                    current_wpm = max(current_wpm - WPM_STEP, MIN_WPM)
                    continue
                elif key in ("r", "R"):
                    word_index = 0
                    continue
                elif key in ("q", "Q", "\x1b"):
                    return

            raw_word = words[word_index]
            clean_word = strip_markdown_formatting(raw_word)

            if not clean_word:
                word_index += 1
                continue

            clear_current_line()
            formatted = format_word_with_orp_highlight(
                clean_word, focus_color, center_width
            )
            sys.stdout.write(formatted)
            sys.stdout.flush()

            delay = compute_word_delay_seconds(current_wpm)
            if pause_on_punctuation and has_trailing_punctuation(clean_word):
                delay *= PUNCTUATION_DELAY_MULTIPLIER

            time.sleep(delay)
            word_index += 1

        clear_current_line()
        sys.stdout.write(
            f"\r\nDone! Read {total_words} words at ~{current_wpm} WPM\r\n"
        )
        sys.stdout.flush()
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)
        show_cursor()


def main() -> None:
    wpm, focus_color, show_pointer, pause_on_punctuation, input_file = parse_arguments(
        sys.argv[1:]
    )

    text = read_input_text(input_file)
    words = split_text_into_words(text)

    if not words:
        print("Error: No words to display", file=sys.stderr)
        raise SystemExit(1)

    display_speed_reader(words, wpm, focus_color, show_pointer, pause_on_punctuation)


if __name__ == "__main__":
    main()
