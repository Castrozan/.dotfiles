import json

from agent_api.inventory import INVENTORY_VARIABLE, hosts


def test_inventory_host_named_self_gets_local_transport_and_every_other_host_gets_ssh(
    tmp_path, monkeypatch
):
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps(
            {
                "self": "kira",
                "hosts": [
                    {"name": "kira", "trust": "owned"},
                    {"name": "alpha", "trust": "owned"},
                    {"name": "beta", "trust": "rented", "ssh_alias": "beta-alias"},
                ],
            }
        )
    )
    monkeypatch.setenv(INVENTORY_VARIABLE, str(inventory))
    assert {entry["name"]: entry["transport"] for entry in hosts()} == {
        "local": "local",
        "kira": "local",
        "alpha": "ssh",
        "beta": "ssh",
    }
    assert [entry["ssh_alias"] for entry in hosts()[2:]] == ["alpha", "beta-alias"]
