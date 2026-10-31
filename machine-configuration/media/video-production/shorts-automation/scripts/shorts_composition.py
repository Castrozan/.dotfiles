import os
import shutil
import subprocess
import tomllib
from pathlib import Path

from shorts_quality import digest, inside_run


CANONICAL_LOCK = Path("native-kit/probe/Cargo.lock")
CANONICAL_MANIFEST = Path("native-kit/probe/Cargo.toml")


def sdk_dependency(manifest):
    dependencies = tomllib.loads(manifest.read_text()).get("dependencies", {})
    dependency = dependencies.get("fframes", {})
    declared_path = manifest.parent / dependency.get("path", "")
    return {**dependency, "path": os.path.normpath(declared_path)}


def require_shared_sdk(manifest, root):
    canonical = sdk_dependency((root / CANONICAL_MANIFEST).resolve())
    if sdk_dependency(manifest) != canonical:
        raise ValueError(f"Composition must depend on the shared SDK: {canonical}")


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
    require_shared_sdk(manifest, root)
    package = tomllib.loads(manifest.read_text())["package"]["name"]
    shutil.copyfile(root / CANONICAL_LOCK, manifest.with_name("Cargo.lock"))
    compile_package(directory, manifest)
    binary = directory / "bin" / package
    binary.parent.mkdir(exist_ok=True)
    shutil.copy2(Path(os.environ["CARGO_TARGET_DIR"]) / "release" / package, binary)
    cargo("clean", manifest, "--package", package, check=True, capture_output=True)
    return {"binary": str(binary.relative_to(directory)), "sha256": digest(binary)}


def discard_build_caches(directory):
    run = directory.resolve()
    for marker in list(directory.glob("*/**/CACHEDIR.TAG")):
        if marker.resolve().is_relative_to(run):
            shutil.rmtree(marker.parent, ignore_errors=True)
