import os

import scene_source_digests as digests

REAL_WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "web")


def build_fake_web_directory(tmp_path):
    scenes_directory = tmp_path / "scenes"
    scenes_directory.mkdir()
    (scenes_directory / "flat.js").write_text(
        'window.AMBIENT_CANVAS_SCENE_FACTORIES["flat"] = function () {};\n'
    )
    nested_directory = scenes_directory / "nested"
    nested_directory.mkdir()
    (nested_directory / "nested.js").write_text(
        'window.AMBIENT_CANVAS_SCENE_FACTORIES["nested"] = function () {};\n'
    )
    (nested_directory / "nested_helper.js").write_text("const helper = 1;\n")
    (tmp_path / "record").mkdir()
    (tmp_path / "vendor").mkdir()
    for relative_path in digests.RECORDING_PIPELINE_RELATIVE_PATHS:
        (tmp_path / relative_path).write_text("pipeline\n")
    return tmp_path


def test_a_flat_scene_maps_to_its_own_file_alone(tmp_path):
    build_fake_web_directory(tmp_path)
    scene_source_files = digests.map_scene_names_to_source_files(str(tmp_path))
    assert scene_source_files["flat"] == [str(tmp_path / "scenes" / "flat.js")]


def test_a_nested_scene_maps_to_every_file_in_its_directory(tmp_path):
    build_fake_web_directory(tmp_path)
    scene_source_files = digests.map_scene_names_to_source_files(str(tmp_path))
    assert sorted(scene_source_files["nested"]) == [
        str(tmp_path / "scenes" / "nested" / "nested.js"),
        str(tmp_path / "scenes" / "nested" / "nested_helper.js"),
    ]


def test_editing_one_scene_leaves_the_other_digest_untouched(tmp_path):
    build_fake_web_directory(tmp_path)
    before_edit = digests.build_scene_source_digests(str(tmp_path))
    (tmp_path / "scenes" / "flat.js").write_text(
        'window.AMBIENT_CANVAS_SCENE_FACTORIES["flat"] = function () { return 1; };\n'
    )
    after_edit = digests.build_scene_source_digests(str(tmp_path))
    assert after_edit["flat"] != before_edit["flat"]
    assert after_edit["nested"] == before_edit["nested"]


def test_editing_a_nested_helper_changes_its_scene_digest(tmp_path):
    build_fake_web_directory(tmp_path)
    before_edit = digests.build_scene_source_digests(str(tmp_path))
    (tmp_path / "scenes" / "nested" / "nested_helper.js").write_text(
        "const helper = 2;\n"
    )
    after_edit = digests.build_scene_source_digests(str(tmp_path))
    assert after_edit["nested"] != before_edit["nested"]


def test_adding_a_scene_leaves_every_existing_digest_untouched(tmp_path):
    build_fake_web_directory(tmp_path)
    before_addition = digests.build_scene_source_digests(str(tmp_path))
    (tmp_path / "scenes" / "added.js").write_text(
        'window.AMBIENT_CANVAS_SCENE_FACTORIES["added"] = function () {};\n'
    )
    after_addition = digests.build_scene_source_digests(str(tmp_path))
    assert "added" in after_addition
    for scene_name, scene_digest in before_addition.items():
        assert after_addition[scene_name] == scene_digest


def test_editing_the_pipeline_changes_the_pipeline_digest(tmp_path):
    build_fake_web_directory(tmp_path)
    before_edit = digests.build_recording_pipeline_digest(str(tmp_path))
    (tmp_path / "recorder.js").write_text("changed pipeline\n")
    assert digests.build_recording_pipeline_digest(str(tmp_path)) != before_edit


def test_adding_a_scene_leaves_the_pipeline_digest_untouched(tmp_path):
    build_fake_web_directory(tmp_path)
    before_addition = digests.build_recording_pipeline_digest(str(tmp_path))
    (tmp_path / "scenes" / "added.js").write_text(
        'window.AMBIENT_CANVAS_SCENE_FACTORIES["added"] = function () {};\n'
    )
    assert digests.build_recording_pipeline_digest(str(tmp_path)) == before_addition


def test_fingerprint_inputs_carry_scenes_and_pipeline(tmp_path):
    build_fake_web_directory(tmp_path)
    fingerprint_inputs = digests.build_segment_fingerprint_inputs(str(tmp_path))
    assert sorted(fingerprint_inputs["scenes"]) == ["flat", "nested"]
    assert fingerprint_inputs["pipeline"]


def test_every_shipped_scene_resolves_to_a_digest():
    fingerprint_inputs = digests.build_segment_fingerprint_inputs(REAL_WEB_DIRECTORY)
    assert len(fingerprint_inputs["scenes"]) > 1
    assert fingerprint_inputs["pipeline"]
