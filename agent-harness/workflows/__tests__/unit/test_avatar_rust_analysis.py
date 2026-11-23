import io
import json
import re
import sys
from pathlib import Path

import pytest

import analysis_report
import analysis_topics

WORKFLOWS_DIRECTORY = Path(__file__).resolve().parents[2]
ANALYSIS_DEFINITION = (
    WORKFLOWS_DIRECTORY / "definitions/avatar-rust-analysis/avatar-rust-analysis.yaml"
)
TOPIC_DEFINITION = (
    WORKFLOWS_DIRECTORY
    / "definitions/avatar-rust-analysis-topic/avatar-rust-analysis-topic.yaml"
)
TEMPLATE_TOPICS_DIRECTORY = ANALYSIS_DEFINITION.parent / "topics"
MAXIMUM_TOPIC_FAN_OUT = 5


@pytest.fixture
def standards_file(tmp_path):
    path = tmp_path / "standards.md"
    path.write_text("standards\n")
    return path


def run_script(monkeypatch, capsys, module, arguments):
    monkeypatch.setattr(sys, "argv", [module.__name__, *arguments])
    module.main()
    return json.loads(capsys.readouterr().out)


def run_report(monkeypatch, capsys, output_directory, stdin_text):
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_text))
    arguments = ["--output-directory", str(output_directory)]
    return run_script(monkeypatch, capsys, analysis_report, arguments)


def topic_arguments(avatar_root, standards_file, output_directory):
    return [
        "--avatar-root",
        str(avatar_root),
        "--standards-file",
        str(standards_file),
        "--output-directory",
        str(output_directory),
    ]


def substituted_template(template_path, avatar_root, standards_file):
    return (
        template_path.read_text()
        .replace("{AVATAR_ROOT}", str(avatar_root))
        .replace("{STANDARDS_FILE}", str(standards_file))
    )


def assert_topics_written(report, output_directory, avatar_root, standards_file):
    template_paths = sorted(TEMPLATE_TOPICS_DIRECTORY.glob("*.md"))
    written_paths = [
        output_directory.resolve() / "topics" / path.name for path in template_paths
    ]
    assert report == {"topics": [str(path) for path in written_paths], "error": ""}
    assert len(written_paths) == 5
    for template_path, written_path in zip(template_paths, written_paths, strict=True):
        expected = substituted_template(template_path, avatar_root, standards_file)
        assert written_path.read_text() == expected


SAMPLE_DECISION = {
    "decision": "Use cargo-dist",
    "reason": "covers all targets",
    "sources": ["a.md", "b.md"],
}


def sample_result(topic):
    return {
        "topic": topic,
        "decisions": [SAMPLE_DECISION],
        "rejected": ["plain matrix"],
        "unknowns": ["signing keys"],
    }


def test_topics_writes_five_substituted_files_and_returns_their_paths(
    tmp_path, monkeypatch, capsys, standards_file
):
    output_directory = tmp_path / "output"
    arguments = topic_arguments(tmp_path, standards_file, output_directory)
    report = run_script(monkeypatch, capsys, analysis_topics, arguments)
    assert_topics_written(report, output_directory, tmp_path, standards_file)


def test_topics_returns_error_object_for_missing_standards_file(
    tmp_path, monkeypatch, capsys
):
    output_directory = tmp_path / "output"
    arguments = topic_arguments(tmp_path, tmp_path / "absent.md", output_directory)
    report = run_script(monkeypatch, capsys, analysis_topics, arguments)
    assert report["topics"] == []
    assert "standards file is missing" in report["error"]
    assert not output_directory.exists()


def test_report_writes_both_outputs_from_a_list(tmp_path, monkeypatch, capsys):
    results = [sample_result("distribution"), sample_result("quality-gates")]
    report = run_report(monkeypatch, capsys, tmp_path, json.dumps(results))
    markdown = Path(report["research_markdown"]).read_text()
    assert report["reports"] == 2
    assert json.loads(Path(report["research_json"]).read_text()) == results
    assert markdown.startswith(
        "## distribution\n\n- Use cargo-dist (covers all targets) [a.md b.md]\n"
    )
    assert "Rejected:\n- plain matrix\n\nUnknown:\n- signing keys\n" in markdown


def test_report_reads_a_list_wrapped_under_any_key(tmp_path, monkeypatch, capsys):
    results = [sample_result("target-architecture")]
    report = run_report(
        monkeypatch, capsys, tmp_path, json.dumps({"research": results})
    )
    assert report["reports"] == 1
    assert json.loads(Path(report["research_json"]).read_text()) == results
    assert "## target-architecture\n" in Path(report["research_markdown"]).read_text()


def test_report_tolerates_invalid_json(tmp_path, monkeypatch, capsys):
    report = run_report(monkeypatch, capsys, tmp_path, "not json {")
    assert report == {"reports": 0, "research_json": "", "research_markdown": ""}


def split_nodes(definition_text):
    return re.split(r"^  - id:", definition_text, flags=re.MULTILINE)[1:]


def has_key(node_text, key):
    return re.search(rf"^    {key}:", node_text, flags=re.MULTILINE) is not None


def is_model_call(node_text):
    return has_key(node_text, "command") or has_key(node_text, "prompt")


def test_topic_definition_has_exactly_one_model_call():
    nodes = split_nodes(TOPIC_DEFINITION.read_text())
    assert sum(is_model_call(node) for node in nodes) == 1


def test_parent_fans_out_over_at_most_five_topics():
    widths = [
        int(width)
        for width in re.findall(r"max_parallel: (\d+)", ANALYSIS_DEFINITION.read_text())
    ]
    assert widths and max(widths) <= MAXIMUM_TOPIC_FAN_OUT


def test_report_counts_failed_topics_without_rendering_them(
    monkeypatch, capsys, tmp_path
):
    failed = {"archon_failed": True, "error": "boom", "status": "failed"}
    succeeded = {"topic": "alpha", "decisions": [], "rejected": [], "unknowns": []}
    report = run_report(monkeypatch, capsys, tmp_path, json.dumps([failed, succeeded]))
    assert (report["reports"], report["failed"]) == (1, 1)
    assert "## alpha" in (tmp_path / "research.md").read_text()
