import json
import os
import uuid
from pathlib import Path

import servant_catalog
import servant_session_id


class TestResumeShapeDetection:
    def test_continue_and_resume_flags_are_resume_shaped(self):
        for flag in ("-c", "--continue", "-r", "--resume"):
            assert servant_session_id.is_resume_shaped_launch([flag])

    def test_a_fresh_launch_is_not_resume_shaped(self):
        assert not servant_session_id.is_resume_shaped_launch([])
        assert not servant_session_id.is_resume_shaped_launch(["-n", "my-session"])


class TestExplicitResumeSessionId:
    def test_an_id_shaped_value_after_resume_is_read_as_the_target(self):
        session_id = "2295054f-355a-4182-9d8d-140f9714e062"
        assert (
            servant_session_id.explicit_resume_session_id(["--resume", session_id])
            == session_id
        )
        assert (
            servant_session_id.explicit_resume_session_id(["-r", session_id])
            == session_id
        )

    def test_a_bare_resume_with_no_value_yields_no_id(self):
        assert servant_session_id.explicit_resume_session_id(["--resume"]) is None

    def test_continue_never_carries_an_explicit_id(self):
        assert servant_session_id.explicit_resume_session_id(["-c"]) is None

    def test_a_search_term_that_is_not_id_shaped_yields_no_id(self):
        assert (
            servant_session_id.explicit_resume_session_id(["--resume", "fix the bug"])
            is None
        )

    def test_a_following_flag_is_not_mistaken_for_the_id(self):
        assert (
            servant_session_id.explicit_resume_session_id(["--resume", "--verbose"])
            is None
        )


class TestTranscriptCwdMatch:
    def _write_transcript(
        self, projects_root, project_dir_name, session_id, cwd, mtime
    ):
        transcript_dir = projects_root / project_dir_name
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = transcript_dir / f"{session_id}.jsonl"
        lines = [
            {"type": "session-created", "sessionId": session_id},
            {"type": "user", "sessionId": session_id, "cwd": cwd, "uuid": "u1"},
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
        resolved = servant_session_id.most_recent_transcript_session_id_for_cwd(
            Path(target_cwd), projects_root=projects_root
        )
        assert resolved == "newer-session"

    def test_a_transcript_for_a_different_cwd_is_not_matched(self, tmp_path):
        projects_root = tmp_path / "projects"
        self._write_transcript(
            projects_root, "other-repo", "unrelated", "/Users/x/other", mtime=9999
        )
        resolved = servant_session_id.most_recent_transcript_session_id_for_cwd(
            Path("/Users/lucas.zanoni/work/repo"), projects_root=projects_root
        )
        assert resolved is None

    def test_no_projects_directory_yields_no_match(self, tmp_path):
        resolved = servant_session_id.most_recent_transcript_session_id_for_cwd(
            Path("/Users/lucas.zanoni/work/repo"),
            projects_root=tmp_path / "does-not-exist",
        )
        assert resolved is None


class TestResolveSessionId:
    def test_a_fresh_launch_mints_a_uuid_the_wrapper_must_pass_on(self, tmp_path):
        session_id, minted_here = servant_session_id.resolve_session_id(
            [], Path("/x"), projects_root=tmp_path
        )
        assert minted_here
        assert uuid.UUID(session_id)

    def test_a_session_id_the_human_passed_is_adopted_not_replaced(self, tmp_path):
        supplied = "2295054f-355a-4182-9d8d-140f9714e062"
        assert servant_session_id.resolve_session_id(
            ["--session-id", supplied], Path("/x"), projects_root=tmp_path
        ) == (supplied, False)

    def test_resuming_an_explicit_id_never_mints(self, tmp_path):
        resumed = "2295054f-355a-4182-9d8d-140f9714e062"
        assert servant_session_id.resolve_session_id(
            ["--resume", resumed], Path("/x"), projects_root=tmp_path
        ) == (resumed, False)

    def test_the_bug_a_resumed_session_resolves_to_the_servant_it_launched_with(
        self, tmp_path
    ):
        """Reproduces the live regression: -c drew a fresh random Servant on every
        relaunch, because the wrapper picked before any session id existed. Minting
        the id at launch makes the Servant a pure function of it, so the resume
        lands on the same one with nothing persisted in between."""
        launched_id, minted_here = servant_session_id.resolve_session_id(
            [], Path("/x"), projects_root=tmp_path
        )
        assert minted_here
        resumed_id, _ = servant_session_id.resolve_session_id(
            ["--resume", launched_id], Path("/x"), projects_root=tmp_path
        )
        assert servant_catalog.select_servant_for_session(
            resumed_id
        ) == servant_catalog.select_servant_for_session(launched_id)

    def test_a_continue_with_nothing_to_match_yields_no_id_and_no_mint(self, tmp_path):
        assert servant_session_id.resolve_session_id(
            ["-c"], Path("/x"), projects_root=tmp_path / "empty"
        ) == (None, False)
