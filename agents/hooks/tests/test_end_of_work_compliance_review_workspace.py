import pytest

import end_of_work_compliance_review as hook


@pytest.fixture(autouse=True)
def _apply_compliance_review_test_isolation(
    reset_session_id_prefix_between_tests, isolate_persistent_log_file
):
    return isolate_persistent_log_file


class TestLoadWorkspacePolicyDocs:
    def test_loads_known_doc_filenames(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("claude rules")
        (tmp_path / "AGENTS.md").write_text("agent rules")
        (tmp_path / "RANDOM.md").write_text("ignored")

        docs = hook.load_workspace_policy_docs(str(tmp_path))

        assert "CLAUDE.md" in docs
        assert "AGENTS.md" in docs
        assert "RANDOM.md" not in docs
        assert docs["CLAUDE.md"] == "claude rules"

    def test_truncates_large_docs(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("x" * 10000)
        docs = hook.load_workspace_policy_docs(str(tmp_path))
        assert len(docs["CLAUDE.md"]) == hook.MAX_WORKSPACE_DOC_CHARS

    def test_returns_empty_when_cwd_blank(self):
        assert hook.load_workspace_policy_docs("") == {}
