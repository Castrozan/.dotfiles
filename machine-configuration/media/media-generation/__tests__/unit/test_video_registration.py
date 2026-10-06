import os
import unittest
from dataclasses import replace

from video_fixture import FixtureRecipe, digest, write_json
from media_video.contract import VideoError, validate_operation_id
from media_video.deadline import ExecutionDeadline
from media_video.registration import load_recipe_registration


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FixtureRecipe()
        self.addCleanup(self.fixture.cleanup)

    def load(self):
        return load_recipe_registration(
            self.fixture.registration, ExecutionDeadline(10)
        )

    def update_manifest(self, document):
        write_json(self.fixture.manifest, document)
        import json

        registration = json.loads(self.fixture.registration.read_bytes())
        registration["source_assets_manifest"]["sha256"] = digest(self.fixture.manifest)
        write_json(self.fixture.registration, registration)

    def test_registration_is_private_and_native_binary_is_pinned(self):
        registered = self.load()
        self.assertEqual(registered.binary.sha256, digest(self.fixture.binary))
        self.assertEqual(len(registered.files), 2)
        for path in (self.fixture.registration, self.fixture.manifest):
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_public_registration_manifest_and_recipe_directory_are_refused(self):
        for path, private_mode in (
            (self.fixture.registration, 0o600),
            (self.fixture.manifest, 0o600),
            (self.fixture.recipe, 0o700),
        ):
            os.chmod(path, 0o755)
            with self.assertRaises(VideoError):
                self.load()
            os.chmod(path, private_mode)

    def test_changed_binary_and_manifest_bytes_are_refused(self):
        for path in (self.fixture.binary, self.fixture.manifest):
            original = path.read_bytes()
            path.write_bytes(b"modified")
            with self.assertRaisesRegex(VideoError, "registered_input_changed"):
                self.load()
            path.write_bytes(original)

    def test_traversal_absolute_and_duplicate_manifest_paths_are_refused(self):
        for path in (
            "../narration.wav",
            str(self.fixture.asset),
            "a/../narration.wav",
            ".",
        ):
            self.update_manifest(
                {"files": [{"path": path, "sha256": digest(self.fixture.asset)}]}
            )
            with self.assertRaisesRegex(VideoError, "invalid_manifest_path"):
                self.load()
        self.update_manifest(
            {
                "files": [
                    {
                        "path": self.fixture.asset.name,
                        "sha256": digest(self.fixture.asset),
                    },
                    {
                        "path": self.fixture.asset.name,
                        "sha256": digest(self.fixture.asset),
                    },
                ]
            }
        )
        with self.assertRaisesRegex(VideoError, "invalid_manifest_path"):
            self.load()

    def test_asset_symlink_is_refused(self):
        target = self.fixture.recipe / "linked.wav"
        target.symlink_to(self.fixture.asset)
        self.update_manifest(
            {"files": [{"path": target.name, "sha256": digest(self.fixture.asset)}]}
        )
        with self.assertRaisesRegex(VideoError, "unsafe_input_path"):
            self.load()

    def test_script_cannot_register_as_compiled_binary(self):
        self.fixture.binary.write_bytes(b"#!/bin/sh\nexit 0\n")
        self.fixture.refresh()
        with self.assertRaisesRegex(VideoError, "native_binary_required"):
            self.load()

    def test_non_executable_binary_is_refused(self):
        os.chmod(self.fixture.binary, 0o600)
        with self.assertRaisesRegex(VideoError, "binary_not_executable"):
            self.load()

    def test_duplicate_json_keys_are_refused(self):
        self.fixture.registration.write_bytes(
            b'{"recipe_id":"first","recipe_id":"second"}'
        )
        with self.assertRaisesRegex(VideoError, "invalid_json"):
            self.load()

    def test_unsupported_output_and_unbounded_deadlines_are_refused(self):
        for changes in (
            {"width": 1920},
            {"height": 1080},
            {"fps": 24},
            {"frames": 1440},
            {"deadline_seconds": 601},
            {"deadline_seconds": 0},
            {"deadline_seconds": float("inf")},
            {"deadline_seconds": float("nan")},
            {"deadline_seconds": True},
            {"width": 1080.0},
        ):
            with self.assertRaises(VideoError):
                replace(self.fixture.request, **changes)

    def test_operation_uuid_cannot_escape_state(self):
        for operation_id in ("../escape", "not-a-uuid", None, "A" * 36):
            with self.assertRaisesRegex(VideoError, "invalid_operation_id"):
                validate_operation_id(operation_id)

    def test_embedded_nul_in_registration_paths_is_refused(self):
        with self.assertRaisesRegex(VideoError, "invalid_registration_path"):
            replace(self.fixture.request, recipe_registration="/private/\x00file")
        self.update_manifest(
            {"files": [{"path": "\x00asset", "sha256": digest(self.fixture.asset)}]}
        )
        with self.assertRaisesRegex(VideoError, "invalid_manifest"):
            self.load()
