import json

from a2a_server.agent_card import build_agent_card_from_environment


class TestBuildAgentCardFromEnvironment:
    def test_includes_required_top_level_fields(self):
        card = build_agent_card_from_environment(
            agent_name="silver",
            description="discord agent silver",
            endpoint_url="http://127.0.0.1:7001",
        )
        payload = card.to_json_serializable_dict()
        assert payload["name"] == "silver"
        assert payload["description"] == "discord agent silver"
        assert payload["url"] == "http://127.0.0.1:7001"
        assert payload["version"] == "0.1.0"
        assert payload["defaultInputModes"] == ["text"]
        assert payload["defaultOutputModes"] == ["text"]
        assert payload["capabilities"] == []

    def test_serializes_provided_capabilities(self):
        card = build_agent_card_from_environment(
            agent_name="silver",
            description="d",
            endpoint_url="http://x",
            capability_specifications=(
                ("validate", "Validate Lancamentos", "Per-record validation"),
                ("aggregate", "CON Rubric Family", "Cross-DB aggregate validation"),
            ),
        )
        capability_payload = card.to_json_serializable_dict()["capabilities"]
        assert len(capability_payload) == 2
        assert capability_payload[0]["id"] == "validate"
        assert capability_payload[1]["name"] == "CON Rubric Family"

    def test_serialize_to_json_bytes_returns_parseable_json(self):
        card = build_agent_card_from_environment(
            agent_name="silver",
            description="d",
            endpoint_url="http://x",
        )
        parsed = json.loads(card.serialize_to_json_bytes())
        assert parsed["name"] == "silver"
