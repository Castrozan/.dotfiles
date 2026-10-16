from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile

import pytest

import download_artifacts as DOWNLOAD
import prepare_reports as REPORTS
import workflow_context as CONTEXT


@pytest.fixture
def coverage_producer(run, artifact, jobs, monkeypatch):
    archive = BytesIO()
    with ZipFile(archive, "w") as bundle:
        bundle.writestr("bats/coverage.json", '{"covered_lines": "1"}')
        bundle.writestr("bats/index.html", "measured coverage")
    content = archive.getvalue()
    artifact.update(
        name="coverage-report", digest="sha256:" + sha256(content).hexdigest()
    )
    jobs[0]["name"] = "bash-coverage / Coverage (PR)"
    jobs[0]["steps"][0]["name"] = "Upload coverage report"
    route = f"repos/{CONTEXT.REPOSITORY}/actions/runs/{run['id']}"
    documents = {
        f"{route}/attempts/2": run,
        f"{route}/attempts/2/jobs?per_page=100": {"total_count": 1, "jobs": jobs},
        f"{route}/artifacts?per_page=100": {"total_count": 1, "artifacts": [artifact]},
    }
    monkeypatch.setattr(CONTEXT, "github_document", documents.__getitem__)
    downloads = []

    def download(command, **arguments):
        downloads.append(command)
        arguments["stdout"].write(content)

    monkeypatch.setattr(DOWNLOAD.subprocess, "run", download)
    return documents, downloads


def prepare_from_event(run, tmp_path):
    context = CONTEXT.collect_context({"workflow_run": run})
    downloads = tmp_path / "downloads"
    DOWNLOAD.download_selected(context, downloads)
    REPORTS.prepare_reports(context, downloads, tmp_path / "site")
    return context


def test_report_reuses_the_exact_verified_coverage_artifact(
    run, coverage_producer, tmp_path
):
    context = prepare_from_event(run, tmp_path)
    selection = context["artifacts"]["coverage-report"]
    assert selection["id"] == 456
    assert selection["producer"]["runAttempt"] == 2
    assert (
        tmp_path / "site/coverage/bats/index.html"
    ).read_text() == "measured coverage"
    assert coverage_producer[1][0][-1].endswith("/actions/artifacts/456/zip")
    assert len(coverage_producer[1]) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"repository": {"full_name": "foreign/repository"}},
        {"head_repository": {"full_name": "foreign/repository"}},
        {"event": "pull_request"},
    ],
)
def test_untrusted_producer_is_rejected_before_any_report_copy(
    run, coverage_producer, tmp_path, changes
):
    run.update(changes)
    with pytest.raises(ValueError):
        prepare_from_event(run, tmp_path)
    assert not coverage_producer[1]
    assert not (tmp_path / "site").exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"created_at": "2026-09-26T00:02:00Z"},
        {"workflow_run": {"id": 999, "head_sha": "a" * 40}},
        {"digest": "sha256:" + "0" * 64},
        {"expired": True},
    ],
)
def test_wrong_attempt_foreign_run_corrupt_or_expired_artifact_cannot_publish(
    run, artifact, coverage_producer, tmp_path, changes
):
    artifact.update(changes)
    with pytest.raises(ValueError, match="verified coverage artifact"):
        prepare_from_event(run, tmp_path)
    assert not (tmp_path / "site").exists()


def test_missing_coverage_artifact_cannot_publish(run, coverage_producer, tmp_path):
    for route in coverage_producer[0]:
        if route.endswith("/artifacts?per_page=100"):
            coverage_producer[0][route] = {"total_count": 0, "artifacts": []}
    with pytest.raises(ValueError, match="verified coverage artifact"):
        prepare_from_event(run, tmp_path)
    assert not coverage_producer[1]
    assert not (tmp_path / "site").exists()


def test_successful_upload_from_another_job_cannot_publish(
    run, jobs, coverage_producer, tmp_path
):
    jobs[0]["name"] = "foreign producer"
    with pytest.raises(ValueError, match="verified coverage artifact"):
        prepare_from_event(run, tmp_path)
    assert not coverage_producer[1]
    assert not (tmp_path / "site").exists()


def test_missing_coverage_document_cannot_publish(run, coverage_producer, tmp_path):
    context = CONTEXT.collect_context({"workflow_run": run})
    downloads = tmp_path / "downloads"
    DOWNLOAD.download_selected(context, downloads)
    (downloads / "coverage-report/bats/coverage.json").unlink()
    with pytest.raises(ValueError, match="coverage document"):
        REPORTS.prepare_reports(context, downloads, tmp_path / "site")
    assert not (tmp_path / "site").exists()
