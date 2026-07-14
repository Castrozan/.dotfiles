import shutil
import sys
import time

import numpy as np

BRAILLE_BASE = 0x2800
BLANK_GLYPH = 0x20
DOT_BIT = np.array(
    [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]], dtype=np.uint16
)

POINT_COUNT = 22000
FRAMES_PER_SECOND = 15
FRAME_INTERVAL_SECONDS = 1.0 / FRAMES_PER_SECOND
TIME_STEP = 2 * np.pi / 45

point_index = np.arange(1, POINT_COUNT, dtype=np.float64)
parity_offset = (point_index % 2) * 9
k = 9 * np.cos(point_index / 81.0)
e = point_index / 765.0 - 13
d = np.hypot(k, e) / 4.0


def render_equation_frame(t, columns, rows):
    width = columns * 2
    height = rows * 4
    scale = min(width, height) / 300.0
    off_x = width / 2.0
    off_y = height / 2.0
    inner = np.where(k * k < 19, t * 3 + d * 4, d / 2 + 4)
    q = (
        79
        - 2 * np.sin(k * 3)
        + np.sin(inner) / 2 * k * (9 + 5 * np.sin(d * d - e / 6 - t + parity_offset))
    )
    c = d * d / 9 - t / 16 + parity_offset
    xi = (q * np.sin(c) * scale + off_x).astype(np.int64)
    yi = ((q + 50) * np.cos(c) * scale + off_y).astype(np.int64)
    visible = (xi >= 0) & (xi < width) & (yi >= 0) & (yi < height)
    xi = xi[visible]
    yi = yi[visible]
    cell = (yi // 4) * columns + (xi // 2)
    bits = DOT_BIT[yi % 4, xi % 2]
    grid = np.zeros(columns * rows, dtype=np.uint16)
    np.bitwise_or.at(grid, cell, bits)
    glyphs = np.where(grid > 0, grid + BRAILLE_BASE, BLANK_GLYPH)
    lines = [
        "".join(map(chr, glyphs[row_index * columns : (row_index + 1) * columns]))
        for row_index in range(rows)
    ]
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
            t += TIME_STEP
            time.sleep(FRAME_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h\033[0m\n")


if __name__ == "__main__":
    main()
