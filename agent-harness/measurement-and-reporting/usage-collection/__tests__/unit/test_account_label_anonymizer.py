import json

import account_label_anonymizer

SAMPLE_ACCOUNT_UUID = "11111111-2222-3333-4444-555555555555"


class TestDeriveOpaqueLabels:
    def test_account_label_does_not_contain_raw_identifier(self):
        label = account_label_anonymizer.derive_account_label(SAMPLE_ACCOUNT_UUID)
        assert SAMPLE_ACCOUNT_UUID not in label
        assert "5555" not in label


class TestReadCurrentAccountUuid:
    def test_account_uuid_is_extracted(self, tmp_path):
        config_path = tmp_path / ".claude.json"
        config_path.write_text(
            json.dumps({"oauthAccount": {"accountUuid": SAMPLE_ACCOUNT_UUID}})
        )
        assert (
            account_label_anonymizer.read_current_account_uuid(config_path)
            == SAMPLE_ACCOUNT_UUID
        )
