import csv
import io
import re
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class DialogButton:
    position: tuple[int, int]
    bounds: tuple[int, int, int, int]


def consent_title(words):
    lines = {}
    for word in words:
        key = tuple(word[name] for name in ("block_num", "par_num", "line_num"))
        lines.setdefault(key, []).append(word)
    titles = [
        line[index : index + 3]
        for line in lines.values()
        for index in range(len(line) - 2)
        if " ".join(word["text"] for word in line[index : index + 3])
        == "Allow remote debugging?"
    ]
    if not titles:
        return None
    if len(titles) != 1:
        raise RuntimeError("Multiple consent titles found")
    return titles[0]


def warning_origin(title, size):
    left, top = int(title[0]["left"]), min(int(word["top"]) for word in title)
    width, _ = size
    if not width * 0.2 < left < width * 0.7 or not 25 < top < 90:
        raise RuntimeError("Consent title is outside the native Chrome header area")
    return left, top


def word_inside_warning(word, origin):
    left, top = origin
    return (
        left - 10 <= int(word["left"]) < left + 420
        and top <= int(word["top"]) < top + 260
    )


def verify_warning(region):
    text = re.sub(r"\s+", " ", " ".join(word["text"] for word in region))
    expected = (
        "Allow remote debugging? An external app wants full control over this Chrome "
        "session to debug it. This includes access to your saved data, cookies and site data, "
        "and the ability to navigate to any URL. Only web developers should turn on this feature, "
        "and only use it with trusted apps. Turn off in settings Cancel Allow"
    )
    if text != expected or any(float(word["conf"]) < 65 for word in region):
        raise RuntimeError(
            "Consent dialog text did not match the exact native Chrome warning"
        )


def allow_button_word(region, top):
    buttons = [
        word
        for word in region
        if word["text"] == "Allow" and int(word["top"]) > top + 150
    ]
    if len(buttons) != 1:
        raise RuntimeError("Expected one Allow button in the consent dialog")
    return buttons[0]


def button_geometry(button, origin, size):
    left, top = origin
    width, height = size
    x, y, button_width, button_height = (
        int(button[key]) for key in ("left", "top", "width", "height")
    )
    if x + button_width >= width or y + button_height >= height:
        raise RuntimeError("Consent button is outside the Chrome window")
    return DialogButton(
        (x + button_width // 2, y + button_height // 2),
        (left - 10, top - 15, left + 430, y + button_height + 20),
    )


def find_allow_button(words, size):
    title = consent_title(words)
    if title is None:
        return None
    origin = warning_origin(title, size)
    region = [word for word in words if word_inside_warning(word, origin)]
    verify_warning(region)
    return button_geometry(allow_button_word(region, origin[1]), origin, size)


def normalized_word(row, offset):
    shifts = {"left": offset[0], "top": offset[1], "width": 0, "height": 0}
    return {**row, **{key: int(row[key]) // 2 + shift for key, shift in shifts.items()}}


def recognize_words(configuration, image, path, offset=(0, 0), segmentation="6"):
    from PIL import ImageOps

    ImageOps.grayscale(image).point(lambda value: 0 if value >= 100 else 255).resize(
        (image.width * 2, image.height * 2)
    ).save(path)
    result = subprocess.run(
        [configuration["tesseract"], str(path), "stdout", "--psm", segmentation, "tsv"],
        check=True,
        capture_output=True,
        text=True,
        timeout=2,
    )
    words = [
        row
        for row in csv.DictReader(io.StringIO(result.stdout), delimiter="\t")
        if row["text"].strip()
    ]
    return [normalized_word(word, offset) for word in words]


def inspect_image(configuration, image, directory):
    words = recognize_words(
        configuration,
        image.crop((0, 0, image.width, min(400, image.height))),
        directory / "header.png",
    )
    title = consent_title(words)
    if title is None:
        return None
    left, top = warning_origin(title, image.size)
    bounds = (left - 10, top - 4, left + 430, top + 190)
    words = recognize_words(
        configuration, image.crop(bounds), directory / "body.png", bounds[:2]
    )
    for index, (start, end) in enumerate(((12, 175), (240, 305), (338, 397))):
        bounds = (left + start, top + 207, left + end, top + 230)
        words.extend(
            recognize_words(
                configuration,
                image.crop(bounds),
                directory / f"button-{index}.png",
                bounds[:2],
                "7",
            )
        )
    return find_allow_button(words, image.size)


def capture_dialog(configuration, target, directory):
    from PIL import Image

    x, y = target["at"]
    width, height = target["size"]
    path = directory / "chrome.png"
    subprocess.run(
        [configuration["grim"], "-g", f"{x},{y} {width}x{height}", str(path)],
        check=True,
        capture_output=True,
        timeout=2,
    )
    with Image.open(path) as image:
        if image.size != (width, height):
            raise RuntimeError(
                "Scaled display is unsupported; refusing coordinate ambiguity"
            )
        return inspect_image(configuration, image, directory)
