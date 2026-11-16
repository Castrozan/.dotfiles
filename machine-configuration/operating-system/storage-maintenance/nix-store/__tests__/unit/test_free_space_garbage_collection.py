from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

from hypothesis import given
from hypothesis import strategies as st

import free_space_garbage_collection as collection

GIBIBYTE = collection.GIBIBYTE
THRESHOLDS = collection.Thresholds(40 * GIBIBYTE, 80 * GIBIBYTE)
byte_counts = st.integers(min_value=0, max_value=500 * GIBIBYTE)


@given(free_bytes=byte_counts, previous=st.none() | byte_counts)
def test_never_collects_at_or_above_the_minimum(free_bytes, previous):
    decision = collection.decide(
        max(free_bytes, THRESHOLDS.minimum_free_bytes), THRESHOLDS, previous
    )
    assert not decision.collect


@given(free_bytes=st.integers(min_value=0, max_value=40 * GIBIBYTE - 1))
def test_collects_below_the_minimum_up_to_the_target(free_bytes):
    decision = collection.decide(free_bytes, THRESHOLDS, None)
    assert decision.collect
    assert free_bytes + decision.bytes_to_free == THRESHOLDS.target_free_bytes


@given(
    previous=st.integers(min_value=GIBIBYTE, max_value=40 * GIBIBYTE - 1),
    drop=st.integers(min_value=0, max_value=40 * GIBIBYTE),
)
def test_repeats_only_after_free_space_falls_a_gibibyte_below_the_previous_run(
    previous, drop
):
    free_bytes = max(previous - drop, 0)
    decision = collection.decide(free_bytes, THRESHOLDS, previous)
    assert decision.collect == (free_bytes <= previous - GIBIBYTE)


def make_profile(directory: Path, name: str, generations: list[int]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for generation in generations:
        (directory / f"{name}-{generation}-link").symlink_to("/nix/store/missing")
    (directory / name).symlink_to(f"{name}-{generations[-1]}-link")


def test_discovers_profiles_that_own_generation_links(tmp_path):
    profiles = tmp_path / "profiles"
    make_profile(profiles, "system", [1, 2])
    make_profile(profiles, "home-manager", [7])
    (profiles / "default").symlink_to("/nix/var/nix/profiles/per-user/root/profile")
    (profiles / "orphan-3-link").symlink_to("/nix/store/missing")

    assert collection.discover_profiles([profiles, tmp_path / "absent"]) == [
        profiles / "home-manager",
        profiles / "system",
    ]


def test_profile_directories_cover_system_and_every_home(tmp_path):
    (tmp_path / "alice").mkdir()
    (tmp_path / "bob").mkdir()

    directories = collection.profile_directories(tmp_path)

    assert Path("/nix/var/nix/profiles") in directories
    assert tmp_path / "alice/.local/state/nix/profiles" in directories
    assert tmp_path / "bob/.local/state/nix/profiles" in directories


def run_with_free_space(tmp_path, free_values, dry_run=False, previous=None):
    state_file = tmp_path / "state" / "free"
    if previous is not None:
        state_file.parent.mkdir(parents=True)
        state_file.write_text(f"{previous}\n")
    arguments = SimpleNamespace(
        minimum_free_bytes=THRESHOLDS.minimum_free_bytes,
        target_free_bytes=THRESHOLDS.target_free_bytes,
        kept_generations=5,
        state_file=state_file,
        store_path=tmp_path,
        home_root=tmp_path / "home",
        dry_run=dry_run,
    )
    usages = iter(SimpleNamespace(free=free) for free in free_values)
    with (
        patch.object(
            collection.shutil, "disk_usage", side_effect=lambda _: next(usages)
        ),
        patch.object(collection, "discover_profiles", return_value=[Path("/p/system")]),
        patch.object(collection.subprocess, "run") as run,
    ):
        collection.run(arguments)
    return run, state_file


def test_prunes_generations_before_collecting_and_records_free_space(tmp_path):
    run, state_file = run_with_free_space(tmp_path, [30 * GIBIBYTE, 70 * GIBIBYTE])

    assert run.call_args_list == [
        call(
            ["nix-env", "--profile", "/p/system", "--delete-generations", "+5"],
            check=True,
        ),
        call(["nix-store", "--gc", "--max-freed", str(50 * GIBIBYTE)], check=True),
    ]
    assert state_file.read_text() == f"{70 * GIBIBYTE}\n"


def test_dry_run_neither_deletes_nor_collects(tmp_path):
    run, state_file = run_with_free_space(tmp_path, [30 * GIBIBYTE], dry_run=True)

    assert run.call_args_list == [
        call(
            [
                "nix-env",
                "--profile",
                "/p/system",
                "--delete-generations",
                "+5",
                "--dry-run",
            ],
            check=True,
        )
    ]
    assert not state_file.exists()


def test_recovered_free_space_clears_the_previous_collection_marker(tmp_path):
    run, state_file = run_with_free_space(
        tmp_path, [60 * GIBIBYTE], previous=30 * GIBIBYTE
    )

    run.assert_not_called()
    assert not state_file.exists()
