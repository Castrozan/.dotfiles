import importlib.util
import json
import pathlib

CLAWDE_SCRIPTS_DIRECTORY = pathlib.Path(__file__).resolve().parent.parent.parent


def _load_merge_discord_channel_access_module():
    module_spec = importlib.util.spec_from_file_location(
        "merge_discord_channel_access",
        CLAWDE_SCRIPTS_DIRECTORY / "merge-discord-channel-access.py",
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


merge_discord_channel_access = _load_merge_discord_channel_access_module()


def _read_json(path):
    return json.loads(pathlib.Path(path).read_text())


def _write_json(path, document):
    pathlib.Path(path).write_text(json.dumps(document))


def test_parse_channel_ids_splits_on_commas_whitespace_and_newlines():
    parsed = merge_discord_channel_access.parse_channel_ids("111, 222\n333 444")
    assert parsed == ["111", "222", "333", "444"]


def test_parse_channel_ids_ignores_non_numeric_tokens():
    parsed = merge_discord_channel_access.parse_channel_ids("111 notanid 222")
    assert parsed == ["111", "222"]


def test_migrates_from_shared_when_target_absent(tmp_path):
    shared = tmp_path / "shared.json"
    state_dir = tmp_path / "monster"
    _write_json(
        shared,
        {
            "dmPolicy": "allowlist",
            "allowFrom": ["284143065877184512"],
            "groups": {"999": {"requireMention": False, "allowFrom": []}},
            "pending": {},
        },
    )

    merge_discord_channel_access.reconcile_agent_access(
        state_directory=str(state_dir),
        shared_access_file=str(shared),
        channels_secret_file=None,
    )

    migrated = _read_json(state_dir / "access.json")
    assert migrated["allowFrom"] == ["284143065877184512"]
    assert migrated["dmPolicy"] == "allowlist"
    assert "999" in migrated["groups"]


def test_creates_default_when_no_target_and_no_shared(tmp_path):
    state_dir = tmp_path / "monster"

    merge_discord_channel_access.reconcile_agent_access(
        state_directory=str(state_dir),
        shared_access_file=str(tmp_path / "missing-shared.json"),
        channels_secret_file=None,
    )

    created = _read_json(state_dir / "access.json")
    assert created["dmPolicy"] == "pairing"
    assert created["allowFrom"] == []
    assert created["groups"] == {}


def test_adds_declared_channel_under_groups(tmp_path):
    state_dir = tmp_path / "monster"
    secret = tmp_path / "channels-secret"
    secret.write_text("123456789\n")

    merge_discord_channel_access.reconcile_agent_access(
        state_directory=str(state_dir),
        shared_access_file=str(tmp_path / "missing-shared.json"),
        channels_secret_file=str(secret),
    )

    document = _read_json(state_dir / "access.json")
    assert document["groups"]["123456789"] == {
        "requireMention": False,
        "allowFrom": [],
    }


def test_does_not_clobber_existing_channel_entry(tmp_path):
    state_dir = tmp_path / "monster"
    state_dir.mkdir()
    _write_json(
        state_dir / "access.json",
        {
            "dmPolicy": "pairing",
            "allowFrom": [],
            "groups": {"123456789": {"requireMention": True, "allowFrom": ["42"]}},
            "pending": {},
        },
    )
    secret = tmp_path / "channels-secret"
    secret.write_text("123456789")

    merge_discord_channel_access.reconcile_agent_access(
        state_directory=str(state_dir),
        shared_access_file=str(tmp_path / "missing-shared.json"),
        channels_secret_file=str(secret),
    )

    document = _read_json(state_dir / "access.json")
    assert document["groups"]["123456789"] == {
        "requireMention": True,
        "allowFrom": ["42"],
    }


def test_missing_channels_secret_adds_no_groups(tmp_path):
    state_dir = tmp_path / "monster"

    merge_discord_channel_access.reconcile_agent_access(
        state_directory=str(state_dir),
        shared_access_file=str(tmp_path / "missing-shared.json"),
        channels_secret_file=str(tmp_path / "missing-secret"),
    )

    document = _read_json(state_dir / "access.json")
    assert document["groups"] == {}


def test_empty_channels_secret_adds_no_groups(tmp_path):
    state_dir = tmp_path / "monster"
    secret = tmp_path / "channels-secret"
    secret.write_text("   \n")

    merge_discord_channel_access.reconcile_agent_access(
        state_directory=str(state_dir),
        shared_access_file=str(tmp_path / "missing-shared.json"),
        channels_secret_file=str(secret),
    )

    document = _read_json(state_dir / "access.json")
    assert document["groups"] == {}


def test_second_run_is_idempotent(tmp_path):
    state_dir = tmp_path / "monster"
    secret = tmp_path / "channels-secret"
    secret.write_text("123456789")

    def run_once():
        merge_discord_channel_access.reconcile_agent_access(
            state_directory=str(state_dir),
            shared_access_file=str(tmp_path / "missing-shared.json"),
            channels_secret_file=str(secret),
        )

    run_once()
    first = _read_json(state_dir / "access.json")
    run_once()
    second = _read_json(state_dir / "access.json")
    assert first == second


def test_merges_declared_channel_into_migrated_shared_groups(tmp_path):
    shared = tmp_path / "shared.json"
    state_dir = tmp_path / "monster"
    _write_json(
        shared,
        {
            "dmPolicy": "allowlist",
            "allowFrom": ["284143065877184512"],
            "groups": {"999": {"requireMention": False, "allowFrom": []}},
            "pending": {},
        },
    )
    secret = tmp_path / "channels-secret"
    secret.write_text("123456789")

    merge_discord_channel_access.reconcile_agent_access(
        state_directory=str(state_dir),
        shared_access_file=str(shared),
        channels_secret_file=str(secret),
    )

    document = _read_json(state_dir / "access.json")
    assert "999" in document["groups"]
    assert "123456789" in document["groups"]
    assert document["allowFrom"] == ["284143065877184512"]
