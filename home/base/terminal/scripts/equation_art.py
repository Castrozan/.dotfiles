import argparse
import random
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


def twin_figures(t):
    i = point_index
    parity = (i % 2) * 9
    k = 9 * np.cos(i / 81.0)
    e = i / 765.0 - 13
    d = np.hypot(k, e) / 4.0
    inner = np.where(k * k < 19, t * 3 + d * 4, d / 2 + 4)
    q = (
        79
        - 2 * np.sin(k * 3)
        + np.sin(inner) / 2 * k * (9 + 5 * np.sin(d * d - e / 6 - t + parity))
    )
    c = d * d / 9 - t / 16 + parity
    return q * np.sin(c), (q + 50) * np.cos(c)


def solo_figure(t):
    i = point_index
    k = 9 * np.cos(i / 81.0)
    e = i / 765.0 - 13
    d = np.hypot(k, e) / 4.0
    inner = np.where(k * k < 19, t * 3 + d * 4, d / 2 + 4)
    q = (
        79
        - 2 * np.sin(k * 3)
        + np.sin(inner) / 2 * k * (9 + 5 * np.sin(d * d - e / 6 - t))
    )
    c = d * d / 9 - t / 16
    return q * np.sin(c), (q + 50) * np.cos(c)


def tight_swirl(t):
    i = point_index
    k = 9 * np.cos(i / 81.0)
    e = i / 765.0 - 13
    d = np.hypot(k, e) / 4.0
    inner = np.where(k * k < 19, t * 3 + d * 4, d / 2 + 4)
    q = (
        79
        - 2 * np.sin(k * 3)
        + np.sin(inner) / 2 * k * (9 + 5 * np.sin(d * d / 2 - e / 6 - t))
    )
    c = d * d / 12 - t / 16
    return q * np.sin(c), (q + 50) * np.cos(c)


def petal_spray(t):
    i = point_index
    k = 9 * np.cos(i / 60.0)
    e = i / 500.0 - 13
    d = np.hypot(k, e) / 4.0
    inner = np.where(k * k < 19, t * 2 + d * 3, d / 2 + 4)
    q = (
        64
        - 2 * np.sin(k * 4)
        + np.sin(inner) / 2 * k * (9 + 5 * np.sin(d * d - e / 6 - t))
    )
    c = d * d / 9 - t / 16
    return q * np.sin(c), (q + 50) * np.cos(c)


EQUATION_FORMULAS = {
    "twin": twin_figures,
    "solo": solo_figure,
    "swirl": tight_swirl,
    "petal": petal_spray,
}


def list_formula_names():
    return list(EQUATION_FORMULAS)


def render_equation_frame(t, columns, rows, formula_name):
    width = columns * 2
    height = rows * 4
    x, y = EQUATION_FORMULAS[formula_name](t)
    extent_x = np.percentile(np.abs(x), 98)
    extent_y = np.percentile(np.abs(y), 98)
    extent = max(extent_x, extent_y, 1e-6)
    scale = 0.46 * min(width, height) / extent
    xi = (x * scale + width / 2.0).astype(np.int64)
    yi = (y * scale + height / 2.0).astype(np.int64)
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


def parse_arguments():
    parser = argparse.ArgumentParser(prog="equation-art")
    parser.add_argument("--formula", choices=list_formula_names())
    parser.add_argument("--list-formulas", action="store_true")
    return parser.parse_args()


def animate(formula_name):
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
            sys.stdout.write(
                "\033[H" + render_equation_frame(t, columns, rows, formula_name)
            )
            sys.stdout.flush()
            t += TIME_STEP
            time.sleep(FRAME_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h\033[0m\n")


def main():
    arguments = parse_arguments()
    if arguments.list_formulas:
        sys.stdout.write("\n".join(list_formula_names()) + "\n")
        return
    formula_name = arguments.formula or random.choice(list_formula_names())
    animate(formula_name)


if __name__ == "__main__":
    main()
