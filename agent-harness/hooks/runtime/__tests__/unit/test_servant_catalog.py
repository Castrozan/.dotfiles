import pytest

import servant_catalog


class TestServantRoster:
    def test_every_entry_carries_a_name_and_a_personality(self):
        for entry in servant_catalog.SERVANT_CATALOG:
            assert entry["name"].strip()
            assert entry["personality"].strip()

    def test_an_entry_carries_nothing_else(self):
        for entry in servant_catalog.SERVANT_CATALOG:
            assert set(entry) == {"name", "personality"}

    def test_names_are_unique(self):
        names = [entry["name"] for entry in servant_catalog.SERVANT_CATALOG]
        assert len(names) == len(set(names))

    def test_the_roster_is_large_enough_that_collisions_are_uncommon(self):
        assert len(servant_catalog.SERVANT_CATALOG) > 90


class TestRosterParsing:
    def test_a_line_splits_on_the_first_pipe(self):
        parsed = servant_catalog._servants_from_roster("Iskandar | Boisterous king.")
        assert parsed == [{"name": "Iskandar", "personality": "Boisterous king."}]

    def test_blank_lines_are_ignored_so_entries_can_be_grouped(self):
        parsed = servant_catalog._servants_from_roster("\nA | one.\n\n\nB | two.\n")
        assert [entry["name"] for entry in parsed] == ["A", "B"]

    def test_a_duplicate_name_would_fail_the_catalog_assertion(self):
        parsed = servant_catalog._servants_from_roster("A | one.\nA | two.")
        assert len({entry["name"] for entry in parsed}) < len(parsed)


def _roster_of(size, prefix="Servant"):
    return [{"name": f"{prefix} {n}", "personality": "x."} for n in range(size)]


def _assignments(session_ids, roster):
    return [
        servant_catalog.select_servant_for_session(session_id, roster)["name"]
        for session_id in session_ids
    ]


class TestServantSelection:
    def test_selection_is_deterministic_per_session_id(self):
        for session_id in ("a", "b", "same-session"):
            first = servant_catalog.select_servant_for_session(session_id)
            second = servant_catalog.select_servant_for_session(session_id)
            assert first == second

    def test_different_session_ids_do_not_all_land_on_one_servant(self):
        selections = {
            servant_catalog.select_servant_for_session(f"session-{n}")["name"]
            for n in range(50)
        }
        assert len(selections) > 1

    def test_every_servant_is_reachable(self):
        drawn = {
            servant_catalog.select_servant_for_session(f"session-{n}")["name"]
            for n in range(20000)
        }
        assert len(drawn) == len(servant_catalog.SERVANT_CATALOG)


class TestSelectionSurvivesRosterEdits:
    """The reason selection is scored per name instead of indexed by position.

    `hash % len(catalog)` tied every session to the roster's size, so adding one
    name re-drew every session on the fleet and reordering the file did the same.
    """

    def test_reordering_the_roster_moves_nobody(self):
        session_ids = [f"session-{n}" for n in range(500)]
        roster = _roster_of(100)
        assert _assignments(session_ids, roster) == _assignments(
            session_ids, list(reversed(roster))
        )

    def test_adding_one_servant_moves_almost_nobody(self):
        session_ids = [f"session-{n}" for n in range(2000)]
        roster = _roster_of(100)
        grown = roster + [{"name": "One More", "personality": "x."}]
        moved = sum(
            before != after
            for before, after in zip(
                _assignments(session_ids, roster), _assignments(session_ids, grown)
            )
        )
        assert moved < len(session_ids) * 0.05

    def test_a_session_only_moves_when_the_new_servant_wins_it(self):
        session_ids = [f"session-{n}" for n in range(2000)]
        roster = _roster_of(100)
        grown = roster + [{"name": "One More", "personality": "x."}]
        after = _assignments(session_ids, grown)
        for before, now in zip(_assignments(session_ids, roster), after):
            assert now in (before, "One More")


class TestServantTemporaryDirectory:
    def test_the_ambient_tmpdir_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TMPDIR", str(tmp_path))
        assert servant_catalog.servant_temporary_directory() == tmp_path

    def test_without_a_tmpdir_it_falls_back_to_tmp(self, monkeypatch):
        monkeypatch.delenv("TMPDIR", raising=False)
        assert str(servant_catalog.servant_temporary_directory()) == "/tmp"


@pytest.mark.parametrize("banned_key", ["class", "catchphrase", "manner"])
def test_the_removed_fields_are_gone(banned_key):
    assert banned_key not in servant_catalog.SERVANT_CATALOG[0]
