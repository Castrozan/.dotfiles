import publish_current_usage_snapshot_to_ingest as publisher
from ccusage_daily_reader import CcusageCollectionError


def test_collection_failure_is_reported_without_a_traceback(monkeypatch, capsys):
    def refuse_collection():
        raise CcusageCollectionError("usage collection timed out")

    monkeypatch.setattr(publisher, "build_current_usage_snapshot", refuse_collection)
    assert publisher.main() == 1
    assert "usage collection timed out" in capsys.readouterr().err
