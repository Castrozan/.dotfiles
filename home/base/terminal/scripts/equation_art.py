import math
import shutil
import sys
import time

sin = math.sin
cos = math.cos
hypot = math.hypot

BRAILLE_BASE = 0x2800
DOT_BIT = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]

POINT_COUNT = 22000


def render_equation_frame(t, columns, rows):
    width = columns * 2
    height = rows * 4
    grid = [0] * (columns * rows)
    scale = min(width, height) / 300.0
    off_x = width / 2.0
    off_y = height / 2.0
    for i in range(1, POINT_COUNT):
        m = (i % 2) * 9
        k = 9 * cos(i / 81.0)
        e = i / 765.0 - 13
        d = hypot(k, e) / 4.0
        inner = t * 3 + d * 4 if k * k < 19 else d / 2 + 4
        q = (
            79
            - 2 * sin(k * 3)
            + sin(inner) / 2 * k * (9 + 5 * sin(d * d - e / 6 - t + m))
        )
        c = d * d / 9 - t / 16 + m
        xi = int(q * sin(c) * scale + off_x)
        yi = int((q + 50) * cos(c) * scale + off_y)
        if 0 <= xi < width and 0 <= yi < height:
            grid[(yi // 4) * columns + (xi // 2)] |= DOT_BIT[yi % 4][xi % 2]
    lines = []
    for row_index in range(rows):
        base = row_index * columns
        lines.append(
            "".join(
                chr(BRAILLE_BASE + value) if value else " "
                for value in grid[base : base + columns]
            )
        )
    return "\n".join(lines)


def main():
    sys.stdout.write("\033[?25l\033[2J")
    previous_size = None
    t = 0.0
    try:
        while True:
            columns, rows = shutil.get_terminal_size((80, 24))
            rows = max(rows - 1, 8)
            if (columns, rows) != previous_size:
                sys.stdout.write("\033[2J")
                previous_size = (columns, rows)
            sys.stdout.write("\033[H" + render_equation_frame(t, columns, rows))
            sys.stdout.flush()
            t += math.pi / 45
            time.sleep(1 / 30)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h\033[0m\n")


if __name__ == "__main__":
    main()
