from datetime import UTC, datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

import gitlab_merge_request_assignee_sweep as sweep

MOMENT = datetime(2026, 11, 9, 18, 0, tzinfo=UTC)
AWARE_MOMENTS = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2035, 1, 1),
    timezones=st.just(UTC),
)


def merge_request(internal_id, author_id=7, assignee_ids=()):
    return sweep.MergeRequest(
        project_id=1,
        internal_id=internal_id,
        author_id=author_id,
        assignee_ids=tuple(assignee_ids),
        web_url=f"https://gitlab.example/mr/{internal_id}",
    )


class FakeGateway:
    def __init__(self, current_by_internal_id, failing_internal_ids=()):
        self.current_by_internal_id = current_by_internal_id
        self.failing_internal_ids = set(failing_internal_ids)
        self.assignments = []
        self.requested_lower_bounds = []

    def list_unassigned_authored_since(self, created_after):
        self.requested_lower_bounds.append(created_after)
        return [
            merge_request(internal_id) for internal_id in self.current_by_internal_id
        ]

    def read(self, listed):
        if listed.internal_id in self.failing_internal_ids:
            raise sweep.GitLabRequestFailed("boom")
        return self.current_by_internal_id[listed.internal_id]

    def assign(self, current, assignee_id):
        self.assignments.append((current.internal_id, assignee_id))


@given(
    st.dictionaries(
        st.integers(min_value=1, max_value=500),
        st.tuples(
            st.integers(min_value=1, max_value=50),
            st.lists(st.integers(min_value=51, max_value=99), max_size=3),
        ),
    )
)
def test_fills_only_merge_requests_still_empty_and_always_with_their_author(
    specification,
):
    current = {
        internal_id: merge_request(internal_id, author_id, assignees)
        for internal_id, (author_id, assignees) in specification.items()
    }
    gateway = FakeGateway(current)

    result = sweep.fill_missing_assignees(gateway, MOMENT)

    expected = {
        internal_id: author_id
        for internal_id, (author_id, assignees) in specification.items()
        if not assignees
    }
    assert dict(gateway.assignments) == expected
    assert len(gateway.assignments) == len(expected)
    assert result.failures == ()


@given(AWARE_MOMENTS, AWARE_MOMENTS)
def test_lower_bound_never_precedes_first_sweep_nor_the_recent_window(first, now):
    bound = sweep.sweep_lower_bound(first, now)

    assert bound >= first
    assert bound >= now - sweep.RECENT_MERGE_REQUEST_WINDOW
    assert bound in (first, now - sweep.RECENT_MERGE_REQUEST_WINDOW)


def test_first_sweep_records_the_floor_and_later_sweeps_keep_it(tmp_path):
    marker = tmp_path / "state" / "gitlab.example.first-sweep-at"

    assert sweep.read_or_record_first_sweep_time(marker, MOMENT) == MOMENT
    later = MOMENT + timedelta(hours=3)
    assert sweep.read_or_record_first_sweep_time(marker, later) == MOMENT


def test_unreadable_marker_restarts_the_floor_at_now(tmp_path):
    marker = tmp_path / "gitlab.example.first-sweep-at"
    marker.write_text("")

    assert sweep.read_or_record_first_sweep_time(marker, MOMENT) == MOMENT
    assert marker.read_text() == MOMENT.isoformat()


def test_merge_request_created_before_the_first_sweep_is_outside_the_query(tmp_path):
    gateway = FakeGateway({})

    sweep.sweep_host("gitlab.example", gateway, tmp_path, MOMENT)

    assert gateway.requested_lower_bounds == [MOMENT]


def test_one_failing_merge_request_does_not_stop_the_others():
    gateway = FakeGateway(
        {1: merge_request(1), 2: merge_request(2), 3: merge_request(3)},
        failing_internal_ids=[2],
    )

    result = sweep.fill_missing_assignees(gateway, MOMENT)

    assert gateway.assignments == [(1, 7), (3, 7)]
    assert [item.internal_id for item in result.assigned] == [1, 3]
    assert len(result.failures) == 1
    assert "https://gitlab.example/mr/2" in result.failures[0]


def test_main_sweeps_every_host_reports_failures_and_exits_nonzero(
    monkeypatch, tmp_path, capsys
):
    def gateway_for(host):
        if host == "down.example":
            gateway = FakeGateway({})
            gateway.list_unassigned_authored_since = _raise_request_failed
            return gateway
        return FakeGateway({5: merge_request(5)})

    monkeypatch.setattr(sweep, "GlabMergeRequestGateway", gateway_for)

    exit_code = sweep.main(
        [
            "--host",
            "down.example",
            "--host",
            "up.example",
            "--state-directory",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "assigned https://gitlab.example/mr/5" in captured.out
    assert "down.example" in captured.err


def test_main_is_silent_and_succeeds_when_nothing_needs_filling(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(sweep, "GlabMergeRequestGateway", lambda _: FakeGateway({}))

    exit_code = sweep.main(["--host", "up.example", "--state-directory", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def _raise_request_failed(_created_after):
    raise sweep.GitLabRequestFailed("offline")
