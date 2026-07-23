import json

import account_label_anonymizer

SAMPLE_ACCOUNT_UUID = "11111111-2222-3333-4444-555555555555"


class TestDeriveOpaqueLabels:
    def test_account_label_is_stable_for_same_uuid(self):
        first = account_label_anonymizer.derive_account_label(SAMPLE_ACCOUNT_UUID)
        second = account_label_anonymizer.derive_account_label(SAMPLE_ACCOUNT_UUID)
        assert first == second

    def test_account_label_has_fixed_opaque_length(self):
        label = account_label_anonymizer.derive_account_label(SAMPLE_ACCOUNT_UUID)
        assert len(label) == account_label_anonymizer.OPAQUE_LABEL_LENGTH

    def test_account_label_does_not_contain_raw_identifier(self):
        label = account_label_anonymizer.derive_account_label(SAMPLE_ACCOUNT_UUID)
        assert SAMPLE_ACCOUNT_UUID not in label
        assert "5555" not in label

    def test_distinct_accounts_get_distinct_labels(self):
        first = account_label_anonymizer.derive_account_label(SAMPLE_ACCOUNT_UUID)
        second = account_label_anonymizer.derive_account_label(
            "99999999-8888-7777-6666-555555555555"
        )
        assert first != second

    def test_account_and_machine_namespaces_do_not_collide(self):
        same_identifier = "shared-identifier"
        account_label = account_label_anonymizer.derive_account_label(same_identifier)
        machine_label = account_label_anonymizer.derive_machine_label(same_identifier)
        assert account_label != machine_label


class TestReadCurrentAccountUuid:
    def test_missing_config_returns_none(self, tmp_path):
        assert (
            account_label_anonymizer.read_current_account_uuid(tmp_path / "absent.json")
            is None
        )

    def test_corrupt_config_returns_none(self, tmp_path):
        corrupt_path = tmp_path / ".claude.json"
        corrupt_path.write_text("{not json")
        assert account_label_anonymizer.read_current_account_uuid(corrupt_path) is None

    def test_config_without_oauth_account_returns_none(self, tmp_path):
        config_path = tmp_path / ".claude.json"
        config_path.write_text(json.dumps({"userID": "abc"}))
        assert account_label_anonymizer.read_current_account_uuid(config_path) is None

    def test_account_uuid_is_extracted(self, tmp_path):
        config_path = tmp_path / ".claude.json"
        config_path.write_text(
            json.dumps({"oauthAccount": {"accountUuid": SAMPLE_ACCOUNT_UUID}})
        )
        assert (
            account_label_anonymizer.read_current_account_uuid(config_path)
            == SAMPLE_ACCOUNT_UUID
        )
