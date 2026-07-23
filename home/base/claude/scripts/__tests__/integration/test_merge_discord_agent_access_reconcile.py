import json
import stat

import merge_discord_agent_access


class TestReconcileDirectMessageAllowlist:
    def test_creates_default_shaped_file_when_absent(self, tmp_path):
        state_directory = tmp_path / "jenny"
        state_directory.mkdir()
        merge_discord_agent_access.reconcile_direct_message_allowlist(
            str(state_directory), "allowlist", ["123456789012345678"]
        )
        document = json.loads((state_directory / "access.json").read_text())
        assert document["dmPolicy"] == "allowlist"
        assert document["allowFrom"] == ["123456789012345678"]
        assert document["groups"] == {}
        assert document["pending"] == {}

    def test_writes_owner_only_permissions(self, tmp_path):
        state_directory = tmp_path / "jenny"
        state_directory.mkdir()
        merge_discord_agent_access.reconcile_direct_message_allowlist(
            str(state_directory), "allowlist", ["123456789012345678"]
        )
        mode = stat.S_IMODE((state_directory / "access.json").stat().st_mode)
        assert mode == 0o600

    def test_preserves_guild_channel_groups_from_channel_adapter(self, tmp_path):
        state_directory = tmp_path / "monster"
        state_directory.mkdir()
        (state_directory / "access.json").write_text(
            json.dumps(
                {
                    "dmPolicy": "pairing",
                    "allowFrom": [],
                    "groups": {
                        "640612380338028606": {"requireMention": False, "allowFrom": []}
                    },
                    "pending": {},
                }
            )
        )
        merge_discord_agent_access.reconcile_direct_message_allowlist(
            str(state_directory), "allowlist", ["123456789012345678"]
        )
        document = json.loads((state_directory / "access.json").read_text())
        assert document["groups"] == {
            "640612380338028606": {"requireMention": False, "allowFrom": []}
        }
        assert document["allowFrom"] == ["123456789012345678"]

    def test_recovers_from_corrupt_access_file(self, tmp_path):
        state_directory = tmp_path / "jenny"
        state_directory.mkdir()
        (state_directory / "access.json").write_text("{ truncated")
        merge_discord_agent_access.reconcile_direct_message_allowlist(
            str(state_directory), "allowlist", ["123456789012345678"]
        )
        document = json.loads((state_directory / "access.json").read_text())
        assert document["dmPolicy"] == "allowlist"
        assert document["allowFrom"] == ["123456789012345678"]
