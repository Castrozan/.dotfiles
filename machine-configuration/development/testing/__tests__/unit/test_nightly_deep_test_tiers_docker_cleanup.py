import io
import subprocess

import nightly_deep_test_tiers as nightly


def test_prune_is_skipped_when_docker_is_absent(monkeypatch):
    calls = []
    monkeypatch.setattr(nightly.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        nightly.subprocess, "run", lambda *args, **kwargs: calls.append(args)
    )
    log = io.StringIO()

    nightly.prune_docker_build_leftovers_the_run_did_not_reuse(log)

    assert calls == []
    assert "no build cache to prune" in log.getvalue()


def test_prune_drops_build_cache_and_dangling_images_the_run_did_not_reuse(monkeypatch):
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(
            command, 0, stdout="Total:\t23.1GB\n", stderr=""
        )

    monkeypatch.setattr(nightly.shutil, "which", lambda name: "/usr/bin/docker")
    monkeypatch.setattr(nightly.subprocess, "run", fake_run)
    log = io.StringIO()

    nightly.prune_docker_build_leftovers_the_run_did_not_reuse(log)

    assert commands == [
        ["docker", "builder", "prune", "--force", "--filter", "until=24h"],
        ["docker", "image", "prune", "--force"],
    ]
    assert (
        "docker builder prune --force --filter until=24h: exit 0, Total:\t23.1GB"
        in log.getvalue()
    )


def test_the_run_prunes_docker_leftovers_after_the_tiers_and_caches(
    monkeypatch, tmp_path
):
    order = []
    monkeypatch.setattr(
        nightly, "open_log_file", lambda: (tmp_path / "run.log").open("w")
    )
    monkeypatch.setattr(nightly, "untracked_paths_in_repository", lambda: set())
    monkeypatch.setattr(
        nightly,
        "run_every_tier_reporting_all_failures",
        lambda log: order.append("tiers") or [],
    )
    monkeypatch.setattr(
        nightly,
        "remove_generated_cache_directories",
        lambda log: order.append("caches"),
    )
    monkeypatch.setattr(
        nightly,
        "prune_docker_build_leftovers_the_run_did_not_reuse",
        lambda log: order.append("docker"),
    )

    assert nightly.run_the_deep_tiers_and_clean_up() == 0
    assert order == ["tiers", "caches", "docker"]
