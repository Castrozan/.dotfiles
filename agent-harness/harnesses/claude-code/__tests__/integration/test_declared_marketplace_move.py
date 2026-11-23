import json
import subprocess
import sys

from reconcile_declared_marketplace_sources import main

OLD_SOURCE = {
    "source": "git",
    "url": "https://old.example/repo.git",
    "ref": "marketplace",
}
NEW_SOURCE = {
    "source": "git",
    "url": "https://new.example/repo.git",
    "ref": "marketplace",
}


def git_repository_with_origin(path, origin_url):
    subprocess.run(["git", "init", "-q", str(path)], check=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(path), "remote", "add", "origin", origin_url],
        check=True,
        timeout=30,
    )
    return path


def origin_url_of(path):
    return subprocess.run(
        ["git", "-C", str(path), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.strip()


def write_json(path, content):
    path.write_text(json.dumps(content))
    return path


def test_a_stale_marketplace_moves_to_its_declared_source_and_nothing_else_changes(
    tmp_path, monkeypatch
):
    clone_path = git_repository_with_origin(tmp_path / "clone", OLD_SOURCE["url"])
    working_repository = git_repository_with_origin(
        tmp_path / "working", "https://mine.example/repo.git"
    )
    monkeypatch.chdir(working_repository)
    known_marketplaces_path = write_json(
        tmp_path / "known_marketplaces.json",
        {
            "betha-agent-marketplace": {
                "source": OLD_SOURCE,
                "installLocation": str(clone_path),
            },
            "dotagents": {"source": OLD_SOURCE},
        },
    )
    user_settings_path = write_json(
        tmp_path / "settings.json",
        {
            "model": "opus",
            "extraKnownMarketplaces": {
                "betha-agent-marketplace": {"source": OLD_SOURCE}
            },
        },
    )
    overlay_path = write_json(
        tmp_path / "overlay.json",
        {
            "extraKnownMarketplaces": {
                "betha-agent-marketplace": {"source": NEW_SOURCE},
                "dotagents": {"source": NEW_SOURCE},
            }
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reconcile",
            str(known_marketplaces_path),
            str(user_settings_path),
            str(overlay_path),
        ],
    )

    assert main() == 0

    assert json.loads(known_marketplaces_path.read_text()) == {
        "betha-agent-marketplace": {
            "source": NEW_SOURCE,
            "installLocation": str(clone_path),
        },
        "dotagents": {"source": NEW_SOURCE},
    }
    assert json.loads(user_settings_path.read_text()) == {
        "model": "opus",
        "extraKnownMarketplaces": {"betha-agent-marketplace": {"source": NEW_SOURCE}},
    }
    assert origin_url_of(clone_path) == NEW_SOURCE["url"]
    assert origin_url_of(working_repository) == "https://mine.example/repo.git"
