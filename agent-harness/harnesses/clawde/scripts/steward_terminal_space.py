import os
import termios


def ensure_terminal_space():
    terminal_size = os.get_terminal_size()
    if terminal_size.lines >= 8:
        return
    termios.tcsetwinsize(1, (8, terminal_size.columns))


if __name__ == "__main__":
    ensure_terminal_space()
