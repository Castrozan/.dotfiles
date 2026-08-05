import pathlib
import re

AMBIENT_CANVAS_WEB_DIRECTORY = pathlib.Path(__file__).resolve().parents[2] / "web"
PLAYLIST_SOURCE = (AMBIENT_CANVAS_WEB_DIRECTORY / "panes.js").read_text()
DOCUMENT_SOURCE = (AMBIENT_CANVAS_WEB_DIRECTORY / "index.html").read_text()
SCENE_SOURCES = {
    path: path.read_text()
    for path in sorted(AMBIENT_CANVAS_WEB_DIRECTORY.glob("scenes/**/*.js"))
}


def scene_names_declared_in_the_playlist():
    return set(re.findall(r"scene:\s*\"([^\"]+)\"", PLAYLIST_SOURCE))


def scene_names_registered_by_a_factory():
    registrations = set()
    for source in SCENE_SOURCES.values():
        registrations.update(
            re.findall(
                r"AMBIENT_CANVAS_SCENE_FACTORIES\[\s*\"([^\"]+)\"\s*\]\s*=", source
            )
        )
    return registrations


def scene_scripts_loaded_by_the_document():
    return set(
        re.findall(r"<script src=\"(scenes/[^\"]+)\"></script>", DOCUMENT_SOURCE)
    )


def test_the_playlist_declares_at_least_one_scene():
    assert scene_names_declared_in_the_playlist()


def test_every_playlist_scene_has_a_registered_factory():
    missing = (
        scene_names_declared_in_the_playlist() - scene_names_registered_by_a_factory()
    )
    assert not missing, (
        f"playlist scenes with no factory registration: {sorted(missing)}"
    )


def test_every_registering_scene_file_is_loaded_by_the_document():
    loaded = scene_scripts_loaded_by_the_document()
    unloaded = sorted(
        str(path.relative_to(AMBIENT_CANVAS_WEB_DIRECTORY))
        for path, source in SCENE_SOURCES.items()
        if "AMBIENT_CANVAS_SCENE_FACTORIES[" in source
        and str(path.relative_to(AMBIENT_CANVAS_WEB_DIRECTORY)) not in loaded
    )
    assert not unloaded, f"scene files never loaded by index.html: {unloaded}"


def test_every_scene_script_tag_points_at_a_file_that_exists():
    absent = sorted(
        reference
        for reference in scene_scripts_loaded_by_the_document()
        if not (AMBIENT_CANVAS_WEB_DIRECTORY / reference).is_file()
    )
    assert not absent, f"index.html loads absent scene files: {absent}"


def test_every_webgl_scene_honours_the_recorder_drawing_buffer_override():
    offenders = sorted(
        str(path.relative_to(AMBIENT_CANVAS_WEB_DIRECTORY))
        for path, source in SCENE_SOURCES.items()
        if 'getContext("webgl"' in source and "preserveDrawingBuffer" not in source
    )
    assert not offenders, f"WebGL scenes that would record blank frames: {offenders}"
