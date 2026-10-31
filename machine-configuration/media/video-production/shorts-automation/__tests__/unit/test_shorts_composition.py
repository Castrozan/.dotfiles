import hashlib
import subprocess

import pytest

import shorts_composition


def composition_manifest(sdk_path, features='["cli", "build-portable"]'):
    return (
        '[package]\nname = "masking-crab"\n\n[dependencies]\n'
        f'fframes = {{ path = "{sdk_path}", features = {features} }}\n'
    )


@pytest.fixture
def composition_run(tmp_path, monkeypatch):
    root = tmp_path / "shorts"
    directory = root / "runs" / "slot"
    manifest = directory / "composition" / "Cargo.toml"
    manifest.parent.mkdir(parents=True)
    sdk = root / "native-kit" / "fframes" / "fframes"
    manifest.write_text(composition_manifest(sdk))
    example = root / "native-kit" / "probe"
    example.mkdir(parents=True)
    (example / "Cargo.lock").write_text("canonical lock")
    (example / "Cargo.toml").write_text(composition_manifest("../fframes/fframes"))
    target = root / "native-kit" / "target"
    monkeypatch.setenv("CARGO_TARGET_DIR", str(target))
    calls = []

    def cargo(arguments, **options):
        calls.append(arguments)
        if arguments[1] == "build":
            options["stderr"].write("Finished")
            compiled = target / "release" / "masking-crab"
            compiled.parent.mkdir(parents=True)
            compiled.write_bytes(b"composition binary")
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(shorts_composition.subprocess, "run", cargo)
    return root, directory, manifest, calls


def test_build_delivers_the_binary_and_keeps_the_shared_target_bounded(composition_run):
    root, directory, manifest, calls = composition_run
    result = shorts_composition.build_composition(
        directory, root, "composition/Cargo.toml"
    )
    assert result == {
        "binary": "bin/masking-crab",
        "sha256": hashlib.sha256(b"composition binary").hexdigest(),
    }
    assert (directory / "bin" / "masking-crab").read_bytes() == b"composition binary"
    assert manifest.with_name("Cargo.lock").read_text() == "canonical lock"
    assert (directory / "evidence" / "build.stderr").read_text() == "Finished"
    assert [call[:4] for call in calls] == [
        ["cargo", "build", "--offline", "--release"],
        ["cargo", "clean", "--offline", "--release"],
    ]
    assert calls[1][-2:] == ["--package", "masking-crab"]


def test_failed_build_reports_its_evidence_and_delivers_nothing(
    composition_run, monkeypatch
):
    root, directory, manifest, calls = composition_run

    def failing_cargo(arguments, **options):
        calls.append(arguments)
        return subprocess.CompletedProcess(arguments, 101)

    monkeypatch.setattr(shorts_composition.subprocess, "run", failing_cargo)
    with pytest.raises(ValueError, match="evidence/build.stderr"):
        shorts_composition.build_composition(directory, root, "composition/Cargo.toml")
    assert not (directory / "bin").exists()
    assert len(calls) == 1


def test_manifest_outside_the_run_is_refused(composition_run):
    root, directory, manifest, calls = composition_run
    outside = root / "Cargo.toml"
    outside.write_text('[package]\nname = "elsewhere"\n')
    with pytest.raises(ValueError, match="inside the current run"):
        shorts_composition.build_composition(directory, root, outside)
    assert calls == []


def test_an_sdk_linked_into_the_run_is_refused_before_it_recompiles(composition_run):
    root, directory, manifest, calls = composition_run
    (directory / "fframes").symlink_to(root / "native-kit" / "fframes")
    manifest.write_text(composition_manifest("../fframes/fframes"))
    with pytest.raises(ValueError, match="shared SDK"):
        shorts_composition.build_composition(directory, root, "composition/Cargo.toml")
    assert calls == []


def test_a_different_sdk_feature_set_is_refused_before_it_recompiles(composition_run):
    root, directory, manifest, calls = composition_run
    sdk = root / "native-kit" / "fframes" / "fframes"
    manifest.write_text(composition_manifest(sdk, features='["cli"]'))
    with pytest.raises(ValueError, match="shared SDK"):
        shorts_composition.build_composition(directory, root, "composition/Cargo.toml")
    assert calls == []


def test_a_composition_without_the_sdk_is_refused(composition_run):
    root, directory, manifest, calls = composition_run
    manifest.write_text('[package]\nname = "masking-crab"\n')
    with pytest.raises(ValueError, match="shared SDK"):
        shorts_composition.build_composition(directory, root, "composition/Cargo.toml")
    assert calls == []


def test_a_kit_reached_through_a_link_still_names_the_real_sdk(
    composition_run, tmp_path
):
    root, directory, manifest, calls = composition_run
    kit = tmp_path / "kit"
    (root / "native-kit").rename(kit)
    (root / "native-kit").symlink_to(kit)
    manifest.write_text(composition_manifest(kit / "fframes" / "fframes"))
    shorts_composition.build_composition(directory, root, "composition/Cargo.toml")
    assert len(calls) == 2


def test_the_sweep_never_follows_a_link_out_of_the_run(tmp_path):
    kit = tmp_path / "native-kit"
    (kit / "target" / "release").mkdir(parents=True)
    (kit / "target" / "CACHEDIR.TAG").write_text("Signature")
    run = tmp_path / "run"
    run.mkdir()
    (run / "native-kit").symlink_to(kit)
    shorts_composition.discard_build_caches(run)
    assert (kit / "target" / "release").is_dir()


def test_build_caches_are_discarded_at_any_depth(tmp_path):
    for cache in (tmp_path / "build-cache", tmp_path / "composition" / "target"):
        (cache / "release").mkdir(parents=True)
        (cache / "CACHEDIR.TAG").write_text("Signature")
    (tmp_path / "final.mp4").write_bytes(b"video")
    (tmp_path / "composition" / "Cargo.toml").write_text("[package]")
    shorts_composition.discard_build_caches(tmp_path)
    assert not (tmp_path / "build-cache").exists()
    assert not (tmp_path / "composition" / "target").exists()
    assert (tmp_path / "final.mp4").exists()
    assert (tmp_path / "composition" / "Cargo.toml").exists()


def test_a_cache_tag_in_the_run_root_never_deletes_the_run(tmp_path):
    (tmp_path / "CACHEDIR.TAG").write_text("Signature")
    (tmp_path / "final.mp4").write_bytes(b"video")
    shorts_composition.discard_build_caches(tmp_path)
    assert (tmp_path / "final.mp4").exists()
