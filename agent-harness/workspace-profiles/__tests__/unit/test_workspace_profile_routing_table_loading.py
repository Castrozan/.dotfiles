import json

from workspace_profile_routing.routing_table_loading import (
    load_routing_table,
    parse_routing_table,
)


def test_parse_routing_table_reads_every_declared_selector():
    profiles = parse_routing_table(
        json.dumps(
            {
                "profiles": [
                    {
                        "name": "work",
                        "directoryPrefixes": ["~/repo"],
                        "gitRemotePatterns": ["gitlab.example.com"],
                    }
                ]
            }
        )
    )

    assert profiles[0].name == "work"
    assert profiles[0].directory_prefixes == ("~/repo",)
    assert profiles[0].git_remote_patterns == ("gitlab.example.com",)


def test_parse_routing_table_defaults_absent_selectors_to_empty():
    profiles = parse_routing_table(json.dumps({"profiles": [{"name": "work"}]}))

    assert profiles[0].directory_prefixes == ()
    assert profiles[0].git_remote_patterns == ()


def test_load_routing_table_returns_no_profiles_when_the_table_is_absent(tmp_path):
    assert load_routing_table(tmp_path / "missing-routing-table.json") == ()
    assert load_routing_table(None) == ()


def test_load_routing_table_reads_a_table_written_to_disk(tmp_path):
    routing_table_path = tmp_path / "routing-table.json"
    routing_table_path.write_text(
        json.dumps({"profiles": [{"name": "work", "directoryPrefixes": ["~/repo"]}]}),
        encoding="utf-8",
    )

    assert load_routing_table(routing_table_path)[0].name == "work"
