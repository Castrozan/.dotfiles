import merge_discord_agent_access


class TestDefaultAccessDocument:
    def test_defaults_to_pairing_with_empty_collections(self):
        document = merge_discord_agent_access.default_access_document()
        assert document == {
            "dmPolicy": "pairing",
            "allowFrom": [],
            "groups": {},
            "pending": {},
        }


class TestApplyDirectMessageAllowlist:
    def test_overwrites_dm_policy_and_allow_from(self):
        document = {"dmPolicy": "pairing", "allowFrom": [], "groups": {}, "pending": {}}
        merge_discord_agent_access.apply_direct_message_allowlist(
            document, "allowlist", ["284143065877184512"]
        )
        assert document["dmPolicy"] == "allowlist"
        assert document["allowFrom"] == ["284143065877184512"]

    def test_preserves_existing_groups_and_pending(self):
        document = {
            "dmPolicy": "pairing",
            "allowFrom": [],
            "groups": {"111": {"requireMention": False, "allowFrom": []}},
            "pending": {"abc": {"senderId": "222"}},
        }
        merge_discord_agent_access.apply_direct_message_allowlist(
            document, "allowlist", ["284143065877184512"]
        )
        assert document["groups"] == {"111": {"requireMention": False, "allowFrom": []}}
        assert document["pending"] == {"abc": {"senderId": "222"}}

    def test_backfills_missing_groups_and_pending(self):
        document = {"dmPolicy": "pairing", "allowFrom": []}
        merge_discord_agent_access.apply_direct_message_allowlist(
            document, "allowlist", []
        )
        assert document["groups"] == {}
        assert document["pending"] == {}
