import copy

from hypothesis import given
from hypothesis import strategies as st

from reconcile_declared_marketplace_sources import rewrite_differing_sources

marketplace_names = st.sampled_from(
    ["betha-agent-marketplace", "dotagents", "avatar", "other"]
)
git_sources = st.builds(
    lambda url: {"source": "git", "url": url, "ref": "marketplace"},
    st.sampled_from(["https://old.example/repo.git", "https://new.example/repo.git"]),
)
marketplace_records = st.dictionaries(
    marketplace_names,
    st.builds(
        lambda source: {"source": source, "installLocation": "/somewhere"}, git_sources
    ),
)
declared_sources = st.dictionaries(marketplace_names, git_sources)


@given(marketplace_records, declared_sources)
def test_declared_records_end_with_the_declared_source_and_nothing_else_changes(
    records, declared
):
    original_records = copy.deepcopy(records)
    rewritten_names = rewrite_differing_sources(records, declared)
    assert set(records) == set(original_records)
    for marketplace_name, record in records.items():
        original_record = original_records[marketplace_name]
        if marketplace_name in declared:
            assert record["source"] == declared[marketplace_name]
        else:
            assert record == original_record
        assert record["installLocation"] == original_record["installLocation"]
        assert (marketplace_name in rewritten_names) == (record != original_record)

