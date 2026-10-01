"""API-level regression checks: repeat-safe bootstrap and scoped integrations."""

from pathlib import Path
from unittest.mock import Mock, patch
import unittest
import tempfile

import audiobookshelf
import indexers
import provision
import readmeabook


class ProvisionTests(unittest.TestCase):
    def test_main_keeps_all_three_passwords_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = {
                "AUDIOBOOK_USERNAME": "lucas",
                "QBITTORRENT_USERNAME": "download-admin",
                "PROWLARR_CONFIG_FILE": str(root / "config.xml"),
                "PROWLARR_BASE_URL": "http://prowlarr",
                "AUDIOBOOKSHELF_BASE_URL": "http://abs",
                "READMEABOOK_BASE_URL": "http://rmab",
                "STATE_DIRECTORY": directory,
            }
            (root / "config.xml").write_text("<Config><ApiKey>key</ApiKey></Config>")
            for name, value in [
                ("AUDIOBOOK_PASSWORD_FILE", "abs-secret"),
                ("READMEABOOK_PASSWORD_FILE", "rmab-secret"),
                ("QBITTORRENT_PASSWORD_FILE", "download-secret"),
            ]:
                path = root / name
                path.write_text(value)
                env[name] = str(path)
            with (
                patch.dict(provision.os.environ, env),
                patch.object(provision, "Client"),
                patch.object(provision, "select_indexers", return_value=[]),
                patch.object(
                    provision, "provision_abs", return_value=("library", "token")
                ) as abs_call,
                patch.object(provision, "provision_rmab") as rmab_call,
            ):
                provision.main()
            self.assertEqual(abs_call.call_args.args[1]["password"], "abs-secret")
            self.assertEqual(rmab_call.call_args.args[1]["password"], "rmab-secret")
            self.assertEqual(rmab_call.call_args.args[-1], "download-secret")

    def test_indexers_exclude_disabled_non_audio_and_unsupported_protocol(self):
        valid = {
            "id": 1,
            "name": "audio",
            "enable": True,
            "protocol": "torrent",
            "capabilities": {
                "categories": [{"id": 3000, "subCategories": [{"id": 3030}]}]
            },
        }
        candidates = [
            valid,
            {**valid, "enable": False},
            {**valid, "protocol": "usenet"},
            {**valid, "capabilities": {"categories": [{"id": 7020}]}},
        ]
        selected = indexers.select_indexers(candidates)
        self.assertEqual([item["id"] for item in selected], [1])
        self.assertTrue(indexers.has_audiobooks([{"id": 3030}]))
        self.assertFalse(selected[0]["rssEnabled"])
        self.assertEqual(selected[0]["ebookCategories"], [])
        with self.assertRaises(RuntimeError):
            indexers.select_indexers([])

    def test_abs_existing_library_and_valid_key_are_reused(self):
        client = Mock(base="http://abs")
        client.ready.return_value = {"isInit": True}
        client.call.side_effect = [
            {"user": {"id": "owner", "accessToken": "login"}},
            {
                "libraries": [
                    {"id": "library", "folders": [{"fullPath": "/data/audiobooks"}]}
                ]
            },
        ]
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(audiobookshelf, "Client") as key_client,
        ):
            token = Path(directory) / "key"
            token.write_text("persisted-token")
            result = audiobookshelf.provision_abs(
                client, {"username": "owner", "password": "secret"}, token
            )
            self.assertEqual(result, ("library", "persisted-token"))
            self.assertEqual(client.call.call_count, 2)
            key_client.return_value.call.assert_called_once_with("/api/libraries")

    def test_abs_bootstrap_persists_key_privately(self):
        client = Mock()
        client.ready.return_value = {"isInit": False}
        client.call.side_effect = [
            {},
            {"user": {"id": "owner", "accessToken": "login"}},
            {"libraries": []},
            {"id": "library"},
            {"apiKey": {"apiKey": "durable"}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            token = Path(directory) / "key"
            self.assertEqual(
                audiobookshelf.provision_abs(
                    client, {"username": "owner", "password": "secret"}, token
                ),
                ("library", "durable"),
            )
            self.assertEqual(token.stat().st_mode & 0o777, 0o600)
            self.assertEqual(token.read_text(), "durable")
        key_request = client.call.call_args_list[-1].args
        self.assertTrue(key_request[1]["isActive"])
        self.assertNotIn("expiresIn", key_request[1])

    def test_completed_rmab_never_recreates_setup_or_download_client(self):
        client = Mock()
        client.ready.return_value = {"setupComplete": True}

        def call(path, body=None, method=None):
            if path == "/api/auth/local/login":
                return {"accessToken": "login"}
            if path == "/api/admin/settings/download-clients":
                return {
                    "clients": [{"id": "existing", "name": "qBittorrent (Nix managed)"}]
                }
            if path == "/api/bookdate/config":
                return {"config": None}
            return {}

        client.call.side_effect = call
        readmeabook.provision_rmab(
            client,
            {"username": "owner", "password": "secret"},
            "library",
            "token",
            "key",
            [],
            "download-admin",
            "download-secret",
        )
        calls = client.call.call_args_list
        self.assertFalse(any(item.args[0] == "/api/setup/complete" for item in calls))
        updates = [
            item for item in calls if item.args[0].endswith("download-clients/existing")
        ]
        self.assertEqual(updates[0].args[2], "PUT")
        self.assertEqual(updates[0].args[1]["username"], "download-admin")
        self.assertEqual(updates[0].args[1]["password"], "download-secret")
        login = next(item for item in calls if item.args[0].endswith("/login"))
        self.assertEqual(login.args[1]["username"], "owner")
        self.assertEqual(login.args[1]["password"], "secret")
        ebook = next(item.args[1] for item in calls if item.args[0].endswith("/ebook"))
        self.assertFalse(any(ebook.values()))
        registration = next(
            item.args[1] for item in calls if item.args[0].endswith("/registration")
        )
        self.assertFalse(registration["enabled"])


if __name__ == "__main__":
    unittest.main()
