import os
import shutil
import subprocess
import tomllib
from pathlib import Path

from shorts_quality import digest, inside_run


CANONICAL_LOCK = Path("native-kit/probe/Cargo.lock")


def cargo(action, manifest, *options, **streams):
    return subprocess.run(
        [
            "cargo",
            action,
            "--offline",
            "--release",
            "--manifest-path",
            str(manifest),
            *options,
        ],
        **streams,
    )


def compile_package(directory, manifest):
    evidence = directory / "evidence"
    evidence.mkdir(exist_ok=True)
    with (
        (evidence / "build.stdout").open("w") as output,
        (evidence / "build.stderr").open("w") as errors,
    ):
        build = cargo("build", manifest, stdout=output, stderr=errors)
    if build.returncode:
        raise ValueError("Composition build failed; inspect evidence/build.stderr")


def build_composition(directory, root, manifest_path):
    manifest = inside_run(directory, manifest_path)
    package = tomllib.loads(manifest.read_text())["package"]["name"]
    shutil.copyfile(root / CANONICAL_LOCK, manifest.with_name("Cargo.lock"))
    compile_package(directory, manifest)
    binary = directory / "bin" / package
    binary.parent.mkdir(exist_ok=True)
    shutil.copy2(Path(os.environ["CARGO_TARGET_DIR"]) / "release" / package, binary)
    cargo("clean", manifest, "--package", package, check=True, capture_output=True)
    return {"binary": str(binary.relative_to(directory)), "sha256": digest(binary)}


def discard_build_caches(directory):
    for marker in list(directory.glob("*/**/CACHEDIR.TAG")):
        shutil.rmtree(marker.parent, ignore_errors=True)
