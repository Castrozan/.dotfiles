BUTTON_AREAS = ((12, 175), (240, 305), (338, 397))
BUTTON_TOP = 207
BUTTON_BOTTOM = 230


def word_inside_control(word, origin, horizontal_area):
    left, top = origin
    start, end = horizontal_area
    x, y, width, height = (int(word[key]) for key in ("left", "top", "width", "height"))
    return all(
        (
            width > 0,
            height > 0,
            left + start <= x,
            x + width <= left + end,
            top + BUTTON_TOP <= y,
            y + height <= top + BUTTON_BOTTOM,
        )
    )


def verify_control_layout(region, origin):
    controls = (region[-6:-2], region[-2:-1], region[-1:])
    for words, horizontal_area in zip(controls, BUTTON_AREAS, strict=True):
        if any(
            not word_inside_control(word, origin, horizontal_area) for word in words
        ):
            raise RuntimeError(
                "Consent controls did not match the native button layout"
            )
