import pathlib
import re

import scene_source_digests

AMBIENT_CANVAS_WEB_DIRECTORY = pathlib.Path(__file__).resolve().parents[2] / "web"
PALETTE_RELATIVE_PATH = "ambient_canvas_palette.js"
PALETTE_GLOBAL_NAME = "AmbientCanvasPalette"
PALETTE_SOURCE = (AMBIENT_CANVAS_WEB_DIRECTORY / PALETTE_RELATIVE_PATH).read_text()
DOCUMENT_SOURCE = (AMBIENT_CANVAS_WEB_DIRECTORY / "index.html").read_text()
COMPOSITOR_SOURCE = (
    AMBIENT_CANVAS_WEB_DIRECTORY / "record" / "ambient-canvas-recording-compositor.js"
).read_text()
FINGERPRINT_SOURCE = (
    AMBIENT_CANVAS_WEB_DIRECTORY / "record" / "ambient-canvas-recording-fingerprint.js"
).read_text()
RECORDER_SOURCE = (AMBIENT_CANVAS_WEB_DIRECTORY / "recorder.js").read_text()
PLAYLIST_PATH = AMBIENT_CANVAS_WEB_DIRECTORY / "panes.js"
SCENES_DIRECTORY = AMBIENT_CANVAS_WEB_DIRECTORY / "scenes"
AUTHORING_SOURCES = {
    path: path.read_text()
    for path in sorted(SCENES_DIRECTORY.glob("**/*.js")) + [PLAYLIST_PATH]
}
DARK_COLOUR_LUMINANCE_CEILING = 96
SCENE_REGISTRATION_PATTERN = re.compile(
    r"AMBIENT_CANVAS_SCENE_FACTORIES\[\s*\"([^\"]+)\"\s*\]\s*="
)
SCRIPT_REFERENCE_PATTERN = re.compile(r"<script src=\"([^\"]+)\"></script>")
DOCUMENT_BACKGROUND_PATTERN = re.compile(
    r"--ambient-canvas-background:\s*(#[0-9a-fA-F]{6});"
)
PALETTE_BACKGROUND_PATTERN = re.compile(
    r"DEFAULT_BACKGROUND_HEX = \"(#[0-9a-fA-F]{6})\""
)
HEX_COLOUR_PATTERN = re.compile(r"#([0-9a-fA-F]{6})\b")
QUOTED_STRING_PATTERN = re.compile(r"\"([^\"\n]*)\"|'([^'\n]*)'")
CHANNEL_TRIPLE_PATTERN = re.compile(
    r"(?<![\d.\-])(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(?![\d.])"
)
OPAQUE_FRAGMENT_COLOUR_PATTERN = re.compile(
    r"gl_FragColor\s*=\s*vec4\(\s*"
    r"([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\)"
)


def rec601_luminance(red, green, blue):
    return 0.299 * red + 0.587 * green + 0.114 * blue


def is_darker_than_a_foreground_colour(channels):
    return rec601_luminance(*channels) < DARK_COLOUR_LUMINANCE_CEILING


def hex_colour_channels(hexadecimal_digits):
    return [int(hexadecimal_digits[offset : offset + 2], 16) for offset in (0, 2, 4)]


def dark_hex_literals(source_text):
    return [
        "#" + hexadecimal_digits
        for hexadecimal_digits in HEX_COLOUR_PATTERN.findall(source_text)
        if is_darker_than_a_foreground_colour(hex_colour_channels(hexadecimal_digits))
    ]


def dark_channel_triple_literals(source_text):
    offenders = []
    for double_quoted, single_quoted in QUOTED_STRING_PATTERN.findall(source_text):
        quoted_text = double_quoted or single_quoted
        for triple in CHANNEL_TRIPLE_PATTERN.findall(quoted_text):
            channels = [int(channel) for channel in triple]
            if max(channels) > 255:
                continue
            if is_darker_than_a_foreground_colour(channels):
                offenders.append("rgb(" + ", ".join(triple) + ")")
    return offenders


def dark_opaque_fragment_colours(source_text):
    offenders = []
    for fragment_colour in OPAQUE_FRAGMENT_COLOUR_PATTERN.findall(source_text):
        if float(fragment_colour[3]) < 1.0:
            continue
        channels = [float(channel) * 255 for channel in fragment_colour[:3]]
        if is_darker_than_a_foreground_colour(channels):
            offenders.append("gl_FragColor = vec4(" + ", ".join(fragment_colour) + ")")
    return offenders


def dark_colour_literals(source_text):
    return (
        dark_hex_literals(source_text)
        + dark_channel_triple_literals(source_text)
        + dark_opaque_fragment_colours(source_text)
    )


def scene_names_to_source_paths():
    scene_source_paths = {}
    for path, source in AUTHORING_SOURCES.items():
        for scene_name in SCENE_REGISTRATION_PATTERN.findall(source):
            if path.parent == SCENES_DIRECTORY:
                scene_source_paths[scene_name] = [path]
            else:
                scene_source_paths[scene_name] = sorted(path.parent.glob("*.js"))
    return scene_source_paths


def palette_background_hex():
    return PALETTE_BACKGROUND_PATTERN.search(PALETTE_SOURCE).group(1)


def test_the_palette_declares_a_single_background_colour():
    assert palette_background_hex()


def test_the_document_loads_the_palette_before_every_scene_script():
    script_references = SCRIPT_REFERENCE_PATTERN.findall(DOCUMENT_SOURCE)
    assert PALETTE_RELATIVE_PATH in script_references, (
        "index.html never loads the palette, so every scene reads it as undefined"
    )
    first_scene_position = min(
        position
        for position, reference in enumerate(script_references)
        if reference.startswith("scenes/")
    )
    assert script_references.index(PALETTE_RELATIVE_PATH) < first_scene_position


def test_the_document_background_matches_the_palette_background():
    document_backgrounds = set(DOCUMENT_BACKGROUND_PATTERN.findall(DOCUMENT_SOURCE))
    assert document_backgrounds == {palette_background_hex()}, (
        f"index.html backgrounds {sorted(document_backgrounds)} "
        f"drifted from the palette {palette_background_hex()}"
    )


def test_the_palette_applies_the_theme_background_query_parameter():
    assert "URLSearchParams" in PALETTE_SOURCE
    assert '"themeBackground"' in PALETTE_SOURCE
    assert re.search(
        r'setProperty\(\s*"--ambient-canvas-background",\s*backgroundHex,\s*\)',
        PALETTE_SOURCE,
    )


def test_no_authoring_source_declares_a_dark_colour_literal():
    offenders = {
        str(path.relative_to(AMBIENT_CANVAS_WEB_DIRECTORY)): found
        for path, source in AUTHORING_SOURCES.items()
        if (found := dark_colour_literals(source))
    }
    assert not offenders, (
        f"backgrounds must come from {PALETTE_GLOBAL_NAME}, not literals: {offenders}"
    )


def test_every_scene_sources_its_colours_from_the_palette():
    offenders = sorted(
        scene_name
        for scene_name, source_paths in scene_names_to_source_paths().items()
        if not any(PALETTE_GLOBAL_NAME in path.read_text() for path in source_paths)
    )
    assert not offenders, (
        f"scenes that never reference {PALETTE_GLOBAL_NAME}: {offenders}"
    )


def test_the_recording_compositor_fills_from_the_palette():
    assert PALETTE_GLOBAL_NAME in COMPOSITOR_SOURCE
    assert not dark_colour_literals(COMPOSITOR_SOURCE)


def test_editing_the_palette_re_records_every_segment(tmp_path):
    for relative_path in scene_source_digests.RECORDING_PIPELINE_RELATIVE_PATHS:
        pipeline_file = tmp_path / relative_path
        pipeline_file.parent.mkdir(parents=True, exist_ok=True)
        pipeline_file.write_text("pipeline\n")
    before_edit = scene_source_digests.build_recording_pipeline_digest(str(tmp_path))
    (tmp_path / PALETTE_RELATIVE_PATH).write_text("a retuned palette\n")
    assert (
        scene_source_digests.build_recording_pipeline_digest(str(tmp_path))
        != before_edit
    ), "a palette edit must change the pipeline digest or every segment stays stale"


def test_the_theme_background_participates_in_every_segment_fingerprint():
    assert 'recordParameters.get("themeBackground")' in RECORDER_SOURCE
    assert "themeBackgroundHex" in FINGERPRINT_SOURCE
    assert "themeBackground: themeBackgroundHex" in FINGERPRINT_SOURCE
