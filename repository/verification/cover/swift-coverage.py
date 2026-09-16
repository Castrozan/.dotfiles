import json
import os
from pathlib import Path
import subprocess
import tempfile


REPOSITORY = Path(__file__).resolve().parents[3]
DESKTOP = Path("machine-configuration/desktop")
SWITCHER = DESKTOP / "window-management/workspace-window-switcher"
LAUNCHER = DESKTOP / "applications/launcher"
AMBIENT = DESKTOP / "appearance/screensaver/ambient-canvas"


def compile_test_binary(source_directory, entry_point, test_sources, binary):
    production_sources = sorted(
        path
        for path in (REPOSITORY / source_directory).rglob("*.swift")
        if path.name not in {entry_point, "Package.swift"}
        and "__tests__" not in path.parts
    )
    subprocess.run(
        [
            "xcrun",
            "swiftc",
            "-profile-generate",
            "-profile-coverage-mapping",
            "-o",
            str(binary),
            *map(str, production_sources),
            *map(str, test_sources),
        ],
        check=True,
        timeout=180,
    )


def collect_coverage(output_directory):
    output_directory.mkdir(parents=True, exist_ok=True)
    suites = [
        (SWITCHER, "main.swift", "swift-sources/__tests__", ()),
        (LAUNCHER, "daemon-entry-point.swift", "swift-sources/__tests__", ()),
        (AMBIENT, "ambient-canvas-player-main.swift", "__tests__/unit", ()),
        (AMBIENT, "ambient-canvas-player-main.swift", "__tests__/integration", (1, 2)),
    ]
    with tempfile.TemporaryDirectory(prefix="dotfiles-swift-coverage-") as temporary:
        directory = Path(temporary)
        environment = dict(
            os.environ, LLVM_PROFILE_FILE=str(directory / "%m-%p.profraw")
        )
        binaries = []
        for index, (owner, entry_point, test_directory, segment_counts) in enumerate(
            suites
        ):
            binary = directory / f"suite-{index}"
            test_sources = sorted(
                (REPOSITORY / owner / test_directory).rglob("*.swift")
            )
            if not test_sources:
                raise ValueError(f"No Swift tests found: {owner / test_directory}")
            compile_test_binary(
                owner / "swift-sources", entry_point, test_sources, binary
            )
            binaries.append(binary)
            for segment_count in segment_counts or (None,):
                arguments = []
                if segment_count is not None:
                    manifest = directory / "loop.segments.json"
                    manifest.write_text(
                        json.dumps(
                            {
                                "segments": [
                                    {
                                        "file": f"segment-{number}.mp4",
                                        "durationSeconds": 30,
                                    }
                                    for number in range(segment_count)
                                ]
                            }
                        )
                    )
                    arguments.append(str(manifest))
                subprocess.run(
                    [str(binary), *arguments], env=environment, check=True, timeout=30
                )
        profile = directory / "coverage.profdata"
        subprocess.run(
            [
                "xcrun",
                "llvm-profdata",
                "merge",
                "-sparse",
                *map(str, directory.glob("*.profraw")),
                "-o",
                str(profile),
            ],
            check=True,
            timeout=60,
        )
        objects = [
            argument for binary in binaries[1:] for argument in ("-object", str(binary))
        ]
        command = [
            "xcrun",
            "llvm-cov",
            "show",
            str(binaries[0]),
            *objects,
            f"-instr-profile={profile}",
            "-use-color=0",
        ]
        report = subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=60
        ).stdout
        report = "\n".join(
            line.removeprefix(str(REPOSITORY) + "/")
            if line.endswith(".swift:")
            else line
            for line in report.splitlines()
        )
        (output_directory / "swift-coverage.txt").write_text(report + "\n")
        subprocess.run(
            [
                "xcrun",
                "llvm-cov",
                "report",
                str(binaries[0]),
                *objects,
                f"-instr-profile={profile}",
            ],
            check=True,
            timeout=60,
        )


if __name__ == "__main__":
    collect_coverage(REPOSITORY / ".sonar-reports")
