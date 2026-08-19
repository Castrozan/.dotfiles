import json
import os
from pathlib import Path

import servant_catalog
import summon_servant


class TestTranscriptCwdMatch:
    def _write_transcript(
        self, projects_root, project_dir_name, session_id, cwd, mtime
    ):
        transcript_dir = projects_root / project_dir_name
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = transcript_dir / f"{session_id}.jsonl"
        lines = [
            {"type": "session-created", "sessionId": session_id},
            {
                "type": "user",
                "sessionId": session_id,
                "cwd": cwd,
                "uuid": "u1",
            },
        ]
        transcript_path.write_text(
            "\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8"
        )
        os.utime(transcript_path, (mtime, mtime))
        return transcript_path

    def test_the_newest_transcript_matching_the_cwd_wins(self, tmp_path):
        projects_root = tmp_path / "projects"
        target_cwd = "/Users/lucas.zanoni/work/repo"
        self._write_transcript(
            projects_root, "repo", "older-session", target_cwd, mtime=1000
        )
        self._write_transcript(
            projects_root, "repo", "newer-session", target_cwd, mtime=2000
        )
        resolved = summon_servant.most_recent_transcript_session_id_for_cwd(
            Path(target_cwd), projects_root=projects_root
        )
        assert resolved == "newer-session"

    def test_a_transcript_for_a_different_cwd_is_not_matched(self, tmp_path):
        projects_root = tmp_path / "projects"
        self._write_transcript(
            projects_root,
            "other-repo",
            "unrelated-session",
            "/Users/x/other",
            mtime=9999,
        )
        resolved = summon_servant.most_recent_transcript_session_id_for_cwd(
            Path("/Users/lucas.zanoni/work/repo"), projects_root=projects_root
        )
        assert resolved is None

    def test_no_projects_directory_yields_no_match(self, tmp_path):
        resolved = summon_servant.most_recent_transcript_session_id_for_cwd(
            Path("/Users/lucas.zanoni/work/repo"),
            projects_root=tmp_path / "does-not-exist",
        )
        assert resolved is None


class TestResolveServantForLaunch:
    def test_a_fresh_launch_resolves_to_nothing_so_the_caller_draws_random(
        self, tmp_path
    ):
        assert (
            summon_servant.resolve_servant_for_launch(
                [], Path("/x"), projects_root=tmp_path
            )
            is None
        )

    def test_resuming_a_session_with_a_stored_identity_keeps_it(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("SERVANT_IDENTITY_STATE_DIRECTORY", str(tmp_path))
        session_id = "2295054f-355a-4182-9d8d-140f9714e062"
        stored = servant_catalog.SERVANT_CATALOG[0]
        servant_catalog.write_servant_identity(session_id, stored)

        resolved = summon_servant.resolve_servant_for_launch(
            ["--resume", session_id], Path("/x"), projects_root=tmp_path
        )
        assert resolved == stored

    def test_resuming_a_session_with_no_stored_identity_is_still_deterministic(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("SERVANT_IDENTITY_STATE_DIRECTORY", str(tmp_path))
        session_id = "3fa1f900-0000-4000-8000-000000000000"

        first = summon_servant.resolve_servant_for_launch(
            ["--resume", session_id], Path("/x"), projects_root=tmp_path
        )
        second = summon_servant.resolve_servant_for_launch(
            ["--resume", session_id], Path("/x"), projects_root=tmp_path
        )
        assert first == second == servant_catalog.select_servant_for_session(session_id)

    def test_the_bug_a_resumed_session_no_longer_redraws_once_recorded(
        self, tmp_path, monkeypatch
    ):
        """Reproduces the live regression: -c drew a fresh random Servant on every
        relaunch of the same conversation, because the wrapper never looked at
        resume intent at all. Once the hook records what a launch resolved to,
        the next resume of that same session must resolve to the same Servant."""
        monkeypatch.setenv("SERVANT_IDENTITY_STATE_DIRECTORY", str(tmp_path))
        session_id = "2295054f-355a-4182-9d8d-140f9714e062"

        first_launch = summon_servant.resolve_servant_for_launch(
            ["-c"], Path("/x"), projects_root=tmp_path / "empty-projects"
        )
        assert first_launch is None  # -c with nothing to match: caller draws random
        drawn_servant = servant_catalog.SERVANT_CATALOG[3]
        servant_catalog.write_servant_identity(session_id, drawn_servant)

        resumed = summon_servant.resolve_servant_for_launch(
            ["--resume", session_id], Path("/x"), projects_root=tmp_path
        )
        assert resumed == drawn_servant
