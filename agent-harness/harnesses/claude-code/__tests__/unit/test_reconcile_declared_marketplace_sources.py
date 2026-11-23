import copy
import json
import subprocess
import sys

from hypothesis import given
from hypothesis import strategies as st

from reconcile_declared_marketplace_sources import main, rewrite_differing_sources

marketplace_names = st.sampled_from(
    ["betha-agent-marketplace", "dotagents", "avatar", "other"]
)
git_sources = st.builds(
    lambda url: {"source": "git", "url": url, "ref": "marketplace"},
    st.sampled_from(["https://old.example/repo.git", "https://new.example/repo.git"]),
)
marketplace_records = st.dictionaries(
    marketplace_names,
    st.builds(
        lambda source: {"source": source, "installLocation": "/somewhere"}, git_sources
    ),
)
declared_sources = st.dictionaries(marketplace_names, git_sources)


@given(marketplace_records, declared_sources)
def test_declared_records_end_with_the_declared_source_and_nothing_else_changes(
    records, declared
):
    original_records = copy.deepcopy(records)
    rewritten_names = rewrite_differing_sources(records, declared)
    assert set(records) == set(original_records)
    for marketplace_name, record in records.items():
        original_record = original_records[marketplace_name]
        if marketplace_name in declared:
            assert record["source"] == declared[marketplace_name]
        else:
            assert record == original_record
        assert record["installLocation"] == original_record["installLocation"]
        assert (marketplace_name in rewritten_names) == (record != original_record)


def write_json(path, content):
    path.write_text(json.dumps(content))
    return path


def test_moves_the_stale_source_in_both_files_and_keeps_the_rest(
    tmp_path, monkeypatch, capsys
):
    old_source = {
        "source": "git",
        "url": "https://old.example/repo.git",
        "ref": "marketplace",
    }
    new_source = {
        "source": "git",
        "url": "https://new.example/repo.git",
        "ref": "marketplace",
    }
    known_marketplaces_path = write_json(
        tmp_path / "known_marketplaces.json",
        {
            "betha-agent-marketplace": {
                "source": old_source,
                "installLocation": "/clone",
            }
        },
    )
    user_settings_path = write_json(
        tmp_path / "settings.json",
        {
            "model": "opus",
            "extraKnownMarketplaces": {
                "betha-agent-marketplace": {"source": old_source}
            },
        },
    )
    overlay_path = write_json(
        tmp_path / "overlay.json",
        {"extraKnownMarketplaces": {"betha-agent-marketplace": {"source": new_source}}},
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
        "betha-agent-marketplace": {"source": new_source, "installLocation": "/clone"}
    }
    assert json.loads(user_settings_path.read_text()) == {
        "model": "opus",
        "extraKnownMarketplaces": {"betha-agent-marketplace": {"source": new_source}},
    }
    assert capsys.readouterr().out.count("source moved") == 2


def test_leaves_files_untouched_when_sources_already_match(tmp_path, monkeypatch):
    source = {
        "source": "git",
        "url": "https://new.example/repo.git",
        "ref": "marketplace",
    }
    known_marketplaces_text = json.dumps(
        {"betha-agent-marketplace": {"source": source}}
    )
    known_marketplaces_path = tmp_path / "known_marketplaces.json"
    known_marketplaces_path.write_text(known_marketplaces_text)
    overlay_path = write_json(
        tmp_path / "overlay.json",
        {"extraKnownMarketplaces": {"betha-agent-marketplace": {"source": source}}},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "reconcile",
            str(known_marketplaces_path),
            str(tmp_path / "absent-settings.json"),
            str(overlay_path),
        ],
    )

    assert main() == 0

    assert known_marketplaces_path.read_text() == known_marketplaces_text


def test_points_the_clone_origin_at_the_declared_url_once(tmp_path, monkeypatch, capsys):
    clone_path = tmp_path / "clone"
    subprocess.run(["git", "init", "-q", str(clone_path)], check=True)
    subprocess.run(
        ["git", "-C", str(clone_path), "remote", "add", "origin", "https://old.example/repo.git"],
        check=True,
    )
    new_source = {"source": "git", "url": "https://new.example/repo.git", "ref": "marketplace"}
    known_marketplaces_path = write_json(
        tmp_path / "known_marketplaces.json",
        {"betha-agent-marketplace": {"source": new_source, "installLocation": str(clone_path)}},
    )
    overlay_path = write_json(
        tmp_path / "overlay.json",
        {"extraKnownMarketplaces": {"betha-agent-marketplace": {"source": new_source}}},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["reconcile", str(known_marketplaces_path), str(tmp_path / "absent-settings.json"), str(overlay_path)],
    )

    assert main() == 0
    assert main() == 0

    origin_url = subprocess.run(
        ["git", "-C", str(clone_path), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert origin_url == "https://new.example/repo.git"
    assert capsys.readouterr().out.count("clone origin moved") == 1
